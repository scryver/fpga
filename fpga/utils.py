#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import Signal, instance


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
    return [Signal(False) for _ in range(nr_signals)]