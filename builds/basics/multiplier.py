from fpga import toVHDL
from fpga.utils import create_signals, create_clock_reset

import fpga.basics.multiplier as mult


def convert_multiplier():
    BITS = 35
    a, b = create_signals(2, BITS, signed=True, delay=None)
    p = create_signals(1, 2 * BITS, signed=True, delay=None)
    clk, rst = create_clock_reset()

    toVHDL(mult.Multiplier35Bit, a, b, p, clk, rst)


def convert_addressable_multiplier():
    BITS = 35
    ADDRESSES = 3
    a, b = create_signals(2, BITS, signed=True, delay=None)
    p = create_signals(1, 2 * BITS, signed=True, delay=None)
    address_in, address_out = create_signals(2, (0, ADDRESSES + 1), mod=True)
    ce = create_signals(1)
    clk, rst = create_clock_reset()

    toVHDL(mult.AddressableMultiplier35Bit, a, b, p, address_in, address_out,
           ce, clk, rst)


def convert_three_port_multiplier():
    BITS = 35
    a, b, c, d, e, f = create_signals(6, BITS, signed=True, delay=None)
    load = create_signals(1, (0, 4))
    clk_ena = create_signals(1)
    clk, rst = create_clock_reset()
    ab_rdy, cd_rdy, ef_rdy = create_signals(3)
    ab, cd, ef = create_signals(3, 2 * BITS, signed=True, delay=None)

    toVHDL(mult.ThreePortMultiplier35Bit, a, b, c, d, e, f, load,
           clk_ena, clk, rst, ab, ab_rdy, cd, cd_rdy, ef, ef_rdy)


def convert_shared_multiplier():
    # @TODO (michiel): This fails
    inputs = create_signals(6, 35, signed=True, delay=None)
    load = create_signals(1, 2, delay=None)

    p_sigs = create_signals(3, 2 * 35, signed=True, delay=None)
    p_rdys = create_signals(3, delay=None)

    ce = create_signals(1)
    clk, rst = create_clock_reset()
    left, right = create_signals(2, 32, signed=True, delay=None)

    toVHDL(mult.SharedMultiplier, inputs[:3], inputs[3:], load, ce, clk, rst,
           p_sigs, p_rdys)


if __name__ == '__main__':
    convert_multiplier()
    convert_addressable_multiplier()
    convert_three_port_multiplier()
    # convert_shared_multiplier()
