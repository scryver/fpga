#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import Signal, instance, intbv, downrange, concat, always
from fpga.utils import EdgeDetect

def Encoder(din, dclk, dout, clock, reset):

    pos_edge = Signal(False)
    neg_edge = Signal(False)

    edge = EdgeDetect(dclk, pos_edge, neg_edge, clock, reset)

    @instance
    def process():
        while True:
            yield clock.posedge, reset.posedge

            if reset:
                pos_edge.next = False
                neg_edge.next = False
                dout.next = False
            else:
                if pos_edge or (neg_edge and din):
                    dout.next = not dout

    return edge, process

def Decoder(din, locked, dclk, dout, clock, reset):

    MAX_CLK_MULT = 256

    p_edge = Signal(False)
    n_edge = Signal(False)
    edge = EdgeDetect(din, p_edge, n_edge, clock, reset)
    current_cycle = Signal(intbv(0, min=0, max=MAX_CLK_MULT))
    prev_cycle = Signal(intbv(0, min=0, max=MAX_CLK_MULT))
    min_cycle = Signal(intbv(MAX_CLK_MULT - 1, min=0, max=MAX_CLK_MULT))
    edge_counter = EdgeCounter(din, locked, min_cycle, current_cycle, prev_cycle, clock, reset)
    # max_cycle = Signal(intbv(0, min=0, max=MAX_CLK_MULT))

    @instance
    def clock_counter():
        count = intbv(0, min=0, max=MAX_CLK_MULT / 2)
        while True:
            yield clock.posedge, reset.posedge

            if reset:
                count[:] = 0
                dclk.next = False
            else:
                if locked and count > min_cycle:
                    count[:] = 0
                    dclk.next = not dclk

                if count == MAX_CLK_MULT / 2 - 1:
                    count[:] = 0
                else:
                    count += 1

    @instance
    def compare():
        half_one = False
        # min_cycle = intbv(0, min=0, max=MAX_CLK_MULT)
        max_cycle = intbv(0, min=0, max=MAX_CLK_MULT)
        prev_min  = intbv(0, min=0, max=MAX_CLK_MULT)
        prev_max  = intbv(0, min=0, max=MAX_CLK_MULT)

        while True:
            yield clock.posedge, reset.posedge

            if reset:
                half_one = False
                max_cycle[:] = 0
                prev_min[:] = 0
                prev_max[:] = 0
                dout.next = False
            else:
                prev_min[:] = prev_cycle - (prev_cycle >> 2)    # 0.75 = 1 - 0.25 = x - rshift(2)
                prev_max[:] = prev_cycle + (prev_cycle >> 1)    #  1.5 = 1 + 0.5  = x + rshift(1)

                if (prev_min <= current_cycle <= prev_max) or current_cycle == 0 or prev_cycle == 0:
                    if locked:
                        if half_one:
                            dout.next = True
                        else:
                            dout.next = False
                    else:
                        dout.next = False
                elif current_cycle > prev_max:
                    dout.next = False
                    max_cycle[:] = current_cycle
                    half_one = False
                elif current_cycle < prev_min:
                    max_cycle[:] = prev_cycle
                    half_one = True

    return edge, edge_counter, clock_counter, compare


def EdgeCounter(din, locked, minimum, current, prev, clock, reset):

    MAX_CLK_MULT = current.max

    p_edge = Signal(False)
    n_edge = Signal(False)
    edge = EdgeDetect(din, p_edge, n_edge, clock, reset)

    @instance
    def edge_counter():
        count = intbv(0, min=0, max=MAX_CLK_MULT)
        first = True
        while True:
            yield clock.posedge, reset.posedge

            if reset:
                current.next = 0
                prev.next = 0
                minimum.next = minimum.max - 1
                count[:] = 0
                first = True
                locked.next = False
            else:
                if 0 < current < minimum:
                    minimum.next = current

                if p_edge or n_edge:
                    first = False
                    prev.next = current
                    current.next = count
                    count[:] = 0
                elif not first:
                    if prev > 0 and current > 0 and prev != current:
                        locked.next = True
                    if count < MAX_CLK_MULT - 1:
                        count += 1
                    else:
                        count[:] = 0

    return edge, edge_counter