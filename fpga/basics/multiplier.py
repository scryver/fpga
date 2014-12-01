#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import Signal, intbv, always, always_comb, concat, toVHDL


def Multiplier35Bit(a, b, p, clk, rst):

    """
    Some text here
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

    @always_comb
    def comb_logic():
        a_upper.next = a[A_MAX:A_MAX - MULTMAX].signed()
        a_lower.next = concat(False, a[A_MAX - MULTMAX:])
        b_upper.next = b[A_MAX:A_MAX - MULTMAX].signed()
        b_lower.next = concat(False, b[A_MAX - MULTMAX:])
        p.next = bufout

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


def convert():
    BITS = 35
    MAX = 2 ** BITS // 2
    MAXOUT = 2 ** (BITS * 2) // 2
    a, b = [Signal(intbv(0, min=-MAX, max=MAX)) for _ in range(2)]
    p = Signal(intbv(0, min=-MAXOUT, max=MAXOUT))
    clk, rst = [Signal(False) for _ in range(2)]

    toVHDL(Multiplier35Bit, a, b, p, clk, rst)

convert()