#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import intbv, concat, instance, always_seq, always_comb
from fpga.utils import create_signals


def p2s_msb(din, load, dout, clock, reset):

    """ Parallel to serial converter
    On load: load in din to buffer
    On every clock cycle shift buffer and output dout at upper or lower bound of buffer depending on MSB_FIRST

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

    @always_comb
    def input_logic():
        dout.next = buf[M - 1]
        nbuf.next = concat(buf[M - 1:0], False)

    # @instance
    # def shift_reg():
    #     buf = intbv(0, min=din.min, max=din.max)

    #     while True:
    #         yield clock.posedge, reset.posedge

    #         # if MSB_FIRST:
    #         dout.next = buf[M - 1]
    #         # else:
    #         #     dout.next = buf[0]

    #         if load:
    #             buf[:] = din
    #         else:
    #             # if MSB_FIRST:
    #             buf[:] = concat(buf[M-1:0], False)
    #             # buf[:] = buf[M - 1:0] << 1
    #             # else:
    #             #     buf[:] = concat(False, buf[M:1])

    return shift_reg, input_logic


def p2s_lsb(din, load, dout, clock, reset):

    """ Parallel to serial converter
    On load: load in din to buffer
    On every clock cycle shift buffer and output dout at upper or lower bound of buffer depending on MSB_FIRST

    :param din:
    :param load:
    :param dout:
    :param clock:
    :param reset:
    :return:
    """

    M = len(din)

    @instance
    def shift_reg():
        buf = intbv(0, min=din.min, max=din.max)

        while True:
            yield clock.posedge, reset.posedge

            dout.next = buf[0]

            if load:
                buf[:] = din
            else:
                buf[:] = concat(False, buf[M:1])

    return shift_reg
