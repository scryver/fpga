from fpga import toVHDL
from fpga.utils import create_signals, create_clock_reset

import fpga.basics.parallel2serial as p2s


def convert_p2s_msb():
    i, o = create_signals(2, 8, signed=True)
    load = create_signals(1)
    clk, rst = create_clock_reset()

    toVHDL(p2s.p2s_msb, i, load, o, clk, rst)

if __name__ == '__main__':
    convert_p2s_msb()

