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
    MULTMAX = 18
    M = 35 + 1
    MOUT = 2 * M
    MAX_IN = 2 ** M // 2
    MAX_LOW = 2 ** (M - 2)
    MAX_OUT = 2 ** MOUT // 2

    mult1, mult3, mult4, bufm1, bufm11, bufm3, bufm4, bufm34 = [Signal(intbv(0, min=-MAX_IN, max=MAX_IN)) for _ in range(8)]
    addLow = Signal(intbv(0, min=-MAX_IN * 2, max=MAX_IN*2))
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
        else:
            bufm1.next = mult1
            bufm11.next = bufm1
            bufm2.next = mult2
            bufm22.next = bufm2
            bufm3.next = mult3
            bufm4.next = mult4
            bufm34.next = addLow[35:].signed()
            bufout.next = adder

    @always_comb
    def comb_logic():
        p.next = bufout

    @always_comb
    def adders():
        addLow.next = (bufm3 + bufm4)
        x = (bufm11 << 34) + bufm22
        y = (bufm34 << 17)

        adder.next = int(x) + int(y)

    @always_comb
    def multipliers():
        mult1.next = a[35:17] * b[35:17]
        mult2.next = concat(False, a[17:]) * concat(False, b[17:])
        mult3.next = a[35:17] * concat(False, b[17:])
        mult4.next = concat(False, a[17:]) * b[35:17]

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