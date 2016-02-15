#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import Signal, instance, intbv, modbv, ResetSignal


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


def create_signals(nr_signals, bits=1, signed=False, enum=None, mod=False,
                   delay=2):
    """Create usable signals for MyHDL."""
    if enum is not None:
        if delay is not None:
            return [Signal(enum, delay) for _ in range(nr_signals)]
        else:
            return [Signal(enum) for _ in range(nr_signals)]

    def modOrInt(min, max, mod):
        if mod:
            return modbv(0, min=min, max=max)
        else:
            return intbv(0, min=min, max=max)

    if bits == 1:
        default = False
    elif isinstance(bits, (tuple, list)):
        mini = bits[0]
        maxi = bits[1]
        default = modOrInt(mini, maxi, mod)
    else:
        if signed:
            mini = -(2 ** (bits - 1))
            maxi = 2 ** (bits - 1)
        else:
            mini = 0
            maxi = 2 ** bits
        default = modOrInt(mini, maxi, mod)

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


def create_clock_reset(rst_value=True, rst_active=True, rst_async=False):
    return Signal(False), ResetSignal(val=rst_value, active=rst_active,
                                      async=rst_async)


def binarystring(signal, prefix="0b"):
    s = ''
    if prefix:
        s += prefix

    s += "{}" * signal._nrbits

    return s.format(*map(int, (signal[signal._nrbits - 1 - i]
                               for i in range(signal._nrbits))))
