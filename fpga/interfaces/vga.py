#!/usr/bin/env python

from __future__ import print_function
from myhdl import Signal, intbv, always, always_comb
from math import log, ceil
from colorama import init, deinit, reinit, Fore
init()
from fpga.examples.pong import PongPixelGenerator
from fpga import toVHDL

__author__ = 'michiel'


WIDTH = 640
HEIGTH = 480
HF = 16         # Horizontal Front porch
HB = 48         # Horizontal Back porch
HR = 96         # Horizontal Retrace
VF = 10         # Vertical Front porch
VB = 33         # Vertical Back porch
VR = 2          # Vertical Retrace
PIXEL_PER_LINE = WIDTH + HF + HB + HR
LINES_PER_SCREEN = HEIGTH + VF + VB + VR
SCREENS_PER_SECOND = 60
X_COUNT_BITS = ceil(log(PIXEL_PER_LINE, 2))
Y_COUNT_BITS = ceil(log(LINES_PER_SCREEN, 2))

infotext = """The display will be of size {width}x{height}
It has a pixel per line count of {ppl}
And a line per screen count of {lps}.
With a display refresh rate of {sps} Hz."""
CLOCK = PIXEL_PER_LINE * LINES_PER_SCREEN * SCREENS_PER_SECOND        # Clockspeed in Hz (25MHz)
print(Fore.RED + "The display clock should be at least: {clock} MHz".format(clock=CLOCK/1e6) + Fore.RESET)
print(Fore.BLUE + infotext.format(width=WIDTH, height=HEIGTH, ppl=PIXEL_PER_LINE, lps=LINES_PER_SCREEN, sps=SCREENS_PER_SECOND))


def color_create(i):
    b = (i % 2) == 1
    g = ((i / 2) % 2) == 1
    r = ((i / 4) % 2) == 1
    return [r, g, b]


def VGA_Controller(data, h_sync, v_sync, r, g, b, clk, rst):

    pixel_x = Signal(intbv(0, min=0)[X_COUNT_BITS:])
    pixel_y = Signal(intbv(0, min=0)[Y_COUNT_BITS:])
    video_on = Signal(False)

    vga_sync = VGA_Sync(pixel_x, pixel_y, video_on, h_sync, v_sync, clk, rst)
    pixel_gen = PixelGenerator(data, pixel_x, pixel_y, video_on, r, g, b, clk, rst)

    return vga_sync, pixel_gen


def VGA_Sync(pixel_x, pixel_y, video_on, h_sync, v_sync, clk, rst):

    hsync_reg, vsync_reg, hs_next, vs_next, h_end, v_end = [Signal(bool(0)) for _ in range(6)]
    h_count, hc_next = [Signal(pixel_x._val) for _ in range(2)]
    v_count, vc_next = [Signal(pixel_y._val) for _ in range(2)]

    @always(clk.posedge, rst.posedge)
    def clocked_logic():
        if rst:
            hsync_reg.next = False
            vsync_reg.next = False
            h_count.next = 0
            v_count.next = 0
        else:
            hsync_reg.next = hs_next #(pixel_x >= WIDTH + HF) and (pixel_x <= WIDTH + HF + HR - 1)
            vsync_reg.next = vs_next
            h_count.next = hc_next
            v_count.next = vc_next

    @always(h_count, h_end)
    def hor_counter():
        if h_end:
            hc_next.next = 0
        else:
            hc_next.next = h_count + 1

    @always(v_count, h_end, v_end)
    def ver_counter():
        if h_end:
            if v_end:
                vc_next.next = 0
            else:
                vc_next.next = v_count + 1
        else:
            vc_next.next = v_count

    @always_comb
    def comb_logic():
        hs_next.next = 1 if (h_count >= WIDTH + HF) and (h_count <= WIDTH + HF + HR -1) else 0
        vs_next.next = 1 if (v_count >= HEIGTH + VF) and (v_count <= HEIGTH + VF + VR -1) else 0
        h_end.next = 1 if h_count == PIXEL_PER_LINE - 1 else 0
        v_end.next = 1 if v_count == LINES_PER_SCREEN - 1 else 0

        # Outputs
        video_on.next = 1 if h_count < WIDTH and v_count < HEIGTH else 0
        h_sync.next = hsync_reg
        v_sync.next = vsync_reg
        pixel_x.next = h_count
        pixel_y.next = v_count

    return clocked_logic, comb_logic, hor_counter, ver_counter


def PixelGenerator(data, pixel_x, pixel_y, video_on, r, g, b, clk, rst):
    BLACK, BLUE, GREEN, CYAN, RED, MAGENTA, YELLOW, WHITE = [i for i in range(8)]

    COLORS = tuple([color_create(i) for i in range(8)])     # Infer ROM
    MAX_COLOR = r.max - 1
    red, green, blue, rnext, gnext, bnext = [Signal(intbv(0, min=r.min, max=r.max)) for _ in range(6)]

    pixel_gen = PongPixelGenerator(data, video_on, pixel_x, pixel_y, rnext, gnext, bnext, clk, rst)

    @always(clk.posedge, rst.posedge)
    def logic():
        if rst:
            red.next = 0
            green.next = 0
            blue.next = 0
        else:
            red.next = rnext
            green.next = gnext
            blue.next = bnext

    @always_comb
    def logic_comb():
        # Outputs
        r.next = red
        g.next = green
        b.next = blue

    return logic, logic_comb, pixel_gen

deinit()

def convert():
    data = Signal(intbv(0)[3:])
    h_sync, v_sync, clk, rst = [Signal(False) for _ in range(4)]
    r, g, b = [Signal(intbv(0)[8:]) for _ in range(3)]

    toVHDL(VGA_Controller, data, h_sync, v_sync, r, g, b, clk, rst)

convert()
# reinit()
# deinit()