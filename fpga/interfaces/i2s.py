#!/usr/bin/env python

__author__ = 'michiel'

import fpga.basics.flipflops as ff

from myhdl import intbv, always, always_comb, concat
from fpga.utils import create_signals


def WordSelect(ws, wsd, nwsd, wsp, sclk):
    """

    :param ws:      Word Select input
    :param wsd:     Clocked word select
    :param nwsd:    Clocked inverted word select
    :param wsp:     Word Select pulse indicating a change in word select
    :param sclk:
    :return:
    """

    wsdd = create_signals(1)

    @always(sclk.posedge)
    def logic():
        wsd.next = ws
        nwsd.next = not ws

        wsdd.next = wsd

    @always_comb
    def out_logic():
        wsp.next = wsd ^ wsdd

    return logic, out_logic


def ShiftRegister(parallel_in, d, load, sdata, sclk, reset):

    buf = create_signals(1, (parallel_in.min, parallel_in.max))
    M = len(parallel_in)

    if parallel_in.min < 0:
        @always(sclk.negedge)
        def logic():
            if reset:
                buf.next = 0
            elif load:
                buf.next = parallel_in
            else:
                buf.next = concat(buf[M - 1:0], d).signed()
    else:
        @always(sclk.negedge)
        def logic():
            if reset:
                buf.next = 0
            elif load:
                buf.next = parallel_in
            else:
                buf.next = concat(buf[M - 1:0], d)

    @always_comb
    def output_logic():
        sdata.next = buf[M - 1]

    return logic, output_logic


def DataBuffer(parallel_in, load, wait, output_enable, dout, sclk, reset):

    buf = create_signals(1, (parallel_in.min, parallel_in.max))

    @always(sclk.posedge)
    def logic():
        if reset:
            buf.next = 0
        elif (load and not wait and not output_enable):
            buf.next = parallel_in

    @always_comb
    def output_logic():
        if output_enable:
            dout.next = buf
        else:
            dout.next = 0

    return logic, output_logic


def Serial2Parallel(sdata, start, dout, sclk):

    M = len(dout)
    assert M > 2
    buf = create_signals(M)
    en = create_signals(M - 1)

    shift_msb = ff.dff_set(en[M - 2], False, start, sclk)
    buf_msb = ff.dffe(buf[M - 1], sdata, start, sclk)

    shifts = [ff.dff_reset(en[M - 3 - i], en[M - 2 - i], sclk, start)
              for i in range(M - 2)]
    bufs = [ff.dffe_rst(buf[M - 2 - i], sdata, en[M - 2 - i], sclk, start)
            for i in range(M - 1)]

    if dout.min < 0:
        @always(sclk.posedge)
        def logic():
            if start:
                t = intbv(0, _nrbits=M)
                for i in range(M):
                    t[i] = buf[i]
                dout.next = t.signed()
    else:
        @always(sclk.posedge)
        def logic():
            if start:
                t = intbv(0, _nrbits=M)
                for i in range(M):
                    t[i] = buf[i]
                dout.next = t

    return shift_msb, shifts, buf_msb, bufs, logic


def I2S_Transmitter(left, right, load_left, load_right, sdata, ws, sclk, reset):
    """
    I2S Transmitter. Left and right data is multiplexed by ws. Ws= 0 means left.
    Sdata will be changed on negedge of sclk.

    :param left:        Left Data parallel input
    :param right:       Right Data parallel input
    :param load_left:   Load left data
    :param load_right:  Load right data
    :param sdata:       Serial data output
    :param ws:          Word clock output
    :param sclk:        Clock input
    :param reset:       Reset input
    :return:
    """
    left_buf, right_buf, left_right = create_signals(3, (left.min, left.max))
    wsd, nwsd, wsp = create_signals(3)

    left_buffer = DataBuffer(left, load_left, wsp, nwsd, left_buf, sclk, reset)
    right_buffer = DataBuffer(right, load_right, wsp, wsd, right_buf, sclk,
                              reset)
    ws_select = WordSelect(ws, wsd, nwsd, wsp, sclk)
    shifter = ShiftRegister(left_right, False, wsp, sdata, sclk, reset)

    @always_comb
    def buffed_or():
        left_right.next = left_buf | right_buf

    return left_buffer, right_buffer, ws_select, shifter, buffed_or


def I2S_Receiver(sdata, ws, left, right, left_ready, right_ready, sclk, reset):

    buf = create_signals(1, (left.min, left.max))

    wsd, nwsd, wsp = create_signals(3)
    ws_select = WordSelect(ws, wsd, nwsd, wsp, sclk)

    s2p = Serial2Parallel(sdata, wsp, buf, sclk)

    @always(sclk.posedge)
    def clocked_logic():
        if reset:
            left.next = 0
            right.next = 0
        else:
            if nwsd and wsp:
                left.next = buf
            elif wsd and wsp:
                right.next = buf

    @always_comb
    def logic():
        left_ready.next = not (nwsd and wsp)
        right_ready.next = not (wsd and wsp)

    return ws_select, s2p, clocked_logic, logic
