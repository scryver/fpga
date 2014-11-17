#!/usr/bin/env python

__author__ = 'michiel'

from myhdl import always, modbv


def ModCounter(count, clk, rst):

    assert isinstance(count._val, modbv)

    @always(clk.posedge)
    def counting():
        if rst:
            count.next = 0
        else:
            count.next = count + 1

    return counting

def ModStartStopCounter(count, startstop, clk, rst):

    assert isinstance(count._val, modbv)

    @always(clk.posedge)
    def counting():
        if rst:
            count.next = 0
        elif startstop:
            count.next = count + 1

    return counting