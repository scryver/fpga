#!/usr/bin/env python

from myhdl import block, Signal, always, intbv, always_comb, always_seq, ResetSignal

from fpga.utils import create_signals, create_same_signals

__author__ = 'michiel'

# For xilinx no async! (better performance)

@block
def OnePortRam(clk, we, addr, din, dout, reset=None, reset_active=1, init_vals=None, async_read=False):

    ADDR_WIDTH = len(addr)
    RAM_LENGTH = 2 ** ADDR_WIDTH

    if init_vals is None:
        init_vals = [0 for _ in range(RAM_LENGTH)]
        ram = create_same_signals(RAM_LENGTH, dout)
    else:
        todo = RAM_LENGTH - len(init_vals)
        for i in range(todo):
            init_vals.append(0)
        ram = [Signal(intbv(value, dout.min, dout.max)) for value in init_vals]

    if async_read:
        if reset is None or isinstance(reset, ResetSignal):
            @always_seq(clk.posedge, reset=reset)
            def write():
                if we == 1:
                    # TODO(michiel): Is this still necessary??????? (upgrade to myhdl 1.0)
                    # Note how we use the val attribute of the din signal, as we don't want to store
                    # the signal object itself, but its current value. Similarly, we use the val
                    # attribute of the addr signal as the dictionary key.
                    ram[int(addr)].next = din
        else:
            @always(clk.posedge)
            def write():
                if reset == reset_active:
                    for i, r in enumerate(ram):
                        r.next = init_vals[i]
                else:
                    ram[int(addr)].next = din

        @always_comb
        def read():
            dout.next = ram[int(addr)]

        return write, read

    else:
        if reset is None or isinstance(reset, ResetSignal):
            @always_seq(clk.posedge, reset=reset)
            def read_write():
                dout.next = ram[int(addr)]
                if we:
                    ram[int(addr)].next = din
        else:
            @always_seq(clk.posedge, reset=reset)
            def read_write():
                if reset == reset_active:
                    for i, r in enumerate(ram):
                        r.next = init_vals[i]
                    dout.next = 0
                else:
                    dout.next = ram[int(addr)]
                    if we:
                        ram[int(addr)].next = din

        return read_write


@block
def OnePortRomSyncRead(clk, addr, dout, ROM_DATA, reset=None, reset_active=1):

    ADDR_WIDTH = len(addr)

    assert isinstance(ROM_DATA, tuple), ("Please supply a tuple for ROM_DATA, we need something non-changeable otherwise it won't get compiled to ROM!")
    # rombuf = tuple(map(int, ROM_DATA))
    addr_reg = Signal(intbv(0)[ADDR_WIDTH:])

    if len(ROM_DATA) < 2 ** ADDR_WIDTH:
        print("WARNING: Address too big so returning 0 for outer of bound addressing.")
        r = list(ROM_DATA)
        for i in range(2 ** ADDR_WIDTH - len(ROM_DATA)):
            r.append(0)
        ROM_DATA = tuple(r)
    elif len(ROM_DATA) > 2 ** ADDR_WIDTH:
        print("WARNING: The address is too small to access all ROM data!")

    if reset is None or isinstance(reset, ResetSignal):
        @always_seq(clk.posedge, reset=reset)
        def read():
            dout.next = ROM_DATA[int(addr)]
    else:
        @always(clk.posedge)
        def read():
            if reset == reset_active:
                dout.next = 0
            else:
                dout.next = ROM_DATA[int(addr)]

    return read


@block
def ShiftRegister(clk, ce, din, dout, reset=None, reset_active=1, length=8):

    ram = create_same_signals(length, dout)


    if reset is None or isinstance(reset, ResetSignal):
        if isinstance(ce, bool):
            assert enable, "Enable never True cannot be allowed!"

            @always_seq(clk.posedge, reset=reset)
            def shift():
                for i in range(length):
                    if i == 0:
                        ram[i].next = din
                    else:
                        ram[i].next = ram[i - 1]
        else:
            @always_seq(clk.posedge, reset=reset)
            def shift():
                if ce:
                    for i in range(length):
                        if i == 0:
                            ram[i].next = din
                        else:
                            ram[i].next = ram[i - 1]
    else:
        if isinstance(ce, bool):
            assert enable, "Enable never True cannot be allowed!"

            @always(clk.posedge)
            def shift():
                if reset == reset_active:
                    for i in range(length):
                        ram[i].next = 0
                else:
                    for i in range(length):
                        if i == 0:
                            ram[i].next = din
                        else:
                            ram[i].next = ram[i - 1]
        else:
            @always(clk.posedge)
            def shift():
                if reset == reset_active:
                    for i in range(length):
                        ram[i].next = 0
                elif ce:
                    for i in range(length):
                        if i == 0:
                            ram[i].next = din
                        else:
                            ram[i].next = ram[i - 1]

    @always_comb
    def logic():
        dout.next = ram[length - 1]

    return shift, logic


def convert():
    we, clk = [Signal(False) for _ in range(2)]
    # addr = Signal(intbv(0, min=0, max=256))
    din, dout = [Signal(intbv(0, min=-64, max=64)) for _ in range(2)]
    inst = ShiftRegister(clk, we, din, dout)
    inst.convert(hdl='VHDL')


if __name__ == '__main__':
    convert()
