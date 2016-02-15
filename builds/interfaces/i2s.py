from fpga import toVHDL
from fpga.utils import create_signals
from fpga.interfaces.i2s import I2S_Transmitter, I2S_Receiver


def convert_transmitter():
    left, right = create_signals(2, 32, signed=True, delay=None)
    # left, right = [Signal(intbv(0)[32:]) for _ in range(2)]
    load_left, load_right, sdata, ws, sclk, reset = create_signals(6, delay=None)

    toVHDL(I2S_Transmitter, left, right, load_left, load_right, sdata, ws, sclk,
           reset)


def convert_receiver():
    left, right = create_signals(2, 32, signed=True, delay=None)
    # left, right = [Signal(intbv(0)[32:]) for _ in range(2)]
    left_ready, right_ready, sdata, ws, sclk, reset = create_signals(6, delay=None)

    toVHDL(I2S_Receiver, sdata, ws, left, right, left_ready, right_ready, sclk,
           reset)

if __name__ == '__main__':
    convert_transmitter()
    convert_receiver()
