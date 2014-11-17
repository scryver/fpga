#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import intbv, concat, instance


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

    @instance
    def shift_reg():
        buffer = intbv(0, min=din.min, max=din.max)

        while True:
            yield clock.posedge, reset.posedge

            # if MSB_FIRST:
            dout.next = buffer[M - 1]
            # else:
            #     dout.next = buffer[0]

            if load:
                buffer[:] = din
            else:
                # if MSB_FIRST:
                buffer[:] = concat(buffer[M-1:0], False)
                # else:
                #     buffer[:] = concat(False, buffer[M:1])

    return shift_reg


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
        buffer = intbv(0, min=din.min, max=din.max)

        while True:
            yield clock.posedge, reset.posedge

            dout.next = buffer[0]

            if load:
                buffer[:] = din
            else:
                buffer[:] = concat(False, buffer[M:1])

    return shift_reg