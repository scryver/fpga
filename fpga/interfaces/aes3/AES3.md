AES3

audio_blocks = [0 .. x]                 => Infinite audio blocks
frames = audio_blocks[0] [0 .. 191]     => 192 frames / audio block
subframe = frames[0] [0 .. 1]           => 2 subframes / frame
time_slot = subframe[0] [0 .. 31]       => 32 time slots / subframe


____________|___blocks|frames|subfra|timeslo|
audio_blocks|       1 |  192 |  384 | 12288 |
frames      |   1/192 |    1 |    2 |    64 |
subframes   |   1/384 |  1/2 |    1 |    32 |
time_slots  | 1/12288 | 1/64 | 1/32 |     1 |

1 time_slot = 1 channel sample of audio

bits
0-3     Preamble
4-7     Auxiliary sample (exampl. talkback)
8-27    Audio sample (or 4-27) => MSB stored last / LSB send first
28      Validity        (V)
29      User data       (U)     => Per channel (MSB in last frame)
30      Channel status  (C)     => Per channel (MSB in last frame)
31      Parity          (P) Set if bits 4–30 have odd parity, or equivalently, so bits 4–31 have even parity.

Preambles:
X = 11100010 (if prev. was 0) or 00011101 (if prev. was 1) Marks word for ch A, not at start of audio block
Y = 11100100 (if prev. was 0) or 00011011 (if prev. was 1) Marks word for ch B
Z = 11101000 (if prev. was 0) or 00010111 (if prev. was 1) Marks word for ch A at start of audio block

Preambles are the first 4 time slots of a subframe (0-3)

| 0 | 1 | 2 | 3 |  | 0 | 1 | 2 | 3 |  Time slots
|___|_  |   |_  |  |   |  _|___|  _|
/   | \_|___/ \_/  \___|_/ |   \_/ \  Preamble X
|___|_  |  _|   |  |   |  _|_  |___|
/   | \_|_/ \___/  \___|_/ | \_/   \  Preamble Y
|___|_  |_  |   |  |   |  _|  _|___|
/   | \_/ \_|___/  \___|_/ \_/ |   \  Preamble Z
|___|   |___|   |  |   |___|   |___|
/   \___/   \___/  \___/   \___/   \  All 0 bits BMC Encoded
|_  |_  |_  |_  |  |  _|  _|  _|  _|
/ \_/ \_/ \_/ \_/  \_/ \_/ \_/ \_/ \  All 1 bits BMC Encoded
|   |   |   |   |  |   |   |   |   |
| 0 | 1 | 2 | 3 |  | 0 | 1 | 2 | 3 |  Time slots

2-channel AES:      ZYXYXYXYXY....
multi-channel AES:  ZYYXYYXYYXYYXYY... (ZYYYYYXYYYYYXYYYYYXYYYYY....)

Channel status: 192 bit word per channel/per block
Usually divided in 24 bytes (192/8)
  Byte | Bits |
     0 |      | Basic control data, sample rate, compression, emphasis
       |    0 |    A value of 1 = AES/EBU, 0 = S/PDIF
       |    1 |    A value of 0 = Linear PCM, 1 = other data (maybe non-audio)
       |  2-4 |    Type of signal preemphasis applied to data (100 = None)
       |    5 |    A value of 0 = Locked source to external time sync. 1 = unlocked source
       |  6-7 |    Sample rate (mostly for storage)
     1 |      | Indicates if the audio stream is stereo, mono or some other combination
       |  0-3 |    Indicates relation between 2 channels, unrelated, stereo, dupl. mono, music/voice commentary, stereo sum/diff
       |  4-7 |    Indicate the format of the user channel word
     2 |      | Audio word length
       |  0-2 |    Aux bits usage. Indicates how aux bits (4-7) are used. 000 = unused, 001 = 24 bit audio
       |  3-5 |    Word length. Specifies sample size, rel. to 20- or 24-bit maximum. Can specify 0, 1, 2 or 4 missing bits. Unused bits are
       |      |      filled with 0, but audio processing functions (such as mixing) will generally fill them with valid data without changing the
       |      |      effective word length.
       |  6-7 |    Unused
     3 |      | Used only for multichannel applications
     4 |      | Additional sample rate information
       |  0-1 |    Indicates the grade of the sample rate reference (per AES11)
       |    2 |    Reserved
       |  3-6 |    Extended sample rate. This indicates other sample rates, not reprs. in byte 0[6-7]. (24, 96, 192kHz etc)
       |    7 |    Sampling frequency scaling flag. If set, indicates that the sample rate is multiplied by 1/1.001 to match NTSC video
     5 |      | Reserved
  6- 9 |      | Four ASCII characters for indicating channel origin. (Used in large studios)
 10-13 |      | Four ASCII characters for indicating channel destination, to control automatic switchers.
 14-17 |      | 32-bit sample address, incrementing block-to-block by 192. (At 48 kHz, this wraps every 24h51m18.485333s)
 18-21 |      | As 14-17 but offset to indicate samples since midnight
    22 |      | Contains information about reliability of the channel status word
       |  0-3 |    Reserved
       |    4 |    If set bytes 0-5 (signal format) are unreliable
       |    5 |    If set bytes 6-13 (channel labels) are unreliable
       |    6 |    If set bytes 14-17 (sample address) are unreliable
       |    7 |    If set bytes 18-21 (timestamp) are unreliable
    23 |      | CRC. This byte is used to detect corruption of the channel status word, as might be caused by switching mid-block.
       |      |    Generator polynomial is x^8 + x^4 + x^3 + x^2 + 1, preset to 1
