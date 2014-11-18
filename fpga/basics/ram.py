#!/usr/bin/env python

from myhdl import Signal, always, intbv, always_comb
from fpga import toVHDL

__author__ = 'michiel'



def OnePortRamAsyncRead(we, addr, din, dout, clk):

    ADDR_WIDTH = len(addr)

    ram = [Signal(intbv(0, dout.min, dout.max)) for _ in range(2 ** ADDR_WIDTH)]

    @always(clk.posedge)
    def write():
        if we:
            ram[addr].next = din

    @always_comb
    def read():
        dout.next = ram[addr]

    return write, read

def OnePortRamSyncRead(we, addr, din, dout, clk):

    ADDR_WIDTH = len(addr)

    ram = [Signal(intbv(0, dout.min, dout.max)) for _ in range(2 ** ADDR_WIDTH)]
    addr_reg = Signal(intbv(0)[ADDR_WIDTH:])

    @always(clk.posedge)
    def write():
        if we:
            ram[addr].next = din
        addr_reg.next = addr

    @always_comb
    def read():
        dout.next = ram[addr_reg]

    return write, read

def convert():
    we, clk = [Signal(False) for _ in range(2)]
    addr = Signal(intbv(0, min=0, max=256))
    din, dout = [Signal(intbv(0, min=-64, max=64)) for _ in range(2)]
    toVHDL(OnePortRamAsyncRead, we, addr, din, dout, clk)

# convert()