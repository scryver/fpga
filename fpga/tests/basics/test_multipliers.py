#!/usr/bin/env python

__author__ = 'michiel'

from random import randrange

from myhdl import Signal, instance, intbv

import fpga.basics.multiplier as mult
from fpga.tests.test_utils import clocker, run_sim


def test_multiplier35bit(time_steps=20000, trace=False):
    def bench():
        ticks = 4
        BITS = 35
        MAX = 2 ** BITS // 2
        MAXOUT = 2 ** (BITS * 2) // 2
        a, b = [Signal(intbv(0, min=-MAX, max=MAX)) for _ in range(2)]
        pipeA, pipeB = [[Signal(intbv(0, min=-MAX, max=MAX)) for _ in range(ticks)] for _ in range(2)]
        p = Signal(intbv(0, min=-MAXOUT, max=MAXOUT))
        clk, rst = [Signal(False) for _ in range(2)]

        mult_inst = mult.Multiplier35Bit(a, b, p, clk, rst)

        clock_gen = clocker(clk)

        # @always(clk.negedge)
        # def stimulus():
        #     a.next = randrange(-MAX, MAX)
        #     b.next = randrange(-MAX, MAX)

        @instance
        def stimulus():
            iA, iB, pA, pB = 0, 0, 1, 1
            yield clk.negedge
            rst.next = False

            while True:
                yield clk.negedge
                a.next = randrange(-MAX, MAX)
                b.next = randrange(-MAX, MAX)
                pipeA[iA].next = a
                pipeB[iB].next = b
                iA = (iA + 1) % ticks
                iB = (iB + 1) % ticks
                if (p != pipeA[pA] * pipeB[pB]):
                    print "{:5.4f}x{:5.4f} = {:5.4f} but got {:5.4f}, error: {:5.4f}".format(a/float(MAX), b/float(MAX), (pipeA[pA] * pipeB[pB])/float(MAXOUT), p/float(MAXOUT), (pipeA[pA] * pipeB[pB] - p)/float(MAXOUT))
                assert p == pipeA[pA] * pipeB[pB], "Difference: p - a * b = {}".format(bin(p - pipeA[pA] * pipeB[pB]))

                pA = (pA + 1) % ticks
                pB = (pB + 1) % ticks

        return mult_inst, clock_gen, stimulus

    run_sim(bench, time_steps, trace)


if __name__ == '__main__':
    test_multiplier35bit()