#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import always, always_comb, always_seq


def dff(q, d, clk, rst=None):
    """Async depends on reset signal, see fpga.utils.create_clock_reset() and
    myhdl.ResetSignal.

    D-FlipFlop with async or sync reset.
    For Xilinx ram use, make sure to supply a synced-reset, it apparantly works
    better."""
    # TODO (michiel): insert app note here

    if rst is not None:
        @always_seq(clk.posedge, rst)
        def logic():
            q.next = d
    else:
        @always(clk.posedge)
        def logic():
            q.next = d

    return logic


def dffe(q, d, enable, clk):

    @always(clk.posedge)
    def logic():
        if enable:
            q.next = d

    return logic


def dffe_rst(q, d, enable, clk, rst):

    @always(clk.posedge)
    def logic():
        if rst:
            q.next = 0
        elif enable:
            q.next = d

    return logic


def dff_set(q, d, s, clk):

    try:
        BITS = len(d)
        MAX = 2 ** BITS - 1
    except TypeError:
        MAX = True

    @always(clk.posedge)
    def logic():
        if s:
            q.next = MAX
        else:
            q.next = d

    return logic


def latch(q, d, g):

    # The @always_comb doesn't mean the generator describes a circuit that is necessarily combinatorial,
    # but merely that it triggers whenever one of the input signals changes
    @always_comb
    def logic():
        if g == 1:
            q.next = d

    return logic
