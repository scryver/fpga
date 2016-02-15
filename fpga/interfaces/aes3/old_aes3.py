#!/usr/env/python

# http://www.xilinx.com/support/documentation/application_notes/xapp514.pdf

from __future__ import print_function
from myhdl import intbv, always, always_comb, concat
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


def AES3_RX_DEMUXED(din, audio1, valid1, user1, cs1, out_en, audio2, valid2, user2, cs2,
                    parity_error, frames, frame0, locked, clk, rst):
    LCK_BITS = 13
    LCK_MAX = 2 ** LCK_BITS - 1

    recdata, recdata_valid = create_signals(2)
    framer_out = create_signals(1, 8)
    framer_valid = create_signals(1)
    x_preamble, y_preamble, z_preamble = create_signals(3)
    channel1, channel2, valid, user_data, cs = create_signals(5)
    audio, audio1_hold = create_signals(2, 24)
    locked_timeout = create_signals(1, LCK_BITS)
    valid1_hold, user1_hold, cs1_hold = create_signals(3)
    parity_error_int = create_signals(1)
    frames_int = create_signals(1, 8)

    aes_dru = AES_Dru(din, recdata, recdata_valid, clk, rst)
    aes_framer = AES_Framer(recdata, recdata_valid, framer_out, framer_valid,
                            x_preamble, y_preamble, z_preamble, clk,
                            rst)
    aes_rx_formatter = AES_RX_Formatter(framer_out, framer_valid, x_preamble,
                                        y_preamble, z_preamble, channel1,
                                        channel2, audio, valid,
                                        parity_error_int, user_data, cs,
                                        frames_int, clk, rst)

    @always(clk.posedge)
    def lock_timeout_logic():
        if y_preamble and framer_valid:
            locked_timeout.next = 0
        else:
            locked_timeout.next = locked_timeout + 1

    @always(clk.posedge)
    def lock_logic():
        if rst:
            locked.next = False
        else:
            if y_preamble and framer_valid:
                locked.next = True
            elif locked_timeout == LCK_MAX:
                locked.next = False

    @always(clk.posedge)
    def demux_registers():
        if channel1:
            audio1_hold.next = audio
            valid1_hold.next = valid
            user1_hold.next = user_data
            cs1_hold.next = cs

    @always(clk.posedge)
    def output_regs():
        if channel2:
            audio1.next = audio1_hold.signed()
            valid1.next = valid1_hold
            user1.next = user1_hold
            cs1.next = cs1_hold
            audio2.next = audio.signed()
            valid2.next = valid
            user2.next = user_data
            cs2.next = cs
            frames.next = frames_int

            if frames_int == 0:
                frame0.next = True
            else:
                frame0.next = False

    @always(clk.posedge)
    def output_enable_logic():
        out_en.next = channel2

    @always(clk.posedge)
    def parity_error_pass():
        if channel1 or channel2:
            parity_error.next = parity_error_int

    return (aes_dru, aes_framer, aes_rx_formatter, lock_timeout_logic,
            lock_logic, demux_registers, output_regs, output_enable_logic,
            parity_error_pass)


def AES_Dru(din, dout, dout_valid, clk, rst):
    """
    This is the multirate data recovery unit for the AES3 receiver. The DRU uses
    a high speed oversampling circuit. It determines the minimum time between
    transitions in the bitstream and then uses 1/2 the value as the offset from
    the last edge position to sample the bitstream.

    The DRU produces a single recovered bit out whenever data_valid is asserted.

    :param din:         Serial bitstream input
    :param dout:        Recovered serial data out
    :param dout_valid:  Asserted when dout is valid
    :param clk:         4x Oversampling clock
    :param rst:         Synchronous reset
    :return:
    """
    UPDATE_CNTR_WIDTH = 10
    UPDATE_CNTR_MAX = 2 ** UPDATE_CNTR_WIDTH - 1
    MIN_VAL_WIDTH = 10
    MIN_VAL_MAX = 2 ** MIN_VAL_WIDTH - 1

    update_tc = UPDATE_CNTR_MAX         # Terminal count for update_cntr

    inffs = create_signals(1, 3)        # Edge detection FFs
    edge_detect = create_signals(1)     # Edge detection signal
    # clocks between edges, min capture reg, min value hold register
    min_cntr, min_capture, min_hold = create_signals(3, MIN_VAL_WIDTH, mod=True)
    # Update tmin capture & hold regs, symlen_cntr < min_campture
    update_min, new_min = create_signals(2)
    # Update period counter
    update_cntr = create_signals(1, UPDATE_CNTR_WIDTH, mod=True)
    # Finds sample points
    sample_cntr = create_signals(1, MIN_VAL_WIDTH, mod=True)
    sample_now = create_signals(1)      # Sample when asserted

    @always(clk.posedge)
    def ffs():
        """ Input FFs

        A shift register of three FFs is used to sample the incoming bitstream.
        The first and second FF remove metastability from the signal. The
        outputs of the second FF and the third FF are compared to determine
        when an edge occurs.
        """
        inffs.next = concat(inffs[2:], din)

    @always_comb
    def edge_detection():
        edge_detect.next = inffs[2] ^ inffs[1]

    @always(clk.posedge)
    def min_counter():
        """ Min Counter

        The min counter is reset when an edge is detected and increments by 1
        the rest of the time, counting the number of clock cycles between edges.
        """
        if edge_detect:
            min_cntr.next = 0
        else:
            min_cntr.next = min_cntr + 1

    @always(clk.posedge)
    def min_capture_reg():
        """ Minimum Capture Register

        This register loads with a value of all ones when update_min is
        asserted. Otherwise, when edge is asserted, it loads with the value of
        min counter if the min count is less than the current value in the
        register.
        """
        if edge_detect:
            if update_min:
                min_capture.next = MIN_VAL_MAX
            elif new_min:
                min_capture.next = min_cntr

    @always_comb
    def new_minimum():
        new_min.next = True if min_cntr < min_capture else False

    @always(clk.posedge)
    def min_hold_reg():
        """ Minimum Hold Register

        Whenever edge_detect and update_min are both asserted, this register
        loads with the current contents of min_capture register, holding the
        minimum value found while min_capture begins searching for a new minimum
        value.
        """
        if edge_detect and update_min:
            min_hold.next = min_capture

    @always(clk.posedge)
    def update_period_counter():
        """ Update Period Counter

        The update period counter increments by one on every detected edge. When this
        counter reaches its maximum count, update_min is asserted and the counter rolls
        over to zero.
        """
        if edge_detect:
            update_cntr.next = update_cntr + 1

    @always_comb
    def update_minimum():
        update_min.next = True if update_cntr == update_tc else False

    @always(clk.posedge)
    def sample_counter():
        """ Sample Counter

        The sample counter determines when it is time to sample the bitstream output of
        inffs[2]. This counter resets to zero when edge_detect is asserted or when the
        sample count is equal to or greater than the min_hold value. Thus, this counter
        counts from 0 to the min_hold value which is then length of time of one symbol
        (half an encoded bit), then it resets and starts over. The bitstream is sampled
        each time the sample counter reaches one half the min_hold value which is approximately
        the middle of the symbol.
        """
        if edge_detect or sample_cntr >= min_hold:
            sample_cntr.next = 0
        else:
            sample_cntr.next = sample_cntr + 1

    @always_comb
    def sample_it_now():
        sample_now.next = True if sample_cntr == concat(False, min_hold[MIN_VAL_WIDTH:1]) else False

    @always(clk.posedge)
    def output_data():
        if sample_now:
            dout.next = inffs[2]

    @always(clk.posedge)
    def output_valid():
        dout_valid.next = sample_now

    return (ffs, edge_detection, min_counter, min_capture_reg, new_minimum,
            min_hold_reg, update_period_counter, update_minimum, sample_counter,
            sample_it_now, output_data, output_valid)


def AES_Framer(din, din_valid, dout, dout_valid, x_preamble, y_preamble,
               z_preamble, clk, rst):
    """
    This module accepts the serial bit stream from the AES data recovery unit
    with the accompanying data valid bit. It identifies the preamble words and
    uses them to align the data. It does the bi-phase decoding and outputs
    8-bit recovered data words with a data valid bit and X, Y, and Z preamble
    indicators.

    :param din:         Serial input data
    :param din_valid:   Input clock enable
    :param dout:        Decoded output and framed data
    :param dout_valid:  Output data valid
    :param x_preamble:  X preamble detected
    :param y_preamble:  Y preamble detected
    :param z_preamble:  Z preamble detected
    :param clk:         Clock input
    :param rst:         Synchronous reset
    :return:
    """

    in_sr = create_signals(1, 9)
    deser = create_signals(1, 8)
    deser_ce = create_signals(1)
    predet_in = create_signals(1, 8)
    x_detect, y_detect, z_detect, pre_detect = create_signals(4)
    fixed_match, dout_ld, state = create_signals(3)
    bitcntr = create_signals(1, 3, mod=True)
    int_xyz = create_signals(1, 3)

    @always(clk.posedge)
    def input_shift_reg():
        if din_valid:
            in_sr.next = concat(din, in_sr[9:1])

    @always_comb
    def predetect_input():
        predet_in.next = ~ in_sr[9:1] if in_sr[0] else in_sr[9:1]

    @always_comb
    def fixedmatch_input():
        fixed_match.next = predet_in[0] and predet_in[1] and predet_in[2] \
            and not predet_in[3] and not predet_in[7]

    @always_comb
    def preamble_detect():
        x_detect.next = True if fixed_match and predet_in[7:4] == 0b100 \
            else False
        y_detect.next = True if fixed_match and predet_in[7:4] == 0b010 \
            else False
        z_detect.next = True if fixed_match and predet_in[7:4] == 0b001 \
            else False

        pre_detect.next = True if fixed_match and (
            predet_in[7:4] == 0b001 or predet_in[7:4] == 0b010 or
            predet_in[7:4] == 0b100) else False

    @always(clk.posedge)
    def deserialization():
        if deser_ce:
            deser.next = concat((in_sr[1] ^ in_sr[2]), deser[8:1])

    @always(clk.posedge)
    def output_register():
        if dout_ld:
            dout.next = deser

    @always(clk.posedge)
    def framer_state_logic():
        if rst:
            state.next = 0
        else:
            if din_valid:
                if pre_detect:
                    state.next = 0
                else:
                    state.next = not state

    @always(clk.posedge)
    def framer_control_logic():
        if rst:
            bitcntr.next = 0
        else:
            if din_valid:
                if pre_detect:
                    bitcntr.next = 0
                elif deser_ce:
                    bitcntr.next = bitcntr + 1

    @always_comb
    def framer_control_comb():
        deser_ce.next = state and din_valid
        dout_ld.next = True if not state and din_valid and bitcntr == 0b111 \
            else False

    @always(clk.posedge)
    def delay_preamble_reg():
        if rst:
            int_xyz.next = 0
        else:
            if din_valid:
                if pre_detect:
                    int_xyz.next = concat(x_detect, y_detect, z_detect)
                elif bitcntr == 0b111:
                    int_xyz.next = 0

    @always(clk.posedge)
    def delay_preambles():
        if rst:
            x_preamble.next = False
            y_preamble.next = False
            z_preamble.next = False
        else:
            if dout_ld:
                x_preamble.next = int_xyz[2]
                y_preamble.next = int_xyz[1]
                z_preamble.next = int_xyz[0]

    @always(clk.posedge)
    def dout_valid_gen():
        if rst:
            dout_valid.next = False
        else:
            dout_valid.next = dout_ld

    return (input_shift_reg, predetect_input, fixedmatch_input, preamble_detect,
            deserialization, output_register, framer_state_logic,
            framer_control_logic, framer_control_comb, delay_preamble_reg,
            delay_preambles, dout_valid_gen)


def AES_RX_Formatter(din, din_valid, x_preamble, y_preamble, z_preamble,
                     channel1, channel2, audio, valid, parity_error, user,
                     cs, frames, clk, rst):

    in_reg = create_signals(1, 28)
    sub = create_signals(1)
    byte_count = create_signals(1, 4)
    preamble_in = create_signals(1)
    ce, ld_out = create_signals(2)
    frames_int = create_signals(1, 8, mod=True)

    @always_comb
    def preambled():
        preamble_in.next = x_preamble or y_preamble or z_preamble

    @always(clk.posedge)
    def byte_counter():
        if din_valid:
            if preamble_in:
                byte_count.next = 1
            else:
                byte_count.next = concat(byte_count[3:], False)

    @always(clk.posedge)
    def input_register():
        if din_valid:
            inreg_tmp = intbv(0)[28:]
            inreg_tmp[:] = in_reg
            if preamble_in:
                inreg_tmp[4:] = din[8:4]
            elif byte_count[0] == 1:
                inreg_tmp[12:4] = din
            elif byte_count[1] == 1:
                inreg_tmp[20:12] = din
            elif byte_count[2] == 1:
                inreg_tmp[28:20] = din
            in_reg.next = inreg_tmp

    @always(clk.posedge)
    def subframe_tracker():
        if din_valid:
            if y_preamble:
                sub.next = 1
            elif x_preamble or z_preamble:
                sub.next = 0

    @always(clk.posedge)
    def frame_counter():
        if din_valid:
            if z_preamble:
                frames_int.next = 0
            elif x_preamble:
                frames_int.next = frames_int + 1

    @always_comb
    def frame_comb():
        frames.next = frames_int

    @always(clk.posedge)
    def output_clk():
        ce.next = din_valid

    @always_comb
    def output_clk_enable():
        ld_out.next = ce and byte_count[3]

    @always(clk.posedge)
    def audio_output():
        if ld_out:
            audio.next = in_reg[24:]

    @always(clk.posedge)
    def channel_indicator():
        channel1.next = ld_out and not sub
        channel2.next = ld_out and sub

    @always(clk.posedge)
    def valid_data():
        if ld_out:
            valid.next = in_reg[24]

    @always(clk.posedge)
    def user_data():
        if ld_out:
            user.next = in_reg[25]

    @always(clk.posedge)
    def channel_status():
        if ld_out:
            cs.next = in_reg[26]

    @always(clk.posedge)
    def parity_error_detection():
        if ld_out:
            p = in_reg[0]
            for i in range(len(in_reg) - 1):
                p ^= in_reg[i + 1]
            parity_error.next = p

    return (preambled, byte_counter, input_register, subframe_tracker,
            frame_counter, frame_comb, output_clk, audio_output,
            channel_indicator, valid_data, user_data, channel_status,
            parity_error_detection, output_clk_enable)
