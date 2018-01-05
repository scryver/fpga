#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import block, Signal, intbv, always, always_comb, concat, toVHDL
from fpga.utils import create_signals
from .ram import ShiftRegister


@block
def Multiplier35Bit(clk, rst, a, b, p):

    """
    Some text here (added buffers to input + one at the output => total delay = 5 clock cycles)
                 ______           ____                             ____            _________
      a[35:17]__|A    P|__mult1__|D  Q|__bufm1[36:]_______________|D  Q|__bufm11__|x[70:34] \\
      b[35:17]__|B     |         |>   |                           |>   |          |          \\
                |______|         |____|                           |____|          |           \\
                 ______           ____                             ____           |            \\
      a[17:]____|A    P|__mult2__|D  Q|__bufm2[36:]_______________|D  Q|__bufm22__|x[34:]       \\
      b[17:]____|B     |         |>   |                           |>   |           \\             |
                |______|         |____|                           |____|            \\            |          ____
                 ______           ____           ____                               |            |__adder__|D  Q|__p[70:]
      a[35:17]__|A    P|__mult3__|D  Q|__bufm3__|    \\                              /            |         |>   |
      b[17:]____|B     |         |>   |         |     \\            ____            /             |         |____|
                |______|         |____|         \\      |__addLow__|D  Q|__bufm34__|y[53:17]     /
                 ______           ____          /      |          |>   |          |            /
      a[17:]____|A    P|__mult4__|D  Q|__bufm4__|     /           |____|          |           /
      b[35:17]__|B     |         |>   |         |____/                            |          /
                |______|         |____|                                           |_________/

    :param a:
    :param b:
    :param p:
    :param clk:
    :param rst:
    :return:
    """
    A_MAX = len(a)
    assert(A_MAX == 35)
    MULTMAX = 18
    MULT_MAX_VAL = 2 ** MULTMAX // 2

    M = 35 + 1
    MOUT = 2 * M
    MAX_IN = 2 ** M // 2
    MAX_LOW = 2 ** (M - 2)
    MAX_OUT = 2 ** (MOUT - 2) // 2

    a_upper, b_upper, a_lower, b_lower, au_buf, bu_buf, al_buf, bl_buf = [Signal(intbv(0, min=-MULT_MAX_VAL, max=MULT_MAX_VAL)) for _ in range(8)]

    mult1, mult3, mult4, bufm1, bufm11, bufm3, bufm4, bufm34 = [Signal(intbv(0, min=-MAX_IN, max=MAX_IN)) for _ in range(8)]
    addLow = Signal(intbv(0, min=-MAX_IN, max=MAX_IN))
    mult2, bufm2, bufm22 = [Signal(intbv(0, min=0, max=MAX_LOW)) for _ in range(3)]
    adder, bufout = [Signal(intbv(0, min=-MAX_OUT, max=MAX_OUT)) for _ in range(2)]
    pipe_buf, n_pipe = create_signals(2, len(p), signed=True)

    @always(clk.posedge)
    def clocked_logic():
        if rst:
            bufm1.next = 0
            bufm11.next = 0
            bufm2.next = 0
            bufm22.next = 0
            bufm3.next = 0
            bufm4.next = 0
            bufm34.next = 0
            bufout.next = 0
            au_buf.next = 0
            bu_buf.next = 0
            al_buf.next = 0
            bl_buf.next = 0
            pipe_buf.next = 0
        else:
            bufm1.next = mult1
            bufm11.next = bufm1
            bufm2.next = mult2
            bufm22.next = bufm2
            bufm3.next = mult3
            bufm4.next = mult4
            bufm34.next = addLow
            bufout.next = adder
            au_buf.next = a_upper
            bu_buf.next = b_upper
            al_buf.next = a_lower
            bl_buf.next = b_lower
            pipe_buf.next = n_pipe

    @always_comb
    def comb_logic():
        a_upper.next = a[A_MAX:A_MAX - MULTMAX].signed()
        a_lower.next = concat(False, a[A_MAX - MULTMAX:])
        b_upper.next = b[A_MAX:A_MAX - MULTMAX].signed()
        b_lower.next = concat(False, b[A_MAX - MULTMAX:])
        n_pipe.next = bufout
        p.next = pipe_buf

    @always_comb
    def adders():
        addLow.next = (bufm3 + bufm4)
        x = (bufm11 << (A_MAX - 1)) + concat(False, bufm22)
        y = (bufm34 << (A_MAX - MULTMAX))

        adder.next = int(x) + int(y)

    @always_comb
    def multipliers():
        mult1.next = au_buf * bu_buf
        mult2.next = al_buf[:] * bl_buf[:]
        mult3.next = au_buf * bl_buf
        mult4.next = al_buf * bu_buf

    return clocked_logic, comb_logic, adders, multipliers


@block
def AddressableMultiplier35Bit(clk, ce, rst, a, b, p, address_in, address_out):
    assert address_in.min == address_out.min and \
        address_in.max == address_out.max

    #: Shift register with 4 clock cycles delay (multiplier pipeline)
    address_shift = ShiftRegister(address_in, ce, address_out, clk, rst, 5)
    multiplier = Multiplier35Bit(a, b, p, clk, rst)

    return address_shift, multiplier


@block
def SharedMultiplier(clk, ce, rst, a_signals, b_signals, load, p_signals, p_rdys):
    assert len(a_signals) == len(b_signals) == len(p_signals)
    assert load.max >= len(a_signals) + 1, "Make sure all signals can be loaded and one extra space for the empty load"
    assert len(a_signals[0]) == 35
    assert len(p_signals[0]) == 70

    mult_a, mult_b = create_signals(2, 35, signed=True)
    mult_out = create_signals(1, 2 * 35, signed=True)
    addr_in, addr_out = create_signals(2, 3)

    output_buffers = create_signals(len(p_signals), 2 * 35, signed=True)
    ready_buffers = create_signals(len(p_signals))

    mult_inst = AddressableMultiplier35Bit(mult_a, mult_b, mult_out, addr_in,
                                           addr_out, ce, clk, rst)

    @always(clk.posedge)
    def load_data():
        if load > 0:
            mult_a.next = a_signals[load - 1]
            mult_b.next = b_signals[load - 1]
            addr_in.next = load
        else:
            mult_a.next = 0
            mult_b.next = 0
            addr_in.next = 0

    @always(clk.posedge)
    def clock_output():
        for i in range(len(p_signals)):
            output_buffers[i].next = output_buffers[i]
            ready_buffers[i].next = False
            if addr_out == i + 1:
                output_buffers[i].next = mult_out
                ready_buffers[i].next = True

    @always_comb
    def set_output():
        for i in range(len(p_signals)):
            p_signals[i].next = output_buffers[i]
            p_rdys[i].next = ready_buffers[i]

    return mult_inst, load_data, clock_output, set_output


@block
def ThreePortMultiplier35Bit(a, b, c, d, e, f, load, clk_ena, clk, rst,
                             ab, ab_rdy, cd, cd_rdy, ef, ef_rdy):
    assert a._nrbits == b._nrbits == c._nrbits == d._nrbits == e._nrbits \
        == f._nrbits == 35
    assert len(load) > 1
    # Internal direct multiplier links
    mult_a, mult_b = create_signals(2, 35, signed=True)
    mult_out = create_signals(1, 2 * 35, signed=True)
    addr_in, addr_out = create_signals(2, 3)

    p_ab, p_cd, p_ef = create_signals(3, 2 * 35, signed=True)
    ab_rdy_dly, cd_rdy_dly, ef_rdy_dly = create_signals(3)

    mult_inst = AddressableMultiplier35Bit(mult_a, mult_b, mult_out, addr_in,
                                           addr_out, clk_ena, clk, rst)

    @always(clk.posedge)
    def load_data():
        if load == 1:
            mult_a.next = a
            mult_b.next = b
            addr_in.next = 1
        elif load == 2:
            mult_a.next = c
            mult_b.next = d
            addr_in.next = 2
        elif load == 3:
            mult_a.next = e
            mult_b.next = f
            addr_in.next = 3
        else:
            mult_a.next = 0
            mult_b.next = 0
            addr_in.next = 0

    @always(clk.posedge)
    def clock_output():
        p_ab.next = p_ab
        p_cd.next = p_cd
        p_ef.next = p_ef
        ab_rdy_dly.next = False
        cd_rdy_dly.next = False
        ef_rdy_dly.next = False
        if addr_out == 1:
            p_ab.next = mult_out
            ab_rdy_dly.next = True
        elif addr_out == 2:
            p_cd.next = mult_out
            cd_rdy_dly.next = True
        elif addr_out == 3:
            p_ef.next = mult_out
            ef_rdy_dly.next = True

    @always_comb
    def set_output_ab():
        ab.next = p_ab
        ab_rdy.next = ab_rdy_dly

    @always_comb
    def set_output_cd():
        cd.next = p_cd
        cd_rdy.next = cd_rdy_dly

    @always_comb
    def set_output_ef():
        ef.next = p_ef
        ef_rdy.next = ef_rdy_dly

    return mult_inst, load_data, clock_output, set_output_ab, set_output_cd, \
        set_output_ef
