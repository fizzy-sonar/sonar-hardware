# PDM capture contract v1

_Status: v1, 2026-08-25. Owners: T-008 defines the electrical/sample contract;
T-020 implements and testbench-checks it; T-009 and T-021 consume it._

## Normative configuration

| Item | v1 value |
|---|---:|
| Microphone | Syntiant `SPH0641LU4H-1` |
| Channels / physical data lines | 24 / 12, one SELECT-low + one SELECT-high mic per line |
| Mic clock | 3.072000 MHz nominal, 50% duty cycle |
| Electrical level | 3.3 V LVCMOS; no pull-up/down on shared PDM data |
| Capture | Both edges through an Artix-7 IDDR clocked from `PDM_CLK_FB` |
| Raw logical frame | 24 bits per 3.072 MHz clock period |
| Raw payload rate | 73.728 Mb/s = 9.216 MB/s, before transport framing |
| Main-path FPGA decimation | None; stream raw continuously to FT232H |
| Host reference decimation | 24, producing 128,000 samples/s/channel |
| Required host passband | 20–40 kHz (primary chirp band is 20–32 kHz) |

The main path follows the later, more specific D012 amendment: the Cmod A7 packs
raw PDM into its elastic FIFO and the laptop performs CIC/FIR processing. D011's
earlier consequence text assigning CIC/FIR to the FPGA is therefore stale for the
FT232H path. CIC in fabric remains optional only for the later DNP 100M RMII path.
This is an ordering clarification between ratified decisions, not an architecture
deviation.

The 3.072 MHz point is inside the Syntiant datasheet's 3.072–4.8 MHz Ultrasonic
Mode and is the exact condition used for its ultrasonic current and response data.
It is also the lowest raw bandwidth. The 128 ksample/s host output has a 64 kHz
Nyquist frequency and therefore retains the required 40 kHz upper band.

## Clock and startup state machine

The FPGA supplies `PDM_CLK_SRC` to the board clock buffer. The buffer returns one
matched output as `PDM_CLK_FB`; the IDDR must use that returned clock, not an
unconstrained copy of the clock-generator net. `PDM_CLK_FB` must land on an
MRCC/SRCC-capable Cmod pin; T-011 assigns the exact pin. Digilent's official Cmod
A7 XDC confirms multiple clock-capable GPIOs, including `pio3`, `pio5`, `pio8`,
`pio18`, `pio19`, `pio36`, `pio37`, `pio38`, `pio40`, `pio43`, `pio46`, `pio47`,
and `pio48`.

Syntiant explicitly says not to power up or wake directly into Ultrasonic Mode.
The implementation shall use this sequence:

1. Hold the clock-buffer output enable low while rails settle.
2. Enable a 1.536 MHz, 50% clock (valid Standard Performance Mode) for at least
   50 ms. This covers the datasheet's 50 ms maximum power-up time and 15 ms maximum
   wake time.
3. Disable the buffer, select the 3.072 MHz divide, and re-enable it so no runt
   pulse is presented to the microphones.
4. Discard the first 10 ms of PDM after 3.072 MHz begins (maximum mode-change time).
5. To sleep, disable the buffer so every output is held low. Every wake repeats
   steps 2–4; it never jumps from zero clock to 3.072 MHz.

An exact Cmod implementation is feasible from its 12 MHz oscillator: configure an
MMCM for 768 MHz VCO (`M=64`, `D=1`) and 6.144 MHz output (`O=125`), then use
toggle/divide logic for exact, 50%-duty 3.072 MHz and 1.536 MHz clocks. T-020 may
use a different legal clocking solution, but the external rates, glitchless switch,
and sequence above are normative.

## Edge and channel semantics

Per the Syntiant interface table, SELECT-high asserts DATA after a rising clock
edge and is latched on the falling edge; SELECT-low asserts after falling and is
latched on rising. For every data line `pdm_d[i]`:

- `channel[2*i]` is the SELECT-low microphone, sampled on the rising edge at `n*T`.
- `channel[2*i+1]` is the SELECT-high microphone, sampled on the falling edge at
  `n*T + T/2`.

The IDDR primitive's vendor-specific Q1/Q2 names do not define the external
contract. T-020's testbench must drive distinguishable alternating edge patterns
and prove the even/rising and odd/falling mapping above.

| Data | Even channel: SELECT low / rising | Odd channel: SELECT high / falling |
|---|---|---|
| D0 | CH00 / M00 | CH01 / M10 |
| D1 | CH02 / M20 | CH03 / M30 |
| D2 | CH04 / M01 | CH05 / M11 |
| D3 | CH06 / M21 | CH07 / M31 |
| D4 | CH08 / M02 | CH09 / M12 |
| D5 | CH10 / M32 | CH11 / M42 |
| D6 | CH12 / M03 | CH13 / M13 |
| D7 | CH14 / M23 | CH15 / M33 |
| D8 | CH16 / M04 | CH17 / M14 |
| D9 | CH18 / M24 | CH19 / M34 |
| D10 | CH20 / M40 | CH21 / M41 |
| D11 | CH22 / M43 | CH23 / M44 |

`Mxy` uses array coordinates `x=0..4`, `y=0..4`; `M22` is absent for the center TX
location. T-011 may choose FPGA pins but must not renumber this logical map.

## Pair time offset and calibration

The odd channel in each pair is sampled half a PDM period after the even channel:
162.760 ns at 3.072 MHz. At 343 m/s that is 55.83 um acoustic-path equivalent,
or 1.172 degrees at 20 kHz and 1.875 degrees at 32 kHz. The raw capture must not
pretend the edges are simultaneous. T-021 shall attach these time coordinates,
then advance odd channels by half a PDM period in the fractional-delay/per-channel
phase calibration. This correction happens before beamforming; it can be combined
with measured channel delay calibration after host decimation.

## Raw-frame boundary and transport handoff

A logical PDM frame is the 24-bit vector assembled from one rising/falling pair.
Frame `n` contains all even samples at `n*T` and odd samples at `n*T+T/2`.
Transport byte order, sync markers, counters, and loss signaling belong in the
separate T-020/T-021 packet-format contract. Whatever packing is selected must be
lossless and preserve this channel order and monotonically increasing frame number.

Required T-020 constants/testbench assertions:

```text
PDM_CLOCK_HZ       = 3_072_000
PDM_DATA_LINES     = 12
PDM_CHANNELS       = 24
PDM_FRAME_BITS     = 24
RAW_PAYLOAD_BPS    = 73_728_000
HOST_DECIMATION    = 24
HOST_SAMPLE_RATE_HZ= 128_000
EVEN_EDGE          = rising
ODD_EDGE           = falling
START_STANDARD_HZ  = 1_536_000
START_STANDARD_MS  = 50
ULTRASONIC_SETTLE_MS = 10
```

## Primary sources checked 2026-08-25

- [Syntiant SPH0641LU4H-1 datasheet](https://static1.squarespace.com/static/6488b0b8150a045d2d112999/t/674f6a2fc6aa4452caafc777/1733259031446/SPH0641LU4H-1_More_Rev_B-1.pdf): clock modes, current, interface timing, edge assignment, startup restrictions, and typical ultrasonic response.
- [Digilent Cmod A7 master XDC](https://github.com/Digilent/digilent-xdc/blob/master/Cmod-A7-Master.xdc): LVCMOS33 and clock-capable pin evidence. Exact project pin assignment remains T-011's job.
- [AMD DS181 v1.27.1](https://docs.amd.com/v/u/en-US/ds181_Artix_7_Data_Sheet): Artix-7 input timing and CPG236 package skew.

The Syntiant-hosted PDF currently contains broken template fields for document code,
revision, and copyright year. Its electrical tables match the older Knowles Rev B
document dated 2015-04-06, but the malformed metadata is explicitly not treated as
fresh revision evidence.
