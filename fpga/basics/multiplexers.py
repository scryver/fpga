#!/usr/env/python

from __future__ import print_function
from myhdl import block, Signal, intbv, always

__author__ = 'michiel'


@block
def mux3(a, b, c, dout, sel, zero_start=True):

    if zero_start:
        @always(a, b, c, sel)
        def logic():
            if sel == 0:
                dout.next = a
            elif sel == 1:
                dout.next = b
            else:
                dout.next = c
    else:
        @always(a, b, c, sel)
        def logic():
            if sel == 1:
                dout.next = a
            elif sel == 2:
                dout.next = b
            elif sel == 3:
                dout.next = c
            else:
                dout.next = 0

    return logic


@block
def mux2(a, b, dout, sel):

    @always(a, b, sel)
    def logic():
        if sel == 0:
            dout.next = a
        else:
            dout.next = b

    return logic
