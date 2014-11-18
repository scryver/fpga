#!/usr/bin/env python

from myhdl import Signal, intbv, always, always_comb, concat
from ball_bitmap import encoding

__author__ = 'michiel'

WIDTHH = 640
HEIGHT = 480

def PongPixelGenerator(data, video_on, pixel_x, pixel_y, r, g, b, clk, rst):

    MAX_COLOR = r.max - 1
    COLOR_BITS = len(r) * 3
    RED_BITS_MIN = COLOR_BITS - COLOR_BITS // 3
    GREEN_BITS_MIN = COLOR_BITS // 3

    refr_tick = Signal(False)

    # Vertical stripe as wall
    WALL_X_L = 32
    WALL_X_R = 35

    BAR_Y_SIZE = 72
    bar_yt, bar_yb = [Signal(intbv(0)[len(pixel_y):]) for _ in range(2)]
    bar_yreg = Signal(intbv(0)[len(pixel_y):])

    wall_on = Signal(bool(0))
    bar_on = Signal(bool(0))
    ball_on, rd_ball_on = [Signal(bool(0)) for _ in range(2)]

    wall_rgb = Signal(intbv(0)[COLOR_BITS:])
    bar_rgb = Signal(intbv(0)[COLOR_BITS:])
    ball_rgb = Signal(intbv(0)[COLOR_BITS:])

    @always_comb
    def reference():
        refr_tick.next = 1 if pixel_x == 0 and pixel_y == HEIGHT + 1 else 0

    @always_comb
    def wall_logic():
        wall_on.next = 1 if WALL_X_L <= pixel_x and pixel_x <= WALL_X_R else 0
        wall_rgb.next = MAX_COLOR

    @always_comb
    def yt_logic():
        bar_yt.next = bar_yreg

    @always_comb
    def yb_logic():
        bar_yb.next = bar_yt + BAR_Y_SIZE - 1

    bar_logic = AnimatedBar(data, refr_tick, pixel_x, pixel_y, bar_yt, bar_yb, bar_yreg, bar_on, bar_rgb, clk, rst)
    ball_logic = AnimatedBall(refr_tick, pixel_x, pixel_y, bar_yt, bar_yb, ball_on, rd_ball_on, ball_rgb, clk, rst)

    @always(video_on, wall_on, bar_on, rd_ball_on, wall_rgb, bar_rgb, ball_rgb)
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
                r.next = MAX_COLOR // 8
                g.next = MAX_COLOR // 8
                b.next = MAX_COLOR // 8

    return reference, wall_logic, yt_logic, yb_logic, bar_logic, ball_logic, pixel_select


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
        ball_rgb.next = concat(intbv(MAX_COLOR)[8:], intbv(0)[16:])

    return ball_logic


def AnimatedBall(refr_tick, pixel_x, pixel_y, bar_yt, bar_yb, ball_on, rd_ball_on, ball_rgb, clk, rst):

    MAX_COLOR = 2 ** (len(ball_rgb) // 3) - 1

    code = [None] * 8
    for key, value in encoding.items():
        if 0 <= key <= 7:
            code[key] = int(value, 2)
    code = tuple(code)

    WALL_X_R = 35
    BAR_X_L = 600
    BAR_X_R = 603
    BALL_SIZE = 8
    BALL_VELOCITY_POS = 2
    BALL_VELOCITY_NEG = -2

    ball_xl, ball_xr = [Signal(intbv(0)[len(pixel_x):]) for _ in range(2)]
    ball_yt, ball_yb = [Signal(intbv(0)[len(pixel_y):]) for _ in range(2)]
    ball_xreg, ball_xr_next = [Signal(intbv(0)[len(pixel_x):]) for _ in range(2)]
    ball_yreg, ball_yr_next = [Signal(intbv(0)[len(pixel_y):]) for _ in range(2)]
    x_delta_reg, xd_next = [Signal(intbv(0)[len(pixel_x):]) for _ in range(2)]
    y_delta_reg, yd_next = [Signal(intbv(0)[len(pixel_y):]) for _ in range(2)]

    rom_addr, rom_col = [Signal(intbv(0)[3:]) for _ in range(2)]
    rom_data = Signal(intbv(0)[8:])
    rom_bit = Signal(False)

    @always(clk.posedge, rst.posedge)
    def clocked_logic():
        if rst:
            ball_xreg.next = 0
            ball_yreg.next = 0
            x_delta_reg.next = 4
            y_delta_reg.next = 4
        else:
            ball_xreg.next = ball_xr_next
            ball_yreg.next = ball_yr_next
            x_delta_reg.next = xd_next
            y_delta_reg.next = yd_next

    @always_comb
    def ball_logic():
        ball_xl.next = ball_xreg
        ball_yt.next = ball_yreg

    @always_comb
    def ball2_logic():
        ball_yb.next = ball_yt + BALL_SIZE - 1
        ball_xr.next = ball_xl + BALL_SIZE - 1

    @always_comb
    def ball3_logic():
        ball_on.next = 1 if ball_xl <= pixel_x and pixel_x <= ball_xr and ball_yt <= pixel_y and pixel_y <= ball_yb else 0
        # Map pixel to rom
        rom_addr.next = pixel_y[3:] - ball_yt[3:]
        rom_col.next = pixel_x[3:] - ball_xl[3:]

    @always_comb
    def rom_lookup():
        rom_data.next = code[rom_addr]

    @always_comb
    def rom_lookup2():
        rom_bit.next = rom_data[rom_col]

    @always_comb
    def on_off_gen():
        rd_ball_on.next = 1 if ball_on and rom_bit else 0

    @always_comb
    def output_logic():
        # Output
        ball_rgb.next = concat(intbv(MAX_COLOR)[8:], intbv(0)[16:])
        ball_xr_next.next = ball_xreg + x_delta_reg if refr_tick else ball_xreg
        ball_yr_next.next = ball_yreg + y_delta_reg if refr_tick else ball_yreg

    @always(x_delta_reg, y_delta_reg, ball_yt, ball_yb, ball_xl, ball_xr, bar_yt, bar_yb)
    def ball_velocity():
        xd_next.next = x_delta_reg
        yd_next.next = y_delta_reg
        if ball_yt < 1:
            yd_next.next = BALL_VELOCITY_POS
        elif ball_yb > HEIGHT - 1:
            yd_next.next = BALL_VELOCITY_NEG
        elif ball_xl <= WALL_X_R:
            xd_next.next = BALL_VELOCITY_POS
        elif BAR_X_L <= ball_xr and ball_xr <= BAR_X_R:
            if bar_yt <= ball_yb and ball_yt <= bar_yb:
                xd_next.next = BALL_VELOCITY_NEG

    return clocked_logic, ball_logic, ball2_logic, ball3_logic, output_logic, ball_velocity, rom_lookup, rom_lookup2, on_off_gen

def AnimatedBar(buttons, refr_tick, pixel_x, pixel_y, bar_yt, bar_yb, yreg, bar_on, bar_rgb, clk, rst):

    MAX_COLOR = 2 ** (len(bar_rgb) // 3) - 1

    BAR_X_L = 600
    BAR_X_R = 603
    BAR_VELOCITY = 4

    bar_yreg, bar_yr_next = [Signal(intbv(0)[len(pixel_y):]) for _ in range(2)]

    @always(clk.posedge, rst.posedge)
    def clocked_logic():
        if rst:
            bar_yreg.next = 0
        else:
            bar_yreg.next = bar_yr_next

    @always_comb
    def logic():
        bar_on.next = 1 if BAR_X_L <= pixel_x and pixel_x <= BAR_X_R and bar_yt <= pixel_y and pixel_y <= bar_yb else 0
        bar_rgb.next = concat(intbv(0)[8:], intbv(MAX_COLOR)[8:], intbv(0)[8:])
        yreg.next = bar_yreg

    @always(bar_yreg, bar_yb, bar_yt, refr_tick, buttons)
    def animation():
        bar_yr_next.next = bar_yreg
        if refr_tick:
            if buttons[1] and bar_yb < HEIGHT - 1 - BAR_VELOCITY:
                bar_yr_next.next = bar_yreg + BAR_VELOCITY
            elif buttons[0] and bar_yb > BAR_VELOCITY:
                bar_yr_next.next = bar_yreg - BAR_VELOCITY

    return logic, clocked_logic, animation