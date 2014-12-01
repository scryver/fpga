#!/usr/env/python

from __future__ import print_function
from myhdl import Signal, intbv, always

__author__ = 'michiel'


def mux3(a, b, c, dout, sel):

    @always(a, b, c, sel)
    def logic():
        if sel == 0:
            dout.next = a
        elif sel == 1:
            dout.next = b
        else:
            dout.next = c

    return logic