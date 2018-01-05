#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import block, always, always_comb, Signal, intbv, modbv


@block
def ModCounter(clk, enable, clear, count):

    assert isinstance(count._val, modbv)

    if isinstance(enable, bool):
        assert enable, "Enable never True cannot be allowed!"

        @always(clk.posedge)
        def counting():
            if clear == True:
                count.next = 0
            else:
                count.next = count + 1
    else:
        @always(clk.posedge)
        def counting():
            if clear == True:
                count.next = 0
            elif enable == True:
                count.next = count + 1

    return counting


@block
def CountTo(clk, enable, clear, reached, MAX_CLOCK=32):

    count = Signal(intbv(0, min=0, max=MAX_CLOCK))

    MAX_CLOCK = MAX_CLOCK - 1 # Rest of the code is 0 indexed

    if isinstance(enable, bool):
        assert enable, "Enable never True cannot be allowed!"

        @always(clk.posedge)
        def counting():
            if clear == True:
                count.next = 0
            elif count != MAX_CLOCK:
                count.next = count + 1
    else:
        @always(clk.posedge)
        def counting():
            if clear == True:
                count.next = 0
            elif (enable == True) and (count != MAX_CLOCK):
                count.next = count + 1

    @always_comb
    def reach_logic():
        reached.next = count == MAX_CLOCK

    return counting, reach_logic
