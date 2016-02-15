#!/usr/bin/env python

__author__ = 'michiel'

from random import randrange

from myhdl import always, always_comb, instance, StopSimulation  # , always, concat

import fpga.interfaces.aes3 as aes3
from fpga.tests.test_utils import clocker, clockdiv, run_sim  # , int_to_bit_list
from fpga.utils import create_signals  # , binarystring


def test_aes3_transmitter():
    def bench(tests=24 * 64):
        cs1, valid1, user1, cs2, valid2, user2 = create_signals(6)
        audio1, audio2 = create_signals(2, 24, signed=True)
        frame0, ce_word, ce_bit, ce_bp, sdata, clk, rst = create_signals(7)

        transmitter = aes3.AES3_TX(audio1, cs1, valid1, user1, audio2, cs2,
                                   valid2, user2, frame0, ce_word, ce_bit,
                                   ce_bp, sdata, clk, rst, auto_clk=False)

        clk_count = create_signals(1, (0, 512), mod=True)

        clockgen = clocker(clk)

        @always(clk.posedge)
        def counter():
            clk_count.next = clk_count + 1

        @always_comb
        def biphase_clocker():
            if clk_count[1:0] == 0:
                ce_bp.next = 1
            else:
                ce_bp.next = 0

        @always_comb
        def bit_clocker():
            if clk_count[2:0] == 0:
                ce_bit.next = 1
            else:
                ce_bit.next = 0

        @always_comb
        def word_clocker():
            if clk_count == 0:
                ce_word.next = 1
            else:
                ce_word.next = 0

        @instance
        def check():
            had_frame_zero = False
            yield clk.posedge
            rst.next = True
            frame0.next = 0
            yield clk.posedge
            frame0.next = 0
            yield ce_word.posedge

            print('| ce_word | ce_bit  | ce_bp   | frame0  | sdata')
            for i in range(tests):
                rst.next = False
                frame0.next = 0
                if ce_bp:
                    print("| {:>7} | {:>7} | {:>7} | {:>7} | {:>7}".format(
                        ce_word, ce_bit, ce_bp, frame0, sdata))
                if clk_count == 0 and not had_frame_zero:
                    frame0.next = 1
                    had_frame_zero = True

                if ce_word:
                    audio1.next = randrange(audio1.min, audio1.max)
                    audio2.next = randrange(audio2.min, audio2.max)
                yield clk.negedge

            raise StopSimulation

        return transmitter, clockgen, check, counter, biphase_clocker, bit_clocker, word_clocker

    run_sim(bench)

if __name__ == '__main__':
    test_aes3_transmitter()
