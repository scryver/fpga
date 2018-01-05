#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import block, intbv, concat, instance, always_seq, always_comb
from fpga.utils import create_signals


@block
def Parallel2Serial(clock, reset, load, din, dout, MSB_FIRST=True):

    """ Parallel to serial converter
    On load: load in din to buffer and outputs the MSB/LSB directly to dout
    On every clock cycle shift buffer depending on MSB_FIRST and output the
    relevant bit. It's up to the programmer to get the signal sizes right.

    :param din:
    :param load:
    :param dout:
    :param clock:
    :param reset:
    :return:
    """

    # MSB_FIRST = True
    M = len(din)
    buf, nbuf = create_signals(2, (din.min, din.max))

    @always_seq(clock.posedge, reset)
    def shift_reg():
        if load:
            buf.next = din
        else:
            buf.next = nbuf

    if MSB_FIRST:
        @always_comb
        def shift_logic():
            dout.next = buf[M - 1]
            nbuf.next = concat(buf[M - 1:0], False)
    else:
        @always_comb
        def shift_logic():
            dout.next = buf[0]
            nbuf.next = concat(False, buf[M:1])

    return shift_reg, shift_logic
