-- File: Multiplier35Bit.vhd
-- Generated by MyHDL 0.8.1
-- Date: Sun Nov 23 01:40:16 2014


library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use std.textio.all;

use work.pck_myhdl_081.all;

entity Multiplier35Bit is
    port (
        a: in signed (34 downto 0);
        b: in signed (34 downto 0);
        p: out signed (69 downto 0);
        clk: in std_logic;
        rst: in std_logic
    );
end entity Multiplier35Bit;
-- Some text here
--              ______           ____                             ____            _________
--   a[35:17]__|A    P|__mult1__|D  Q|__bufm1[36:]_______________|D  Q|__bufm11__|x[70:34] \
--   b[35:17]__|B     |         |>   |                           |>   |          |          \
--             |______|         |____|                           |____|          |           \
--              ______           ____                             ____           |            \
--   a[17:]____|A    P|__mult2__|D  Q|__bufm2[36:]_______________|D  Q|__bufm22__|x[34:]       \
--   b[17:]____|B     |         |>   |                           |>   |           \             |
--             |______|         |____|                           |____|            \            |          ____
--              ______           ____           ____                               |            |__adder__|D  Q|__p[70:]
--   a[35:17]__|A    P|__mult3__|D  Q|__bufm3__|    \                              /            |         |>   |
--   b[17:]____|B     |         |>   |         |     \            ____            /             |         |____|
--             |______|         |____|         \      |__addLow__|D  Q|__bufm34__|y[53:17]     /
--              ______           ____          /      |          |>   |          |            /
--   a[17:]____|A    P|__mult4__|D  Q|__bufm4__|     /           |____|          |           /
--   b[35:17]__|B     |         |>   |         |____/                            |          /
--             |______|         |____|                                           |_________/
-- 
-- :param a:
-- :param b:
-- :param p:
-- :param clk:
-- :param rst:
-- :return:

architecture MyHDL of Multiplier35Bit is


constant A_MAX: integer := 35;
constant MULTMAX: integer := 18;



signal bufm11: signed (35 downto 0);
signal b_upper: signed (17 downto 0);
signal addLow: signed (35 downto 0);
signal bufm34: signed (35 downto 0);
signal a_lower: signed (17 downto 0);
signal bufm4: signed (35 downto 0);
signal bufout: signed (69 downto 0);
signal bufm1: signed (35 downto 0);
signal bufm3: signed (35 downto 0);
signal bu_buf: signed (17 downto 0);
signal a_upper: signed (17 downto 0);
signal mult3: signed (35 downto 0);
signal mult2: unsigned(33 downto 0);
signal mult1: signed (35 downto 0);
signal b_lower: signed (17 downto 0);
signal bufm22: unsigned(33 downto 0);
signal adder: signed (69 downto 0);
signal al_buf: signed (17 downto 0);
signal au_buf: signed (17 downto 0);
signal bl_buf: signed (17 downto 0);
signal bufm2: unsigned(33 downto 0);
signal mult4: signed (35 downto 0);

begin




MULTIPLIER35BIT_CLOCKED_LOGIC: process (clk) is
begin
    if rising_edge(clk) then
        if bool(rst) then
            bufm1 <= to_signed(0, 36);
            bufm11 <= to_signed(0, 36);
            bufm2 <= to_unsigned(0, 34);
            bufm22 <= to_unsigned(0, 34);
            bufm3 <= to_signed(0, 36);
            bufm4 <= to_signed(0, 36);
            bufm34 <= to_signed(0, 36);
            bufout <= to_signed(0, 70);
            au_buf <= to_signed(0, 18);
            bu_buf <= to_signed(0, 18);
            al_buf <= to_signed(0, 18);
            bl_buf <= to_signed(0, 18);
        else
            bufm1 <= mult1;
            bufm11 <= bufm1;
            bufm2 <= mult2;
            bufm22 <= bufm2;
            bufm3 <= mult3;
            bufm4 <= mult4;
            bufm34 <= addLow;
            bufout <= adder;
            au_buf <= a_upper;
            bu_buf <= b_upper;
            al_buf <= a_lower;
            bl_buf <= b_lower;
        end if;
    end if;
end process MULTIPLIER35BIT_CLOCKED_LOGIC;



a_upper <= signed(unsigned(a(A_MAX-1 downto (A_MAX - MULTMAX))));
a_lower <= signed(unsigned'('0' & unsigned(a((A_MAX - MULTMAX)-1 downto 0))));
b_upper <= signed(unsigned(b(A_MAX-1 downto (A_MAX - MULTMAX))));
b_lower <= signed(unsigned'('0' & unsigned(b((A_MAX - MULTMAX)-1 downto 0))));
p <= bufout;


MULTIPLIER35BIT_ADDERS: process (bufm4, bufm22, bufm34, bufm11, bufm3) is
    variable y: integer;
    variable x: integer;
begin
    addLow <= (bufm3 + bufm4);
    x := to_integer(shift_left(bufm11, (A_MAX - 1)) + signed(resize(unsigned'('0' & bufm22), 36)));
    y := to_integer(shift_left(bufm34, (A_MAX - MULTMAX)));
    adder <= to_signed(x + y, 70);
end process MULTIPLIER35BIT_ADDERS;



mult1 <= (au_buf * bu_buf);
mult2 <= resize(unsigned(al_buf) * unsigned(bl_buf), 34);
mult3 <= (au_buf * bl_buf);
mult4 <= (al_buf * bu_buf);

end architecture MyHDL;
