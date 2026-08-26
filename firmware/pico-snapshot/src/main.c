#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/dma.h"
#include "hardware/pio.h"
#include "tusb.h"
#include "snapshot_protocol.h"
#include "pdm_capture.pio.h"

/* SRAM default: two 48 KiB windows (16,384 logical frames = 5.33 ms each).
 * This is deliberately small enough for Pico 2's 520 KiB SRAM beside code/stacks.
 * A board-specific Pico Plus 2 adapter may replace these pointers with PSRAM; that
 * adapter is the only PSRAM boundary and must preserve contiguous byte windows. */
#define WINDOW_FRAMES 16384u
#define WINDOW_BYTES (WINDOW_FRAMES * SONAR_BYTES_PER_FRAME)
/* DMA lands aligned 32-bit PIO words, then the inactive buffer is compacted. */
static uint32_t dma_words[2][WINDOW_FRAMES] __attribute__((aligned(4)));
static uint8_t window[2][WINDOW_BYTES] __attribute__((aligned(4)));
static volatile bool ready[2];
static uint32_t sequence;
extern void sonar_repack_pio_words(uint8_t *, const uint32_t *, uint32_t);

/* Board pin assignment is intentionally not frozen here; T-011 owns the header. */
static void configure_pio_dma(void) {
    PIO pio = pio0;
    uint clock_off = pio_add_program(pio, &pdm_clock_program);
    uint sample_off = pio_add_program(pio, &pdm_sample_program);
    (void)clock_off; (void)sample_off;
    /* The two DMA channels are chained ping-pong descriptors, each with
       transfer_count=WINDOW_FRAMES and write_addr=dma_words[index]. Completion
       IRQ only flips ready[index]; USB compaction/transmit runs on the inactive
       window. T-011 must provide PDM header GPIO numbers before this pin-specific
       setup is enabled. */
}
static void cdc_write_snapshot(const uint8_t *payload, uint32_t frames) {
    sonar_snapshot_header_t h = {.sequence = sequence++, .first_frame = 0,
        .clock_hz = 3072000, .channels = SONAR_CHANNELS, .data_lines = SONAR_DATA_LINES,
        .frame_count = frames, .payload_bytes = frames * SONAR_BYTES_PER_FRAME,
        .payload_crc32 = sonar_crc32(payload, frames * SONAR_BYTES_PER_FRAME)};
    uint8_t header[SONAR_SNAPSHOT_HEADER_BYTES];
    sonar_snapshot_encode_header(header, &h);
    while (!tud_cdc_connected()) tud_task();
    tud_cdc_write(header, sizeof header); tud_cdc_write(payload, h.payload_bytes); tud_cdc_write_flush();
}
int main(void) {
    stdio_init_all(); tusb_init(); configure_pio_dma();
    while (true) { tud_task(); for (unsigned i = 0; i < 2; ++i) if (ready[i]) {
        ready[i] = false; sonar_repack_pio_words(window[i], dma_words[i], WINDOW_FRAMES);
        cdc_write_snapshot(window[i], WINDOW_FRAMES);
    } }
}
