#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import Signal, intbv, instance, StopSimulation
import fpga.basics.parallel2serial as p2s
from tests.test_utils import clocker, run_sim


def test_p2s():
    def bench():
        M = 8
        load, dout_msb, dout_lsb, clock, reset = [Signal(False) for _ in range(5)]
        din = Signal(intbv(0, min=0, max=2**M))

        dut = p2s.p2s_msb(din, load, dout_msb, clock, reset)
        dut2 = p2s.p2s_lsb(din, load, dout_lsb, clock, reset)

        clockgen = clocker(clock)

        def input_gen():
            for i in range(2 ** M):
                yield i

        @instance
        def input_switch():
            yield clock.negedge
            a = input_gen()

            for i in range(2 ** M):
                din.next = next(a)
                for k in range(M):
                    yield clock.negedge
                    load.next = k == 0

        @instance
        def check():
            yield clock.negedge
            reset.next = False

            for j in range(2 ** M):
                yield load.negedge
                o_msb = intbv(0, min=din.min, max=din.max)
                o_lsb = intbv(0, min=din.min, max=din.max)
                for k in range(M):
                    yield clock.negedge
                    o_msb[M - 1 - k] = dout_msb
                    o_lsb[k] = dout_lsb

                # print(j, o_msb, o_lsb)
                assert j == o_msb == o_lsb

            raise StopSimulation

        return dut, dut2, clockgen, input_switch, check

    run_sim(bench)


if __name__ == '__main__':
    test_p2s()