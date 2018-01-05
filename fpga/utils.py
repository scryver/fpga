#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import block, always_seq, intbv, modbv, Signal, ResetSignal

__all__ = [
    'EdgeDetect',
    'create_signals',
    'create_clock_reset',
    'binarystring',
]

@block
def EdgeDetect(clock, reset, din, pos_edge, neg_edge, reset_active=1):

    prev_din = Signal(False)

    if reset is None or isinstance(reset, ResetSignal):
        @always_seq(clock.posedge, reset=reset)
        def process():
            pos_edge.next = din and not prev_din
            neg_edge.next = not din and prev_din
            prev_din.next = din
    else:
        @always(clock.posedge)
        def process():
            if reset == reset_active:
                pos_edge.next = 0
                neg_edge.next = 0
                prev_din.next = 0
            else:
                pos_edge.next = din and not prev_din
                neg_edge.next = not din and prev_din
                prev_din.next = din

    return process


def create_same_signals(nr_signals, example, delay=2):
    return create_signals(nr_signals, example._nrbits, signed=(example.min < 0),
                          mod=isinstance(example, modbv), delay=delay)


def create_signals(nr_signals, bits=1, signed=False, enum=None, mod=False,
                   delay=2, default_value=None):
    """Create usable signals for MyHDL."""
    if enum is not None:
        if delay is not None:
            return [Signal(enum, delay) for _ in range(nr_signals)]
        else:
            return [Signal(enum) for _ in range(nr_signals)]

    def modOrInt(min, max, mod):
        if mod:
            return modbv(0 if default_value is None else default_value, min=min, max=max)
        else:
            return intbv(0 if default_value is None else default_value, min=min, max=max)

    if bits == 1:
        default = False if default_value is None else default_value
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


def create_clock_reset_old(rst_value=True, rst_active=True, rst_async=False):
    print("Warning: Don't use the ResetSignal as a precaution, the default values don't seem to work...")
    return Signal(False), ResetSignal(val=rst_value, active=rst_active,
                                      async=rst_async)


def create_clock_reset(rst_active=1):
    return Signal(False), Signal(bool(rst_active))


def binarystring(signal, prefix="0b"):
    s = ''
    if prefix:
        s += prefix

    s += "{}" * signal._nrbits

    return s.format(*map(int, (signal[signal._nrbits - 1 - i]
                               for i in range(signal._nrbits))))
