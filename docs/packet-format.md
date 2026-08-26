# Sonar transport packets v1
## SNP1 Pico snapshot
Little endian 48-byte header: `SNP1` bytes 0–3; version u8 1 (4); header bytes u8 48 (5); flags u16 0 (6); capture ID u32 (8); first logical frame u64 (12); PDM clock Hz u32 (20); channels/data lines u16 24/12 (24); frame count/payload bytes u32 (28); payload CRC32 (36); header CRC32 bytes 0–39 (40); reserved u32 zero (44). Payload is 3 bytes/frame, bits CH00..CH23, even rising then odd falling.
## SNR1 FT232H continuous
Agreed with T-020: fixed 32-byte LE header emitted once per fresh capture: `SNR1` at
0, version u8=1 at 4, header length u8=32 at 5, flags u16=`0x0007` at 6 (raw PDM,
3-byte LE frames, even-rise/odd-fall), capture ID u32 at 8, first logical frame u64
at 12, clock Hz u32 at 20, channels/data lines u16 24/12 at 24, reserved u32 zero
at 28. It is followed by unbounded 3-byte logical frames using SNP1 bit packing.
There is no payload magic/CRC/trailer: payload bytes cannot be resynchronized. FT
backpressure is lossless; FPGA FIFO overflow permanently stops a capture, then drains
accepted bytes. Host must treat timeout/short capture as incomplete and query sticky
hardware status through a future control path.
