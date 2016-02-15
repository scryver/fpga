from __future__ import print_function

import myhdl

from fpga.tests.test_utils import clocker, clockdiv, run_sim  # , int_to_bit_list
from fpga.utils import create_signals


def AES_CRC_Checker(din, frames, ce, clk, crc_err):
    """AES CRC Checker

    :param din:     input, Serial input data
    :param frames:  input, Frame counter (0 - 192)
    :param ce:      input, Clock enable @ Fs, word clock
    :param clk:     input, Clock
    :param crc_err: output, CRC Error flag
    """
    pass


def AES_CRC_Generator(din, frames, ce, clk, dout):
    """AES CRC Generator

    During bytes 0 through 22 the din is passed through to dout. But during
    byte 23, the calculated CRC bits are output on dout.
    (Generator polynomial is x^8+x^4+x^3+x^2+1, preset to 1.)

    :param din:     input, Serial input data
    :param frames:  input, Frame counter (0 - 192)
    :param ce:      input, Clock enable @ Fs, word clock
    :param clk:     input, Clock
    :param crc_err: output, CRC Error flag
    """
    pass


def check_crc_stream2(serin, serout, clk, crc_poly, frame_counter,
                      bits_per_frame=None):
    """
    Generate stream of data, from 0 till bits_per_frame - crc_poly._nrbits - 1
    it is equal to the input, after that it is the remainder of the crc check.

    In frames == 0 to frames == len(crc_poly) output crc_err value.

    if bits_per_frame = None use frame_counter.max
    bits_per_frame = total nr bits per frame, bits_per_frame - len(crc_poly) - 1 = data_length
    """
    lc = len(crc_poly)

    inp_buf = create_signals(0, lc)
    out_buf = create_signals(0, lc)

    @myhdl.always(clk.posedge)
    def buf_input():
        if frame_counter < bits_per_frame - (lc - 1) and inp_buf[lc - 1] == 1:
            out_buf.next = inp_buf ^ crc_poly
        else:
            out_buf.next = inp_buf

        if frame_counter < bits_per_frame - (lc - 1):
            inp_buf.next = myhdl.concat(out_buf[lc - 1:], serin)
        elif frame_counter == 0:
            inp_buf.next = 0
        else:
            inp_buf.next = out_buf[lc - 1:] << 1

    @myhdl.always_comb
    def output_logic():
        if frame_counter >= bits_per_frame - (lc - 1):
            serout.next = out_buf[lc - 2]
        else:
            serout.next = bool(serin)

    return buf_input, output_logic


def check_crc_stream(serin, clk, crc_poly, dout):
    lc = len(crc_poly)

    inp_buf = myhdl.Signal(myhdl.intbv(0, _nrbits=lc))
    out_buf = myhdl.Signal(myhdl.intbv(0, _nrbits=lc))

    @myhdl.always(clk.posedge)
    def buf_input():
        if inp_buf[lc - 1] == 1:
            out_buf.next = inp_buf ^ crc_poly
        else:
            out_buf.next = inp_buf
        inp_buf.next = myhdl.concat(out_buf[lc - 1:], serin)
        # print(myhdl.bin(inp_buf, lc))
        # print(myhdl.bin(out_buf, lc))

    @myhdl.always_comb
    def output_logic():
        dout.next = out_buf[lc - 1:]

    return buf_input, output_logic


def check_crc(din, crc_poly, remainder=None):
    lc = len(crc_poly) - 1
    ld = len(din)
    b = myhdl.intbv(0, _nrbits=ld + lc)
    # print(myhdl.bin(b, b._nrbits))
    b[b._nrbits:b._nrbits - ld] = din
    if remainder is not None:
        b[lc:] = remainder
    # print(myhdl.bin(b, b._nrbits))
    for i in range(ld - 1, -1, -1):
        if b[i + lc] == 0:
            continue
        b[i + lc + 1:i] ^= crc_poly
        # print(myhdl.bin(b, b._nrbits))

    dout = myhdl.intbv(0, _nrbits=ld)
    dcrc = myhdl.intbv(0, _nrbits=lc)
    dout[:] = b[:lc + 1]
    dcrc[:] = b[lc:]
    if remainder is not None:
        assert b == 0, "CRC not valid!"
    return dout, dcrc


def test_check_crc():
    x = myhdl.intbv(0, _nrbits=22 * 8)
    x[:] = 0xAAAAAAAAAAAAAAAAAAABCDEFAAAAAAAAAAAAAAAAAAAA  # 13548
    crc_poly = myhdl.intbv(0, _nrbits=9)
    crc_poly[8] = 1
    crc_poly[4] = 1
    crc_poly[3] = 1
    crc_poly[2] = 1
    crc_poly[0] = 1
    print(myhdl.bin(x, x._nrbits))
    print(myhdl.bin(crc_poly, crc_poly._nrbits))

    c, err = check_crc(x, crc_poly)

    print(myhdl.bin(c, c._nrbits))
    print(myhdl.bin(err, err._nrbits))

    d, derr = check_crc(x, crc_poly, err)

    print(myhdl.bin(d, d._nrbits))
    print(myhdl.bin(derr, derr._nrbits))


if __name__ == '__main__':

    def bench():
        serin, serout, clk = create_signals(3)
        dout = create_signals(1, 3)
        crc_poly = myhdl.intbv(0, _nrbits=4)
        crc_poly[:] = 11

        clockgen = clocker(clk)
        crc_stream = check_crc_stream(serin, clk, crc_poly, dout)

        # Padded 1 bit to the front and 3 to the back
        input_stream = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0,
                        1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0,
                        1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0,
                        1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0]

        @myhdl.instance
        def create_input():
            i = 0
            while True:
                yield clk.negedge
                i += 1
                if i >= len(input_stream):
                    raise myhdl.StopSimulation
                serin.next = input_stream[i]

        @myhdl.always(clk.posedge)
        def print_out():
            if frame_counter == 0:
                print("ZERO")
            print("|{:^6}|{:^6}|{:^6}|".format(int(serin), myhdl.bin(dout, dout._nrbits), serout))

        frame_counter = create_signals(1, (0, 16), mod=True)

        @myhdl.always(clk.posedge)
        def frame_counting():
            frame_counter.next = frame_counter + 1

        crc2 = check_crc_stream2(serin, serout, clk, crc_poly, frame_counter, 16)

        return clockgen, crc_stream, create_input, print_out, frame_counting, crc2

    run_sim(bench)
