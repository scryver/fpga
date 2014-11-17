#!/usr/bin/env python

from myhdl import Signal, intbv, always, always_comb
from ball_bitmap import encoding

__author__ = 'michiel'

WIDTH = 640
HEIGHT = 480

def PongPixelGenerator(video_on, pixel_x, pixel_y, r, g, b):

    MAX_COLOR = r.max - 1
    COLOR_BITS = len(r) * 3
    RED_BITS_MIN = COLOR_BITS - COLOR_BITS // 3
    GREEN_BITS_MIN = COLOR_BITS // 3

    # Vertical stripe as wall
    WALL_X_L = 32
    WALL_X_R = 35

    # Right paddle bar
    BAR_X_L = 600
    BAR_X_R = 603
    BAR_Y_SIZE = 72
    BAR_VELOCITY = 4
    bar_yt, bar_yb = [Signal(intbv(0)[len(pixel_y):]) for _ in range(2)]
    bar_yreg, bar_yr_next = [Signal(intbv(0)[len(pixel_y):]) for _ in range(2)]

    # Square ball
    BALL_SIZE = 8
    BALL_VELOCITY_POS = 2
    BALL_VELOCITY_NEG = -2
    ball_xl, ball_xr = [Signal(intbv(0)[len(pixel_x):]) for _ in range(2)]
    ball_yt, ball_yb = [Signal(intbv(0)[len(pixel_y):]) for _ in range(2)]
    ball_xreg, ball_xr_next = [Signal(intbv(0)[len(pixel_x):]) for _ in range(2)]
    ball_yreg, ball_yr_next = [Signal(intbv(0)[len(pixel_y):]) for _ in range(2)]
    x_delta_reg, xd_next = [Signal(intbv(0)[len(pixel_x):]) for _ in range(2)]
    y_delta_reg, yd_next = [Signal(intbv(0)[len(pixel_y):]) for _ in range(2)]

    wall_on = Signal(bool(0))
    bar_on = Signal(bool(0))
    ball_on, rd_ball_on = [Signal(bool(0)) for _ in range(2)]

    wall_rgb = Signal(intbv(0)[COLOR_BITS:])
    bar_rgb = Signal(intbv(0)[COLOR_BITS:])
    ball_rgb = Signal(intbv(0)[COLOR_BITS:])

    @always_comb
    def wall_logic():
        wall_on.next = 1 if WALL_X_L <= pixel_x and pixel_x <= WALL_X_R else 0
        wall_rgb.next = MAX_COLOR


    @always_comb
    def bar_logic():
        bar_on.next = 1 if BAR_X_L <= pixel_x and pixel_x <= BAR_X_R and BAR_Y_T <= pixel_y and pixel_y <= BAR_Y_B else 0
        bar_rgb.next = MAX_COLOR << 8


    # ball_logic = SimpleBall(pixel_x, pixel_y, ball_on, ball_r, ball_g, ball_b)
    ball_logic = AnimatedBall(pixel_x, pixel_y, ball_on, rd_ball_on, ball_xl, ball_xr,
                              ball_yt, ball_yb, ball_rgb)

    @always(video_on, wall_on, bar_on, ball_on, wall_rgb, bar_rgb, ball_rgb)
    def pixel_select():
        if not video_on:
            r.next = 0
            g.next = 0
            b.next = 0
        else:
            if wall_on:
                r.next = wall_rgb[COLOR_BITS:RED_BITS_MIN]
                g.next = wall_rgb[RED_BITS_MIN:GREEN_BITS_MIN]
                b.next = wall_rgb[GREEN_BITS_MIN:]
            elif bar_on:
                r.next = bar_rgb[COLOR_BITS:RED_BITS_MIN]
                g.next = bar_rgb[RED_BITS_MIN:GREEN_BITS_MIN]
                b.next = bar_rgb[GREEN_BITS_MIN:]
            elif rd_ball_on:
                r.next = ball_rgb[COLOR_BITS:RED_BITS_MIN]
                g.next = ball_rgb[RED_BITS_MIN:GREEN_BITS_MIN]
                b.next = ball_rgb[GREEN_BITS_MIN:]
            else:
                r.next = MAX_COLOR // 4
                g.next = MAX_COLOR // 4
                b.next = MAX_COLOR // 4


    return wall_logic, bar_logic, ball_logic, pixel_select

def SimpleBall(pixel_x, pixel_y, ball_on, ball_rgb):

    MAX_COLOR = 2 ** (len(ball_rgb) // 3) - 1

    BALL_SIZE = 8
    BALL_X_L = 580
    BALL_X_R = BALL_X_L + BALL_SIZE - 1
    BALL_Y_T = 238
    BALL_Y_B = BALL_Y_T + BALL_SIZE - 1

    @always_comb
    def ball_logic():
        ball_on.next = 1 if BALL_X_L <= pixel_x and pixel_x <= BALL_X_R and BALL_Y_T <= pixel_y and pixel_y <= BALL_Y_B else 0
        ball_rgb.next = MAX_COLOR << 16

    return ball_logic


def AnimatedBall(pixel_x, pixel_y, ball_on, rd_ball_on, ball_xl, ball_xr, ball_yt, ball_yb, ball_rgb):

    MAX_COLOR = 2 ** (len(ball_rgb) // 3) - 1


    code = [None] * 8
    for key, value in encoding.items():
        if 0 <= key <= 7:
            code[key] = int(value, 2)
    code = tuple(code)

    rom_addr, rom_col = [Signal(intbv(0)[3:]) for _ in range(2)]
    rom_data = Signal(intbv(0)[8:])
    rom_bit = Signal(False)

    @always_comb
    def ball_logic():
        ball_on.next = 1 if ball_xl <= pixel_x and pixel_x <= ball_xr and ball_yt <= pixel_y and pixel_y <= ball_yb else 0
        # Map pixel to rom
        rom_addr.next = pixel_y[3:] - ball_yt[3:]
        rom_col.next = pixel_x[3:] - ball_xl[3:]

    @always_comb
    def rom_lookup():
        rom_data.next = code[rom_addr]
        rom_bit.next = rom_data[rom_col]
        rd_ball_on.next = 1 if ball_on and rom_bit else 0

        # Output
        ball_rgb.next = MAX_COLOR << 16

    return ball_logic, rom_lookup