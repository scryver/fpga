#!/usr/bin/env python

__author__ = 'michiel'

from random import randrange

from myhdl import always, delay, instance

import fpga.basics.flipflops as ff
from fpga.utils import create_clock_reset, create_signals
from fpga.tests.test_utils import clocker, run_sim


class Test:
    template = """def dff(q, d, clk):

    @always(clk.posedge)
    def logic():
        q.next = d

    return logic"""

t = Test()
exec(t.template)


def test_dff(time_steps=2000, trace=False):
    def bench():
        q, d, clock = create_signals(3)

        # dff_inst = ff.dff(q, d, clock)
        dff_inst = dff(q, d, clock)
        clock_gen = clocker(clock)

        @always(clock.negedge)
        def stimulus():
            assert d == q
            d.next = randrange(2)

        return dff_inst, clock_gen, stimulus

    run_sim(bench, time_steps, trace)


def test_dff_reset(time_steps=2000, trace=False):
    def bench_async():
        q, d = create_signals(2, 8)
        p_rst = create_signals(1)
        clock, reset = create_clock_reset(rst_active=False, rst_async=True)

        dffa_inst = ff.dff_reset(q, d, clock, reset)

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

    def bench_sync():
        q, d = create_signals(2, 8)
        p_rst = create_signals(1)
        clock, reset = create_clock_reset()

        dffa_inst = ff.dff_reset(q, d, clock, reset)

        clock_gen = clocker(clock)

        @always(clock.negedge)
        def stimulus():
            if not p_rst:
                assert d == q
            # print("CLK DOWN | {} | {} | {} | {} | {} ".format(reset, p_rst, d,
            #       q, clock))

            d.next = randrange(2)

        @always(clock.posedge)
        def reset_buf_dly():
            # print("CLK UP   | {} | {} | {} | {} | {} ".format(reset, p_rst, d,
            #       q, clock))
            p_rst.next = reset

        @instance
        def reset_gen():
            yield delay(5)
            reset.next = 0

            while True:
                yield delay(randrange(500, 1000))
                reset.next = 1
                yield delay(randrange(80, 140))
                reset.next = 0

        return dffa_inst, clock_gen, stimulus, reset_gen, reset_buf_dly

    run_sim(bench_async, time_steps, trace)
    run_sim(bench_sync, time_steps, trace)


def test_latch(time_steps=2000, trace=False):
    def bench():
        q, d, g = create_signals(3)

        latch_inst = ff.latch(q, d, g)

        @always(delay(7))
        def dgen():
            d.next = randrange(2)

        @always(delay(41))
        def ggen():
            g.next = randrange(2)

        @always(q.posedge, q.negedge)
        def qcheck():
            assert g and q == d

        return latch_inst, dgen, ggen, qcheck

    run_sim(bench, time_steps, trace)


if __name__ == '__main__':
    test_dff()
    test_dff_reset(20000)
    test_latch(200000)
