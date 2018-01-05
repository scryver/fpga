#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import block, always, always_comb, always_seq, ResetSignal


@block
def dff(clk, d, q, enable=True, reset=None, reset_active=1):
    """Async depends on reset signal, see fpga.utils.create_clock_reset() and
    myhdl.ResetSignal.

    D-FlipFlop with async or sync reset.
    For Xilinx ram use, make sure to supply a synced-reset, it apparantly works
    better."""
    # TODO (michiel): insert app note here

    if isinstance(enable, bool):
        assert enable, "Enable never True cannot be allowed!"
        if reset is None or isinstance(reset, ResetSignal):
            @always_seq(clk.posedge, reset)
            def logic():
                q.next = d
        else:
            @always(clk.posedge)
            def logic():
                if reset == reset_active:
                    q.next = 0
                else:
                    q.next = d
    else:
        if reset is None or isinstance(reset, ResetSignal):
            @always_seq(clk.posedge, reset)
            def logic():
                if enable:
                    q.next = d
        else:
            @always(clk.posedge)
            def logic():
                if reset == reset_active:
                    q.next = 0
                elif enable:
                    q.next = d

    return logic

#
# @block
# def dff_set(clk, s, d, q):
#
#     try:
#         BITS = len(d)
#         MAX = 2 ** BITS - 1
#     except TypeError:
#         MAX = True
#
#     @always(clk.posedge)
#     def logic():
#         if s:
#             q.next = MAX
#         else:
#             q.next = d
#
#     return logic
#
#
# @block
# def dff_set_reset(clk, s, r, d, q):

def latch(g, d, q):

    # The @always_comb doesn't mean the generator describes a circuit that is necessarily combinatorial,
    # but merely that it triggers whenever one of the input signals changes
    @always_comb
    def logic():
        if g == 1:
            q.next = d

    return logic
