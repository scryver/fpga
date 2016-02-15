#!/usr/bin/env python
from __future__ import print_function

from fpga.utils import create_signals

__author__ = 'michiel'

import math
import random
import fpga.utils as utils
from myhdl import always, instance, delay, StopSimulation, Simulation, traceSignals, bin


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


def run_sim(bench, time_steps=None, trace=False, **kwargs):
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
            b.append(benches[i](**kwargs))

    if M == 1:
        s = Simulation(b[0])
    else:
        s = Simulation(tuple(b))
    s.run(time_steps)


def benchEdgeDetect(tests=100):

    din, p_edge, n_edge, clock, reset = create_signals(5)

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


def int_to_bit_list(number, bits=8, signed=None):
    if signed:
        assert -2 ** (bits - 1) <= number < 2 ** (bits - 1), \
            "Number {} not in range({}, {})".format(number, -2 ** (bits - 1),
                                                    2 ** (bits - 1))
        if number < 0:
            bit_list = [1]
            number = -(number + 1)
        else:
            bit_list = [0]
    else:
        assert 0 <= number < 2 ** bits, \
            "Number {} not in range({}, {})".format(number, 0, 2 ** bits)
        bit, number = divmod(number, 2 ** (bits - 1))
        bit_list = [bit]

    for i in range(bits - 2, -1, -1):
        bit, number = divmod(number, 2 ** i)
        bit_list.append(bit if not (signed and bit_list[0] == 1)
                        else int(not bit))

    return bit_list


def generate_external_clock(clk, frequency=44100, samples_per_sec=500000000.):
    if samples_per_sec >= 1000000000:
        suffix = "GHz"
        sps = samples_per_sec / 1000000000.
        tsuf = "psec"
    elif samples_per_sec >= 1000000:
        suffix = "MHz"
        sps = samples_per_sec / 1000000.
        tsuf = "nsec"
    elif samples_per_sec >= 1000:
        suffix = "kHz"
        sps = samples_per_sec / 1000.
        tsuf = "usec"
    else:
        suffix = "Hz"
        sps = samples_per_sec / 1.
        tsuf = "msec"
    tpc = 1000. / sps
    half_time = 1.0 / frequency * samples_per_sec  # nsec
    half_cycle = int(round(half_time))
    error = half_time - half_cycle
    print("Creating external clock with frequency {} @ {:6.2f} {}".format(frequency, sps, suffix))
    print("One clock cycle takes {:6.2f} {}".format(tpc, tsuf))
    print("Error: {}".format(error))

    @always(delay(half_cycle))
    def clock_generator():
        clk.next = not clk

    return clock_generator


def test_external_clocks(steps=211680, master_clk=21168000):
    def bench_clks(steps, master_clk):
        clk44, clk48, prev44, prev48 = create_signals(4)

        gen44 = generate_external_clock(clk44, 44100, master_clk)
        gen48 = generate_external_clock(clk48, 48000, master_clk)

        @instance
        def check_times():
            cnt44, cnt48 = 0, 0
            prev44.next = clk44
            prev48.next = clk48
            yield delay(1)

            for i in range(steps + 2):
                if prev44 != clk44 and clk44:
                    cnt44 += 1
                if prev48 != clk48 and clk48:
                    cnt48 += 1
                prev44.next = clk44
                prev48.next = clk48
                yield delay(1)

            print(cnt44, cnt48)
            raise StopSimulation

        return check_times, gen44, gen48

    run_sim(bench_clks, steps=steps, master_clk=master_clk)


if __name__ == '__main__':
    # test_bench()
    # print(int_to_bit_list(-8, 4, signed=True))
    # print(int_to_bit_list(7, 4))
    # print(int_to_bit_list(8, 4))
    # print(bin(7, 4))
    # print(bin(-8))
    # test_external_clocks(500000000, 500000000.)

    # PAGE 430

    def generate_aes(frequency, fs=44100):
        i = 0
        prev = 0

        def channel_status():
            csbit = 0
            while True:
                if csbit == 0:
                    yield 1         # 1 = AES/EBU, 0 = S/PDIF
                elif csbit == 4:
                    yield 1         # Preemphasis = None
                else:
                    yield 0
                csbit += 1
                csbit %= 192

        def user_data():
            while True:
                yield 0

        def valid_data():
            while True:
                yield 0

        def preamble_x(prev=0):
            yield 0 if prev else 1
            yield 1 if prev else 0
            for i in range(3):
                yield 0 if prev else 1
            for i in range(3):
                yield 1 if prev else 0

        def preamble_y(prev=0):
            for i in range(2):
                yield 0 if prev else 1
            yield 1 if prev else 0
            for i in range(2):
                yield 0 if prev else 1
            for i in range(3):
                yield 1 if prev else 0

        def preamble_z(prev=0):
            for i in range(3):
                yield 0 if prev else 1
            yield 1 if prev else 0
            yield 0 if prev else 1
            for i in range(3):
                yield 1 if prev else 0

        def biphase_mark(sample, prev):
            bit = int(not prev)
            yield bit
            if int(sample):
                yield int(not bit)
            else:
                yield bit

        block = 0
        chan_gen = channel_status()
        user_gen = user_data()
        valid_gen = valid_data()
        while True:
            for frame in range(192):
                i += 1.
                cs = next(chan_gen)
                ud = next(user_gen)
                vd = next(valid_gen)
                for subframe in range(2):
                    if frame == subframe == 0:
                        for z in preamble_z(prev):
                            yield z
                        prev = z
                    elif subframe == 0:
                        for x in preamble_x(prev):
                            yield x
                        prev = x
                    else:
                        for y in preamble_y(prev):
                            yield y
                        prev = y
                    channel = math.sin(math.pi * 2. * i * frequency / float(fs))
                    channel = bin(int(round(channel * 2 ** 23)), 24)

                    parity_list = []
                    for time_slot in range(28):  # 32 - preamble bits
                        if time_slot < 24:
                            parity_list.append(channel[time_slot])
                            for k in biphase_mark(channel[time_slot], prev):
                                yield k
                            prev = k
                        elif time_slot == 24:
                            parity_list.append(cs)
                            for k in biphase_mark(cs, prev):
                                yield k
                            prev = k
                        elif time_slot == 25:
                            parity_list.append(ud)
                            for k in biphase_mark(ud, prev):
                                yield k
                            prev = k
                        elif time_slot == 26:
                            parity_list.append(vd)
                            for k in biphase_mark(vd, prev):
                                yield k
                            prev = k
                        else:
                            ones = 0
                            for p in range(len(parity_list)):
                                if int(parity_list[p]):
                                    ones += 1
                            if ones % 2 == 0:
                                par = 0
                            else:
                                par = 1
                            for k in biphase_mark(par, prev):
                                yield k
                            prev = k

            block += 1

    aes = generate_aes(100)

    for i in range(200):
        preamble = [next(aes) for j in range(64)]

        if i % 2 == 0:
            print(''.join(map(str, preamble)))

        ones = 0
        for x in preamble:
            if int(x):
                ones += 1

        # Assertion to check for 0-DC offset
        assert len(preamble) - ones == ones, \
            "{} zeros, {} ones (should be equal)".format(len(preamble) - ones,
                                                         ones)
