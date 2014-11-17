#!/usr/bin/env python

__author__ = 'michiel'

import random
import fpga.encoders.biphasemark as biphasemark
from myhdl import Signal, always, instance, delay, StopSimulation, Simulation, traceSignals, intbv
from tests.test_utils import clocker, run_sim


def benchEncoder(tests=1000):

    din, dclk, dout, clock, reset = [Signal(False) for _ in range(5)]
    # formatter = ("|" + " {:^10} |" * 6).format
    # splitter = "+" + ("=" * 12 + "+") * 6

    dut = biphasemark.Encoder(din, dclk, dout, clock, reset)

    clockgen = clocker(clock)

    test_din = []
    test_clock = []
    test_dout = []

    for i in range(tests):
        sample = bool(random.randint(0, 1))
        test_din.append(sample)
        test_din.append(sample)
        test_clock.append(True)
        test_clock.append(False)
        try:
            prev_out = test_dout[(i * 2) - 1]
        except IndexError:
            prev_out = False

        test_dout.append(not prev_out)
        if sample:
            test_dout.append(prev_out)
        else:
            test_dout.append(not prev_out)

    @instance
    def check():
        yield clock.negedge
        reset.next = False

        # print formatter('din', 'dclk', 'dout', 'expect', 'clock', 'reset')
        # print splitter
        for i, c, o in zip(test_din, test_clock, test_dout):
            yield clock.negedge
            din.next = i
            dclk.next = c
            yield clock.negedge
            yield clock.negedge
            yield clock.negedge
            # print formatter(din, dclk, dout, o, clock, reset)

            assert dout == o

        raise StopSimulation

    return dut, clockgen, check

def benchDecoder(tests=1000, data_length=50):

    din, locked, dclk, dout, clock, reset = [Signal(False) for _ in range(6)]
    # formatter = ("|" + " {:^10} |" * 6).format
    # splitter = "+" + ("=" * 12 + "+") * 6

    dut = biphasemark.Decoder(din, locked, dclk, dout, clock, reset)

    clockgen = clocker(clock)

    test_din, test_clock, test_dout = [[] for _ in range(3)]

    for i in range(tests):
        test_din.append([])
        test_clock.append([False])
        test_dout.append([False, False])
        for j in range(data_length):
            sample = bool(random.randint(0, 1))
            test_dout[i].append(sample)
            test_dout[i].append(sample)

            try:
                prev_out = test_din[i][(j * 2) - 1]
            except IndexError:
                prev_out = False

            test_din[i].append(not prev_out)
            if sample:
                test_din[i].append(prev_out)
            else:
                test_din[i].append(not prev_out)

            if test_din[i][0] and test_din[i][1]:
                test_clock[i].append(True)
                test_clock[i].append(False)
            else:
                test_clock[i].append(False)
                test_clock[i].append(True)


        test_clock[i].pop()
        test_dout[i].pop()
        test_dout[i].pop()

    @instance
    def check():
        yield clock.negedge
        reset.next = False

        for j in range(tests):
            for k in range(15):
                yield clock.negedge
                reset.next = k == 0
            # print splitter
            # print formatter('Test', 'nr', j + 1, ' ', ' ', ' ')
            # print splitter
            # print formatter('din', 'locked', 'expclk', 'dclk', 'expout', 'dout')
            # print splitter
            count = 0
            for i, c, o in zip(test_din[j], test_clock[j], test_dout[j]):
                yield clock.negedge
                din.next = i
                for _ in range(j + 5):
                    yield clock.negedge
                # print formatter(din, locked, c, dclk, o, dout)

                if locked:
                    # if dclk != c:
                    #     print formatter('dclk', 'error', 'expect', c, 'got', dclk)
                    assert dclk == c

                    if count > 2:
                        # if dout != o:
                        #     print formatter('dout', 'error', 'expect', o, 'got', dout)
                        assert dout == o, "Dout error: expected %s got %s" % (o, dout)
                    count += 1

                for _ in range(j + 2):
                    yield clock.negedge

        raise StopSimulation

    return dut, clockgen, check

def test_bench(trace=False):
    run_sim((benchEncoder, benchDecoder))

def test_loop():
    def bench(tests=1000, data_length=50):
        din, dclk, encoded, locked, decoded_clk, decoded, clock, reset = [Signal(False) for _ in range(8)]

        encoder = biphasemark.Encoder(din, dclk, encoded, clock, reset)
        decoder = biphasemark.Decoder(encoded, locked, decoded_clk, decoded, clock, reset)

        clockgen = clocker(clock)

        test_din = []
        test_clock = []
        test_encoded = []
        test_decoded = []

        for i in range(tests):
            test_din.append([])
            test_clock.append([])
            test_encoded.append([])
            test_decoded.append([])
            for j in range(data_length):
                sample = bool(random.randint(0, 1))
                test_din[i].append(sample)
                test_din[i].append(sample)
                test_clock[i].append(True)
                test_clock[i].append(False)
                try:
                    prev_out = test_encoded[i][(j * 2) - 1]
                except IndexError:
                    prev_out = False

                test_encoded[i].append(not prev_out)
                if sample:
                    test_encoded[i].append(prev_out)
                else:
                    test_encoded[i].append(not prev_out)

            test_decoded[i] = [False, False] + test_din[i]
            test_decoded[i].pop()
            test_decoded[i].pop()

        @instance
        def check():
            yield clock.negedge
            reset.next = False

            for j in range(tests):
                for k in range(15):
                    yield clock.negedge
                    reset.next = k == 0

                count = 0
                for i, c, e, d in zip(test_din[j], test_clock[j], test_encoded[j], test_decoded[j]):
                    yield clock.negedge
                    din.next = i
                    dclk.next = c
                    for _ in range(5):
                        yield clock.negedge

                    assert e == encoded, "Encoder issue: expected {} got {}".format(e, encoded)
                    if locked:
                        if count > 2:
                            assert d == decoded, "Decoder issue: expected {} got {}".format(d, decoded)
                        else:
                            count += 1

            raise StopSimulation

        return encoder, decoder, clockgen, check

    run_sim(bench)


def test_edge_count():
    def bench():
        M = 256
        N = M - 1
        din, locked, clock, reset = [Signal(False) for _ in range(4)]
        current, prev = [Signal(intbv(0, min=0, max=M)) for _ in range(2)]
        minimum = Signal(intbv(N, min=0, max=M))

        dut = biphasemark.EdgeCounter(din, locked, minimum, current, prev, clock, reset)

        # formatter = ("|" + "{:^8}|" * 5).format
        # splitter = ("+" + "=" * 8) * 5 + "+"

        clockgen = clocker(clock)

        ticks = 5
        half = ticks - 1
        whole = ticks * 2 - 1
        data_in = [
            [False, False, True, True, False, False, True], # 000
            [False, False, True, True, False, True, False], # 001
            [False, False, True, False, True, True, False], # 010
            [False, False, True, False, True, False, True], # 011
            [False, True, False, False, True, True, False], # 100
            [False, True, False, False, True, False, True], # 101
            [False, True, False, True, False, False, True], # 110
            [False, True, False, True, False, True, False], # 111
            [True, True, False, False, True, True, False],  # 000
            [True, True, False, False, True, False, True],  # 001
            [True, True, False, True, False, False, True],  # 010
            [True, True, False, True, False, True, False],  # 011
            [True, False, True, True, False, False, True],  # 100
            [True, False, True, True, False, True, False],  # 101
            [True, False, True, False, True, True, False],  # 110
            [True, False, True, False, True, False, True]   # 111
        ]
        data_out = [
            [
                [False, N, 0, 0],
                [False, N, 0, 0],
                [False, N, 0, 0],             # Here comes the first edge and starts the count
                [False, N, 0, 0],
                [False, whole, whole, 0],       # Second edge and first output values
                [False, whole, whole, 0],
                [False, whole, whole, whole],
            ],
            [
                [False, N, 0, 0],
                [False, N, 0, 0],
                [False, N, 0, 0],             # Here comes the first edge and starts the count
                [False, N, 0, 0],
                [False, whole, whole, 0],     # Second edge and first output values (no lock)
                [True, half, half, whole],      # Third edge, definitely got a one
                [True, half, half, half],
            ],
            [
                [False, 0, 0, 0],
                [False, 0, 0, 0],
                [False, 0, 0, 0],
                [True, ticks, ticks, ticks * 2],
                [True, ticks, ticks, ticks],
                [True, ticks, ticks * 2, ticks],
            ],
        ]

        @instance
        def check():
            yield clock.negedge
            reset.next = False

            for i in range(len(data_in)):
                # print splitter
                # print formatter('din', 'locked', 'min', 'current', 'prev')
                # print splitter
                yield clock.negedge
                reset.next = True
                yield clock.negedge
                reset.next = False
                for j in range(len(data_in[i])):
                    din.next = data_in[i][j]
                    yield clock.negedge
                    yield clock.negedge
                    yield clock.negedge
                    yield clock.negedge
                    yield clock.negedge
                    # print formatter(din, locked, minimum, current, prev)

            raise StopSimulation

        return dut, clockgen, check

    run_sim(bench)


if __name__ == '__main__':
    test_bench()
    test_edge_count()
    test_loop()