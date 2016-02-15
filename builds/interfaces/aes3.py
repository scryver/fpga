from fpga import toVHDL
from fpga.utils import create_signals
from fpga.interfaces.aes3 import AES3_TX, AES3_RX_DEMUXED


def convert_tx():
    cs1, valid1, user1, cs2, valid2, user2, frame0, ce_word, ce_bit, \
        ce_bp, sdata, clk, rst = create_signals(13)
    audio_ch1, audio_ch2 = create_signals(2, 24, signed=True)

    toVHDL(AES3_TX, audio_ch1, cs1, valid1, user1, audio_ch2, cs2, valid2,
           user2, frame0, ce_word, ce_bit, ce_bp, sdata, clk, rst)


def convert_rx():
    din, valid1, user1, cs1, out_en, valid2, user2, cs2, parity_error, frame0, \
        locked, clk, rst = create_signals(13)
    audio_ch1, audio_ch2 = create_signals(2, 24, signed=True)
    frames = create_signals(1, 8)

    toVHDL(AES3_RX_DEMUXED, din, audio_ch1, valid1, user1, cs1, out_en,
           audio_ch2, valid2, user2, cs2, parity_error, frames, frame0, locked,
           clk, rst)

convert_rx()
convert_tx()
