from fpga import CustomVHDL
from fpga.utils import create_signals, create_clock_reset

import fpga.basics.flipflops as ff


def convert_async_dff():
    q, d = create_signals(2, 4)
    clk, rst = create_clock_reset(rst_async=True)

    converter = CustomVHDL()
    converter(ff.dff, q, d, clk, rst)


def convert_dff():
    q, d = create_signals(2, 4)
    clk, rst = create_clock_reset(rst_async=True)

    converter = CustomVHDL()
    converter(ff.dff, q, d, clk)


if __name__ == '__main__':
    convert_dff()
    # convert_async_dff()
