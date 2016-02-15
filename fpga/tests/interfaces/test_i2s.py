#!/usr/bin/env python

__author__ = 'michiel'

from random import randrange

from myhdl import Signal, intbv, instance, StopSimulation, always, concat

import fpga.interfaces.i2s as i2s
from fpga.tests.test_utils import clocker, clockdiv, run_sim, int_to_bit_list
from fpga.utils import create_signals


def test_word_select():
    def bench():
        ws, wsd, nwsd, wsp, clk = create_signals(5)

        wordsel = i2s.WordSelect(ws, wsd, nwsd, wsp, clk)

        testData = [
            [False, False, True, False],
            [True, True, False, True],
            [True, True, False, False],
            [True, True, False, False],
            [True, True, False, False],
            [False, False, True, True],
            [False, False, True, False],
            [False, False, True, False]
        ]

        clockgen = clocker(clk)

        @instance
        def stimulus():
            yield clk.negedge

            for x in range(50):
                for w, wd, nwd, wp in testData:
                    ws.next = w
                    yield clk.negedge
                    # print "ws: {ws}, wsd: {wsd} (exp: {wd}), wsp: {wsp} (exp: {wp})".format(
                    #     ws=ws, wsd=wsd, wd=wd, wsp=wsp, wp=wp
                    # )
                    assert wd == wsd
                    assert nwd == nwsd == (not wsd)
                    assert wp == wsp

            raise StopSimulation

        return wordsel, clockgen, stimulus

    run_sim(bench)


def test_shift_reg():
    def bench():
        M = 16

        d, load, sdata, sclk, reset = create_signals(5)
        p_in = create_signals(1, (0, M))

        shifter = i2s.ShiftRegister(p_in, d, load, sdata, sclk, reset)

        clockgen = clocker(sclk)

        testData = []
        pl = len(p_in)
        p = intbv(0, min=0, max=M)
        for i in range(M):
            p[:] = i
            testData.append((p[:], False, True, p[pl - 1]))

            for j in range(pl - 1):
                testData.append((p[:], False, False, p[pl - 2 - j]))

        @instance
        def stimulus():
            yield sclk.posedge
            reset.next = False
            yield sclk.posedge

            for p, din, l, sd in testData:
                p_in.next = p
                d.next = din
                load.next = l
                yield sclk.posedge
                assert sd == sdata

            raise StopSimulation

        return shifter, clockgen, stimulus

    run_sim(bench)


def test_transmitter():
    def bench(tests=1000, bus_width=24):
        assert bus_width > 2
        bus_width = 24
        load_left, load_right, sdata, ws, sclk, reset = create_signals(6)
        left, right = create_signals(2, bus_width, signed=True)

        transmitter = i2s.I2S_Transmitter(left, right, load_left, load_right,
                                          sdata, ws, sclk, reset)

        clockgen = clocker(sclk)

        ws_count = create_signals(1, (0, bus_width))
        ws_gen = clockdiv(sclk.negedge, ws, ws_count, bus_width)

        MAX = 2 ** (bus_width - 1)

        @always(sclk.negedge)
        def left_right_gen():
            if ws_count == 0 and not ws:
                right.next = randrange(-MAX, MAX)
                load_right.next = True
                load_left.next = False
            elif ws_count == 0 and ws:
                left.next = randrange(-MAX, MAX)
                load_left.next = True
                load_right.next = False

        @instance
        def check():
            yield sclk.posedge
            reset.next = False

            for i in range(tests):
                yield sclk.posedge
                if ws_count == 0:
                    # We start a new ws round but we still need to get the LSB
                    # of the previous data stream
                    if ws:
                        assert left[0] == sdata
                    else:
                        assert right[0] == sdata
                else:
                    if ws:
                        assert right[bus_width - ws_count] == sdata
                    else:
                        assert left[bus_width - ws_count] == sdata

            raise StopSimulation

        return transmitter, clockgen, ws_gen, left_right_gen, check

    run_sim(bench)


def test_serial_to_parallel():
    def bench(bus_width=4):
        assert bus_width > 2
        sdata, start, sclk = create_signals(3)
        dout = create_signals(1, bus_width, signed=True)

        s2p = i2s.Serial2Parallel(sdata, start, dout, sclk)

        output_data = [randrange(-2 ** (bus_width - 1), 2 ** (bus_width - 1))
                       for _ in range(20)]

        input_data = [int_to_bit_list(output_data[i], bus_width, signed=True)
                      for i in range(len(output_data))]

        clockgen = clocker(sclk)

        start_count = create_signals(1, (0, bus_width * 2))
        start_gen = clockdiv(sclk.negedge, start, start_count,
                             bus_width * 2 - 2, True)

        @instance
        def stimulus():
            for i in range(len(input_data)):
                for j in range(len(input_data[i])):
                    yield sclk.negedge
                    sdata.next = input_data[i][j]
                    if j == 0:
                        yield start.posedge

            raise StopSimulation

        @instance
        def check():
            # printstr = "{{start_count:>{busw}}} | {{sdata:>{busw}}} | {{dout:>{busw}}}"
            # printstr = printstr.format(busw=bus_width).format
            # print(printstr(start_count="sc", sdata="sd", dout="ou"))
            yield sclk.negedge

            i = 0
            for _ in range(50):
                # print(printstr(start_count=start_count, sdata=int(sdata),
                #                dout=binarystring(dout, prefix=None)))
                if start_count == 0:
                    if i > 1:
                        # i == 0 is the first load, data is ready at i == 2
                        assert dout == output_data[i - 2]
                    i += 1

                yield sclk.negedge

            raise StopSimulation    # No asserts yet

        return s2p, clockgen, start_gen, stimulus, check

    run_sim(bench)


def test_loop_transmit_receive():
    def bench(tests=1000):
        M = 6
        load_left, load_right, left_ready, right_ready, sdata, ws, sclk, reset = create_signals(8)
        left, right, left_out, right_out, left_check, right_check = [Signal(intbv(0,_nrbits=M)) for _ in range(6)]

        transmitter = i2s.I2S_Transmitter(left, right, load_left, load_right, sdata, ws, sclk, reset)
        receiver = i2s.I2S_Receiver(sdata, ws, left_out, right_out, left_ready, right_ready, sclk, reset)

        clockgen = clocker(sclk)

        ws_count = Signal(intbv(0, min=0, max=M))
        ws_gen = clockdiv(sclk.negedge, ws, ws_count, M)

        @always(sclk.negedge)
        def left_right_gen():
            if ws_count == 0 and not ws:
                right_check.next = right
                right.next = randrange(2 ** M)
                load_right.next = True
                load_left.next = False
            elif ws_count == 0 and ws:
                left_check.next = left
                left.next = randrange(2 ** M)
                load_left.next = True
                load_right.next = False

        @instance
        def check():
            prev_left = True
            prev_right = True
            yield sclk.posedge
            reset.next = False

            for i in range(tests):
            # while True:
                yield sclk.posedge
                if ws_count == 0:
                    # We start a new ws round but we still need to get the LSB of the previous data stream
                    if ws:
                        assert left[0] == sdata
                    else:
                        assert right[0] == sdata
                else:
                    if ws:
                        assert right[M - ws_count] == sdata
                    else:
                        assert left[M - ws_count] == sdata

                if left_ready ^ prev_left:
                    assert left_out == left_check
                if right_ready ^ prev_right:
                    assert right_out == right_check

                prev_left = left_ready
                prev_right = right_ready

            raise StopSimulation

        return transmitter, receiver, clockgen, ws_gen, left_right_gen, check

    run_sim(bench)


def test_loop_receive_transmit():
    def bench(tests=1000):
        M = 6
        clock_delay = 4 * M

        left_ready, right_ready, sdata, sdata_out, ws, sclk, reset = create_signals(7)
        left, right = [Signal(intbv(0, _nrbits=M)) for _ in range(2)]
        sdata_pipe = Signal(intbv(0, _nrbits=clock_delay))

        transmitter = i2s.I2S_Transmitter(left, right, left_ready, right_ready, sdata_out, ws, sclk, reset)
        receiver = i2s.I2S_Receiver(sdata, ws, left, right, left_ready, right_ready, sclk, reset)

        clockgen = clocker(sclk)

        ws_count = Signal(intbv(0, min=0, max=M))
        ws_gen = clockdiv(sclk.negedge, ws, ws_count, M)

        @always(sclk.negedge)
        def data_gen():
            sdata.next = randrange(2)
            sdata_pipe.next = concat(sdata, sdata_pipe[clock_delay:1])

        @instance
        def check():
            check_counter = 0
            yield sclk.posedge
            reset.next = False

            for i in range(tests):
            # while True:
                yield sclk.posedge

                if check_counter <= 6 * M:
                    check_counter += 1
                else:
                    assert sdata_pipe[0] == sdata_out

            raise StopSimulation

        return transmitter, receiver, clockgen, ws_gen, data_gen, check

    run_sim(bench)


if __name__ == '__main__':
    test_word_select()
    test_shift_reg()
    test_transmitter()
    test_serial_to_parallel()
    test_loop_transmit_receive()
    test_loop_receive_transmit()
