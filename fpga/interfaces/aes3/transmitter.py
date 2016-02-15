#!/usr/env/python

# http://www.xilinx.com/support/documentation/application_notes/xapp514.pdf

from myhdl import always, always_comb, concat
from fpga.utils import create_signals

__author__ = 'michiel'


def AES3_TX(audio_ch1, cs1, valid1, user1, audio_ch2, cs2, valid2, user2,
            frame0, ce_word, ce_bit, ce_bp, sdata, clk, rst, auto_clk=True):
    """
    :param audio_ch1: 24 bit input signal (:mod:`myhdl`.Signal)
    :param cs1: AES channel data bit
    :param valid1: AES valid data bit
    :param user1: AES user data bit
    :param audio_ch2: 24 bit input signal (:mod:`myhdl`.Signal)
    :param cs2: AES channel data bit
    :param valid2: AES valid data bit
    :param user2: AES user data bit
    :param frame0: Flag to indicate AES frame 0                 | Once every 192 frames
    :param ce_word: Word clock enable       @   1Fs             | Output if auto_clk = True. cs, user and valid bit are loaded when high
    :param ce_bit: Bit clock enable         @  64Fs             | Output if auto_clk = True
    :param ce_bp: Biphase clock enable      @ 128Fs (2x ce_bit) | Output if auto_clk = True
    :param sdata: Serial AES data
    :param clk: Master clock                @ 512Fs
    """
    frame0_reg, last_state = create_signals(2)
    inreg1, inreg2 = create_signals(2, 27)
    sr = create_signals(1, 28)
    parity1, parity2 = create_signals(2)
    out_xz, out_y, out_ch1, out_ch2 = create_signals(4)
    set_out_xz, set_out_y, set_out_ch1, set_out_ch2 = create_signals(4)
    seq = create_signals(1, 37)
    pre_sr = create_signals(1, 8)

    dout, b0, b1, txd, state = create_signals(5)

    if auto_clk:
        clkenable_gens = AES_TX_ClockDivider(clk, ce_bp, ce_bit, ce_word)

    PRE_X = 0b01000111
    PRE_Y = 0b00100111
    PRE_Z = 0b00010111
    PRE_X_INV = 0b10111000
    PRE_Y_INV = 0b11011000
    PRE_Z_INV = 0b11101000

    @always(clk.posedge)
    def state_logic():
        if rst:
            state.next = False
        elif ce_bp:
            state.next = ce_bit

    @always(clk.posedge)
    def input_reg():
        if ce_word:
            inreg1.next = concat(cs1, user1, valid1, audio_ch1)
            inreg2.next = concat(cs2, user2, valid2, audio_ch2)
            frame0_reg.next = frame0

    @always(clk.posedge)
    def audio_shift_reg():
        if ce_bit:
            if seq[1]:
                sr.next = concat(parity1, inreg1)
            elif seq[33]:
                sr.next = concat(parity2, inreg2)
            elif out_ch1 or out_ch2:
                sr.next = concat(False, sr[28:1])

    @always_comb
    def parity_gen():
        p1 = inreg1[0]
        p2 = inreg2[0]
        for i in range(len(inreg1) - 1):
            p1 ^= inreg1[i + 1]
            p2 ^= inreg2[i + 1]
        parity1.next = p1
        parity2.next = p2

    @always(clk.posedge)
    def sequencer():
        if ce_bit:
            seq.next = concat(seq[36:], ce_word)

    @always(clk.posedge)
    def output_setter():
        if ce_bit:
            set_out_xz.next = False
            set_out_y.next = False
            set_out_ch1.next = False
            set_out_ch2.next = False

            if seq[0]:
                set_out_xz.next = True
            if seq[4]:
                set_out_ch1.next = True
            if seq[32]:
                set_out_y.next = True
            if seq[36]:
                set_out_ch2.next = True

    @always(clk.posedge)
    def output_xz():
        if rst:
            out_xz.next = False
        else:
            if ce_bit:
                if set_out_xz:
                    out_xz.next = True
                elif set_out_ch1:
                    out_xz.next = False

    @always(clk.posedge)
    def output_ch1():
        if rst:
            out_ch1.next = False
        else:
            if ce_bit:
                if set_out_ch1:
                    out_ch1.next = True
                elif set_out_y:
                    out_ch1.next = False

    @always(clk.posedge)
    def output_y():
        if rst:
            out_y.next = False
        else:
            if ce_bit:
                if set_out_y:
                    out_y.next = True
                elif set_out_ch2:
                    out_y.next = False

    @always(clk.posedge)
    def output_ch2():
        if rst:
            out_ch2.next = False
        else:
            if ce_bit:
                if set_out_ch2:
                    out_ch2.next = True
                elif set_out_xz:
                    out_ch2.next = False

    @always(clk.posedge)
    def preamble_logic():
        if ce_bp:
            if seq[1] and ce_bit:
                if frame0_reg:
                    if b1:
                        pre_sr.next = PRE_Z_INV
                    else:
                        pre_sr.next = PRE_Z
                else:
                    if b1:
                        pre_sr.next = PRE_X_INV
                    else:
                        pre_sr.next = PRE_X
            elif seq[33] and ce_bit:
                if b1:
                    pre_sr.next = PRE_Y_INV
                else:
                    pre_sr.next = PRE_Y
            else:
                pre_sr.next = concat(False, pre_sr[8:1])

    @always_comb
    def output_mux():
        dout.next = pre_sr[0] if out_xz or out_y else sr[0]
        txd.next = b0 if state else b1

    @always_comb
    def biphase_comb_logic_0():
        b0.next = dout if out_xz or out_y else not last_state

    @always_comb
    def biphase_comb_logic_1():
        b1.next = dout if out_xz or out_y else b0 ^ dout

    @always(clk.posedge)
    def last_state_logic():
        if ce_bit:
            last_state.next = b1

    @always(clk.posedge)
    def sdata_logic():
        if ce_bp:
            sdata.next = txd

    functions = [state_logic, input_reg, audio_shift_reg, parity_gen, sequencer,
                 output_setter, output_ch1, output_ch2, output_xz, output_y,
                 preamble_logic, output_mux, biphase_comb_logic_0,
                 biphase_comb_logic_1, last_state_logic, sdata_logic]

    if auto_clk:
        functions.append(clkenable_gens)

    return tuple(functions)


def AES_TX_ClockDivider(clk, biphase_enable, bit_enable, word_enable):
    clken_count = create_signals(1, 9, mod=True)

    @always(clk.posedge)
    def counting():
        clken_count.next = clken_count + 1

    @always_comb
    def biphase_clocker():
        if clken_count[1:0] == 0:
            biphase_enable.next = 1
        else:
            biphase_enable.next = 0

    @always_comb
    def bit_clocker():
        if clken_count[2:0] == 0:
            bit_enable.next = 1
        else:
            bit_enable.next = 0

    @always_comb
    def word_clocker():
        if clken_count == 0:
            word_enable.next = 1
        else:
            word_enable.next = 0

    return counting, biphase_clocker, bit_clocker, word_clocker
