#!/usr/bin/env python
from fpga.utils import create_std_logic

__author__ = 'michiel'

import random
import fpga.utils as utils
from myhdl import always, instance, delay, StopSimulation, Simulation, traceSignals


def clocker(clock, half_cycle=10):
    @always(delay(half_cycle))
    def clock_generator():
        clock.next = not clock

    return clock_generator


def clockdiv(edge, clockdivided, counter, cycles, single_pulse=False):
    """

    :param edge:
    :param clockdivided:
    :param counter:
    :param cycles:
    :param single_pulse:     If True a single cycle pulse will be created, if False a clock with 50% duty cycle
    :return:
    """
    @always(edge)
    def clock_divider():
        if counter < cycles - 1:
            counter.next += 1
            if single_pulse:
                clockdivided.next = False
        else:
            counter.next = 0
            if single_pulse:
                clockdivided.next = True
            else:
                clockdivided.next = not clockdivided

    return clock_divider


def run_sim(bench, time_steps=None, trace=False):
    try:
        M = len(bench)
        benches = tuple(bench)
    except TypeError:
        M = 1
        benches = (bench, )

    b = []
    if trace:
        for i in range(M):
            b.append(traceSignals(benches[i]))
    else:
        for i in range(M):
            b.append(benches[i]())

    if M == 1:
        s = Simulation(b[0])
    else:
        s = Simulation(tuple(b))
    s.run(time_steps)


def benchEdgeDetect(tests=100):

    din, p_edge, n_edge, clock, reset = create_std_logic(5)

    dut = utils.EdgeDetect(din, p_edge, n_edge, clock, reset)

    clockgen = clocker(clock)

    test_stream = []
    pos_stream = []
    neg_stream = []

    for i in range(tests):
        try:
            prev_test = test_stream[i - 1]
        except IndexError:
            prev_test = False

        current_test = random.randint(0, 1)
        p = bool(current_test and not prev_test)
        n = bool(not current_test and prev_test)
        test_stream.append(bool(current_test))
        pos_stream.append(p)
        neg_stream.append(n)

    @instance
    def check():
        yield clock.negedge
        reset.next = False

        for t, p, n in zip(test_stream, pos_stream, neg_stream):
            yield clock.negedge
            # print "t: %s, p: %s, n: %s" % (t, p, n)
            din.next = t
            yield clock.negedge
            # print "d: %s, p: %s, n: %s" % (din, p_edge, n_edge)
            assert p == p_edge
            assert n == n_edge

        raise StopSimulation

    return dut, clockgen, check

def test_bench():
    run_sim(benchEdgeDetect)


if __name__ == '__main__':
    test_bench()
