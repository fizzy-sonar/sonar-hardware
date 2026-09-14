# FT232H USB-C bench preflight — T-023 / T-024 / T-025

2026-09-13: schematic-level adapter audit only. No board, EEPROM contents, physical
bus timing or throughput was observed. This is an experiment checklist, not an
instruction to connect an unconfigured bridge to an actively driving FPGA.

Sources: [Adafruit's current Eagle schematic](https://github.com/adafruit/Adafruit-FT232H-Breakout-PCB/blob/master/Adafruit%20FT232H.sch),
[FTDI datasheet, sections 3.5.2 and 4.13–4.14](https://ftdichip.com/wp-content/uploads/2024/09/DS_FT232H.pdf),
and `orchestration/pinmap.md`. The schematic was downloaded and its XML nets
inspected locally. FTDI's direct PDF fetch returned 403; its primary-source
search-indexed pin table and mode-selection text were readable. Exact module
revision and datasheet revision must be archived at physical bring-up.

| Adafruit silk | Synchronous FIFO function | Cmod DIP position / connection |
|---|---|---|
| D0..D7 | FIFO D0..D7 | 26, 27, 28, 29, 30, 31, 32, 33 respectively |
| C0 | RXF# | 34 |
| C1 | TXE# | 35 |
| C2 | RD# | 36 |
| C3 | WR# | 37 |
| C4 | SIWU# | Pull to bridge VCCIO (3.3 V) when unused; no Cmod signal assigned |
| C5 | 60 MHz CLKOUT | 47 (U8, clock-capable) |
| C6 | OE# | 38 |
| GND | Shared reference | Cmod GND, DIP 25 |

The Adafruit schematic maps IC2 ACBUS0..6 to C0..6; D0..7 are exposed as well.
It includes a 93LC56B EEPROM. Its I2C switch can join D1/D2: keep that switch OFF
and the STEMMA connector empty. R10/R11 are 12k pulls on D0/D1, not on the
microphone data; include their loading in the FPGA-to-bridge timing experiment.
Neither the USB-C connector nor the product's SPI/I2C examples establish FIFO
operation. Do not substitute SPI/MPSSE throughput for this parallel interface.

Before actively connecting the buses:

1. Acquire the module with soldered headers or budget assembly. Prepare a short
   grounded adapter suited to 60 MHz, with labeled pin 1 and continuity checks;
   loose long breadboard wiring is not a timing reference. Verify actual module
   revision against the schematic. Keep board 5 V/3.3 V outputs separate unless
   a reviewed power plan explicitly connects them.
2. Read and save its original EEPROM; record serial number/revision. Configure
   **FT245 FIFO in EEPROM**, verify readback and reset/re-enumerate, then request
   **synchronous FIFO mode 0x40** through the host. Both settings are required by
   FTDI section 4.13. The current host constructor calls only `set_bitmode(0,0x40)`;
   it neither checks nor supplies the EEPROM prerequisite.
3. Check CLKOUT = 60 MHz and default OE#/RD#/SIWU#/TXE# behavior before the FPGA
   drives the bus. Ensure there is no bus contention during boot/re-enumeration.
   Preserve the original EEPROM for rollback; never flash a guessed image.
4. T-020 supplies input/output setup and hold constraints against CLKOUT plus
   actual adapter delay. Verify WR#/data/TXE# behavior physically. T-024 supplies
   explicit idle/deadline/disconnect semantics and closes/releases the USB device.
5. T-023/T-024 supply a known counter-pattern source and recording/checking CLI.
   Demonstrate sustained 9.216 then 14.4 MB/s, measure stall tolerance, count
   losses and save captures/source IDs. Test the intended cable/hub/macOS setup,
   including busy host and reconnect, before declaring continuous readout ready.

The current FPGA keeps OE# and RD# high and only transmits; control commands must
be implemented on an appropriate interface, not assumed to exist because RXF#
is pinned. The independent Cmod SRAM/UART path remains the diagnostic fallback.
