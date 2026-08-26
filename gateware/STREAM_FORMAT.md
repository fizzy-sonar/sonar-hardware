# Raw capture wire formats

Status: T-020 proposal for T-021 adoption/review. Multi-byte integers are unsigned
little-endian. The canonical physical channel map remains
`docs/pdm-capture-contract.md`.

## Shared payload

Every logical PDM frame is exactly three bytes:

| Byte | Bits |
|---:|---|
| 0 | `CH00..CH07` in bits 0..7 |
| 1 | `CH08..CH15` in bits 0..7 |
| 2 | `CH16..CH23` in bits 0..7 |

Therefore channel `2*i` is DATA line `i` sampled on the rising edge and channel
`2*i+1` is that line sampled on the following falling edge. This payload is
byte-for-byte identical in `SNP1` and `SNR1`.

## Bounded UART snapshot: SNP1 v1

The simulator implements the shared 48-byte SNP1 v1 header already proposed by
T-009:

| Offset | Type | Field |
|---:|---|---|
| 0 | `char[4]` | ASCII `SNP1` |
| 4 | `u8` | version = 1 |
| 5 | `u8` | header bytes = 48 |
| 6 | `u16` | flags = 0 |
| 8 | `u32` | capture ID/sequence |
| 12 | `u64` | first logical frame |
| 20 | `u32` | PDM clock Hz |
| 24 | `u16` | channel count = 24 |
| 26 | `u16` | data-line count = 12 |
| 28 | `u32` | logical frame count |
| 32 | `u32` | payload bytes = 3 * frame count |
| 36 | `u32` | payload CRC-32 |
| 40 | `u32` | CRC-32 over header bytes 0..39 |
| 44 | `u32` | reserved = 0 |

IEEE CRC-32 uses reflected polynomial `0xedb88320`, initial state `0xffffffff`,
and final XOR `0xffffffff` (the result produced by Python `zlib.crc32`).

## Continuous FT245 stream: SNR1 v1

One 32-byte header begins each fresh capture:

| Offset | Type | Field |
|---:|---|---|
| 0 | `char[4]` | ASCII `SNR1` |
| 4 | `u8` | version = 1 |
| 5 | `u8` | header bytes = 32 |
| 6 | `u16` | flags = `0x0007`: raw PDM, 3-byte LE frame, fixed edge map |
| 8 | `u32` | capture ID/sequence |
| 12 | `u64` | first logical frame (zero in the present core) |
| 20 | `u32` | PDM clock Hz (`3072000` or `4800000`) |
| 24 | `u16` | channel count = 24 |
| 26 | `u16` | data-line count = 12 |
| 28 | `u32` | reserved = 0 |

The raw three-byte frames follow without padding or in-band markers. Logical frame
number is implicit: `first_logical_frame + payload_byte_offset / 3`.
The present core starts each capture at logical frame zero. Its capture ID starts
at zero after global reset and increments once for every accepted rising edge of
the synchronized capture control.

### Capture boundary

- No byte is emitted merely because reset was released. A synchronized rising
  `capture_enable` starts exactly one header, followed by that capture's payload.
- `capture_enable` low is an explicit abort/fresh-stream boundary. Hold it low for
  at least three rising edges of both `PDM_CLK_FB` and `FT_CLK`; the supplied
  startup controller holds it low for milliseconds. Both FIFO ports, the packer,
  and header are reset locally during that interval, so stale payload cannot be
  followed by a new header.
- Deasserting capture may discard an undrained tail and therefore ends the old
  host parse operation. It is not a graceful end-of-stream command. To preserve
  an overflowed prefix, keep capture asserted while the FIFO drains, observe
  `capture_stopped`, then establish the explicit low boundary.
- `overflow_sticky` and `capture_stopped` are top-level status outputs. They stay
  asserted through the low interval after an overflow and clear only at the next
  PDM-domain capture start (or global reset).

### Backpressure, loss, and resynchronization

- `TXE#` high stalls the FT245 reader. No FIFO word or byte advances while stalled.
- `ft245_sync_tx` adds a one-byte registered output stage. `WR#` and data change
  only from `FT_CLK`, giving the next FT232H sampling edge a full clock period of
  setup; retirement still requires both sampled `TXE#` and registered `WR#` low.
  This follows the write qualification and 7.5 ns minimum setup requirements in
  [FTDI's FT232H datasheet](https://ftdichip.com/wp-content/uploads/2024/09/DS_FT232H.pdf).
- The input FIFO allocates 16,384 32-bit words = 65,536 bytes. Each word stores one
  24-bit frame plus an unused high byte, so it buffers 16,384 logical frames
  (5.333 ms at 3.072 MHz or 3.413 ms at 4.8 MHz).
- If that FIFO becomes full, the producer does not overwrite or skip a frame and
  continue. It latches `overflow_sticky`, permanently stops that capture, and
  drains only the already accepted prefix. Payload prefetch is held until the
  header completes, so the elastic capacity is exactly 16,384 complete frames.
- SNR1 v1 has no trailer, payload CRC, or trustworthy in-band resync marker. Magic
  can occur naturally in PDM bytes. A host starts parsing only at a fresh capture
  boundary, groups every subsequent three bytes as a frame, and treats timeout,
  disconnect, short capture, or asserted external overflow status as incomplete.
  It must not scan arbitrary payload for `SNR1` and claim recovery.
- A future bidirectional control/status protocol may add an explicit terminal
  record or chunked counters/CRCs. That is a versioned format change, not something
  this skeleton silently implies.
