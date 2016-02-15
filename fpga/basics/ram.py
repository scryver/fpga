#!/usr/bin/env python

from myhdl import Signal, always, intbv, always_comb, always_seq
from fpga import toVHDL

__author__ = 'michiel'

# For xilinx no async! (better performance)


def OnePortRamAsyncRead(we, addr, din, dout, clk, reset=None):

    ADDR_WIDTH = len(addr)

    ram = [Signal(intbv(0, dout.min, dout.max)) for _ in range(2 ** ADDR_WIDTH)]

    @always_seq(clk.posedge, reset=reset)
    def write():
        if we:
            # Note how we use the val attribute of the din signal, as we don't want to store
            # the signal object itself, but its current value. Similarly, we use the val
            # attribute of the addr signal as the dictionary key.
            ram[addr.val].next = din.val

    @always_comb
    def read():
        dout.next = ram[addr.val]

    return write, read

def OnePortRamSyncRead(we, addr, din, dout, clk, reset=None):

    def init_ram():
        return [Signal(intbv(0, dout.min, dout.max)) for _ in range(2 ** ADDR_WIDTH)]

    ADDR_WIDTH = len(addr)

    ram = init_ram()
    addr_reg = Signal(intbv(0)[ADDR_WIDTH:])

    @always_seq(clk.posedge, reset=reset)
    def write():
        if we:
            ram[addr.val].next = din.val
        addr_reg.next = addr.val

    @always_comb
    def read():
        dout.next = ram[addr_reg.val]

    return write, read

def OnePortRomSyncRead(addr, dout, clk, ROM_DATA, reset=None):

    ADDR_WIDTH = len(addr)

    rombuf = tuple([int(ROM_DATA[i]) for i in range(len(ROM_DATA))])
    addr_reg = Signal(intbv(0)[ADDR_WIDTH:])

    @always_seq(clk.posedge, reset=reset)
    def addr_write():
        addr_reg.next = addr.val

    @always_comb
    def read():
        dout.next = rombuf[addr_reg.val]

    return addr_write, read

def ShiftRegister(din, ce, dout, clk, reset=None, length=8):

    ram = [Signal(intbv(0, dout.min, dout.max)) for _ in range(length)]

    @always_seq(clk.posedge, reset=reset)
    def shift():
        if ce:
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
    toVHDL(ShiftRegister, din, we, dout, clk)

if __name__ == '__main__':
    convert()
