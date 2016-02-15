#!/usr/bin/env python

from __future__ import print_function

__author__ = 'michiel'

from random import randrange

from myhdl import Signal, instance, intbv, bin, always

import fpga.basics.multiplier as mult
from fpga.utils import create_signals, create_clock_reset
from fpga.tests.test_utils import clocker, run_sim


def switchable_multiplier(time_steps=20000, trace=False):
    def bench():
        BITS = 35
        MAX = 2 ** (BITS - 1)

        # The input signals

        # The numbers to multiply. a * b and c * d
        a, b, c, d, e, f = create_signals(6, BITS, signed=True)
        # The load signal, max = number of inputs signals + 1
        # A value of 0 will not load anything.
        load = create_signals(1, 2)

        # The output signals

        # The multiplied output signals
        p_ab, p_cd, p_ef = create_signals(3, 2 * BITS, signed=True)
        ab_ready, cd_ready, ef_ready = create_signals(3)

        p_sigs = create_signals(3, 2 * BITS, signed=True)
        p_rdys = create_signals(3)

        # Test bench global clock and reset
        clk, rst = create_clock_reset()

        # Test bench check values
        pipeline1 = []
        pipeline2 = []
        pipeline3 = []

        mult_inst = mult.ThreePortMultiplier35Bit(a, b, c, d, e, f, load,
                                                  clk, rst,
                                                  p_ab, ab_ready,
                                                  p_cd, cd_ready,
                                                  p_ef, ef_ready)

        mult_inst2 = mult.SharedMultiplier([a, c, e], [b, d, f], load, clk, rst,
                                           p_sigs, p_rdys)

        clock_gen = clocker(clk)

        # Loader
        @instance
        def loader():
            i = 0
            while True:
                yield clk.negedge

                if i < 5:
                    load.next = 0
                elif i < 10:
                    load.next = 1
                elif i < 15:
                    load.next = 2
                elif i < 20:
                    load.next = 3

                i += 1
                i %= 20

        def string_mult(a, b):
            return "| {:5.2e} * {:5.2e} = {:5.2e}".format(*map(float, (a, b, a * b)))

        @instance
        def stimulus():
            yield clk.negedge
            rst.next = False

            while True:
                yield clk.negedge
                a.next = randrange(-MAX, MAX)
                b.next = randrange(-MAX, MAX)
                c.next = randrange(-MAX, MAX)
                d.next = randrange(-MAX, MAX)
                e.next = randrange(-MAX, MAX)
                f.next = randrange(-MAX, MAX)

                # check_address, check_a, check_b, check_p = pipeline[int(address_out)]

                print('-' * 20)
                print(load, string_mult(a, b), string_mult(c, d), string_mult(e, f))
                print('-' * 20)
                if ab_ready:
                    print("AB: {:5.2e}".format(float(p_ab)))
                if cd_ready:
                    print("CD: {:5.2e}".format(float(p_cd)))
                if ef_ready:
                    print("EF: {:5.2e}".format(float(p_ef)))
                print('-' * 20)
                if p_rdys[0]:
                    print("AB2: {:5.2e}".format(float(p_sigs[0])))
                if p_rdys[1]:
                    print("CD2: {:5.2e}".format(float(p_sigs[1])))
                if p_rdys[2]:
                    print("EF2: {:5.2e}".format(float(p_sigs[2])))
                print('-' * 20)
                # assert check_address == address_out and check_p == p

                # pipeline[int(address_in)] = int(address_in), int(a), int(b), int(a * b)

        return mult_inst, mult_inst2, clock_gen, loader, stimulus

    run_sim(bench, time_steps, trace)


def test_multiplier35bit(time_steps=20000, trace=False):
    def bench():
        ticks = 5
        BITS = 35
        MAX = 2 ** BITS // 2
        MAXOUT = 2 ** (BITS * 2) // 2

        a, b = create_signals(2, BITS, signed=True)
        pipeA, pipeB = [create_signals(ticks, BITS, signed=True) for _ in range(2)]
        p = create_signals(1, 2 * BITS, signed=True)
        clk, rst = create_signals(2)

        mult_inst = mult.Multiplier35Bit(a, b, p, clk, rst)

        clock_gen = clocker(clk)

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
                    f_a = float(a)
                    f_b = float(b)
                    f_p = float(p)
                    f_pipeA = float(pipeA[pA])
                    f_pipeB = float(pipeB[pB])
                    print("{:5.4f}x{:5.4f} = {:5.4f}".format(
                        f_a/float(MAX), f_b/float(MAX),
                        (f_pipeA * f_pipeB)/float(MAXOUT)) +
                        " but got {:5.4f}, error: {:5.4f}".format(
                            f_p/float(MAXOUT),
                            (f_pipeA * f_pipeB - f_p)/float(MAXOUT)))
                assert p == pipeA[iA] * pipeB[iB], \
                    "Difference: p - a * b = {}".format(
                        bin(p - pipeA[iA] * pipeB[pB], 2 * BITS))

                pA = (pA + 1) % ticks
                pB = (pB + 1) % ticks

        return mult_inst, clock_gen, stimulus

    run_sim(bench, time_steps, trace)


def test_addressable_multiplier(time_steps=20000, trace=False):
    def bench():
        BITS = 35
        MAX = 2 ** BITS // 2

        a, b = create_signals(2, BITS, signed=True)
        p = create_signals(1, 2 * BITS, signed=True)
        clk, rst = create_clock_reset()
        address_in, address_out = create_signals(2, 3, mod=True)
        pipeline = {i: (0, 0, 0, 0) for i in range(len(address_in))}  # Check pipeline

        mult_inst = mult.AddressableMultiplier35Bit(a, b, p, address_in, address_out, clk, rst)

        clock_gen = clocker(clk)

        @instance
        def stimulus():
            yield clk.negedge
            rst.next = False

            while True:
                yield clk.negedge
                a.next = randrange(-MAX, MAX)
                b.next = randrange(-MAX, MAX)
                address_in.next = address_in + 1

                check_address, check_a, check_b, check_p = pipeline[int(address_out)]

                # print('-' * 20)
                # print(address_out, address_in)
                # print('-' * 20)
                # print(pipeline)
                # print('-' * 20)
                assert check_address == address_out and check_p == p

                pipeline[int(address_in)] = int(address_in), int(a), int(b), int(a * b)

        return mult_inst, clock_gen, stimulus

    run_sim(bench, time_steps, trace)


if __name__ == '__main__':
    # test_multiplier35bit()
    # test_addressable_multiplier(20)
    switchable_multiplier(800)
