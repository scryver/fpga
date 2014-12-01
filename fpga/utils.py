#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import Signal, instance, intbv, modbv


def EdgeDetect(din, pos_edge, neg_edge, clock, reset):

    prev_din = Signal(False)

    @instance
    def process():
        while True:
            yield clock.posedge, reset.posedge

            if reset:
                prev_din.next = False
                pos_edge.next = False
                neg_edge.next = False
            else:
                pos_edge.next = din and not prev_din
                neg_edge.next = not din and prev_din
                prev_din.next = din

    return process


def create_std_logic(nr_signals):
    from warnings import warn
    warn("Will be replaced by create_signals")
    return create_signals(nr_signals)


def create_signals(nr_signals, bits=1, signed=False, enum=None, mod=False, delay=2):
    if enum is not None:
        if delay is not None:
            return [Signal(enum, delay) for _ in range(nr_signals)]
        else:
            return [Signal(enum) for _ in range(nr_signals)]

    if bits == 1:
        default = False
    else:
        if signed:
            mini = -(2 ** (bits - 1))
            maxi = 2 ** (bits - 1)
        else:
            mini = 0
            maxi = 2 ** bits

        if mod:
            default = modbv(0, min=mini, max=maxi)
        else:
            default = intbv(0, min=mini, max=maxi)

    if delay is not None:
        if nr_signals > 1:
            return [Signal(default, delay) for _ in range(nr_signals)]
        else:
            return Signal(default, delay)
    else:
        if nr_signals > 1:
            return [Signal(default) for _ in range(nr_signals)]
        else:
            return Signal(default)