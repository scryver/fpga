#!/usr/bin/env python

__author__ = 'michiel'

from random import randrange

from myhdl import Signal, always, delay, instance, intbv

import fpga.basics.flipflops as ff
from fpga.tests.test_utils import clocker, run_sim


def test_dff(time_steps=2000, trace=False):
    def bench():
        q, d, clock = [Signal(False) for _ in range(3)]

        dff_inst = ff.dff(q, d, clock)

        clock_gen = clocker(clock)

        @always(clock.negedge)
        def stimulus():
            assert d == q
            d.next = randrange(2)

        return dff_inst, clock_gen, stimulus

    run_sim(bench, time_steps, trace)


def test_dff_async(time_steps=2000, trace=False):
    def bench():
        q, d = [Signal(intbv(0, min=0, max=256)) for _ in range(2)]
        clock, reset, p_rst = [Signal(False) for _ in range(3)]

        dffa_inst = ff.dff_async(q, d, clock, reset)

        clock_gen = clocker(clock)

        @always(clock.negedge)
        def stimulus():
            if reset and p_rst:
                assert d == q

            p_rst.next = reset
            d.next = randrange(2)

        @instance
        def reset_gen():
            yield delay(5)
            reset.next = 1

            while True:
                yield delay(randrange(500, 1000))
                reset.next = 0
                yield delay(randrange(80, 140))
                reset.next = 1

        return dffa_inst, clock_gen, stimulus, reset_gen

    run_sim(bench, time_steps, trace)


def test_latch(time_steps=2000, trace=False):
    def bench():
        q, d, g = [Signal(False) for _ in range(3)]

        latch_inst = ff.latch(q, d, g)

        @always(delay(7))
        def dgen():
            d.next = randrange(2)

        @always(delay(41))
        def ggen():
            g.next = randrange(2)

        return latch_inst, dgen, ggen

    run_sim(bench, time_steps, trace)


if __name__ == '__main__':
    test_dff()
    test_dff_async(20000)
    test_latch(200)