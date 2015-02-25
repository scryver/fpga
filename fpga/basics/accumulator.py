#!/usr/bin/env python

from myhdl import always_comb, always_seq
from fpga.utils import create_signals

__author__ = 'michiel'


def Accumulator(din, ce, clr, dout, clk):

    accum, n_accum = create_signals(2, len(dout), dout.min < 0)

    @always_comb
    def output():
        dout.next = accum

    @always_seq(clk.posedge, reset=None)
    def clocked():
        if clr:
            accum.next = 0
        elif ce:
            accum.next = n_accum

    @always_comb
    def logic():
        n_accum.next = accum + din

    return output, clocked, logic