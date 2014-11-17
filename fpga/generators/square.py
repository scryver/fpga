#!/usr/bin/env python

__author__ = 'michiel'


from myhdl import Signal, intbv, always
from math import log


FS = 48000          # Base sample rate
FS_MODE = 4         # Sample rate multiplier for output (1Fs, 2Fs, 4Fs)
CLK_FREQ = 64       # Clock frequency multiplier (if 64: clk = 64 * FS_MODE * Fs)


def SquareGenerator(freq, duty, dout, clk, reset):

    # freq.max = FS / 2
    # freq.min = 0Hz

    M = len(freq)       # Bits
    CLK_MULT = FS_MODE * CLK_FREQ
    HALF_HZ_CYCLES = CLK_MULT * FS
    extra_bits = log(CLK_MULT, 2)

    assert M > extra_bits

    count = Signal(intbv(0, _nrbits=M + extra_bits))
    count_max = Signal(intbv(0, _nrbits=M + extra_bits))

    @always(clk.posedge)
    def set_freq():
        count_max.next = ((freq << (extra_bits - M)) + CLK_MULT) << (freq // M)

    @always(clk.posedge)
    def counting():
        if count < count_max - 1:
            count.next += 1
        else:
            count.next = 0
            dout.next = not dout

    return set_freq, counting