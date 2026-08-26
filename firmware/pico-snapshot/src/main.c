#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/dma.h"
#include "hardware/pio.h"
#include "tusb.h"
#include "snapshot_protocol.h"
#include "capture_config.h"
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

/* Build supplies pins; defaults deliberately invalid until T-011 assigns header pins. */
#ifndef PDM_CLK_GPIO
#define PDM_CLK_GPIO 255u
#define PDM_DATA_GPIO 255u
#endif
static int dma_chan, discard_chan, sm; static volatile int completed = -1; static int active; static uint64_t logical_frame; static uint32_t discard_word;
static void set_clock(uint32_t hz,bool on){pio_sm_set_enabled(pio0,sm,false);gpio_put(PDM_CLK_GPIO,0);pio_sm_set_clkdiv(pio0,sm,sonar_pio_divider(clock_get_hz(clk_sys),hz));if(on)pio_sm_set_enabled(pio0,sm,true);}
static void __isr dma_done(void) { dma_hw->ints0 = 1u << dma_chan; pio_sm_set_enabled(pio0,sm,false); completed = active; }
static void configure_pio_dma(void) {
    PIO pio = pio0;
    hard_assert(PDM_CLK_GPIO < 30 && PDM_DATA_GPIO < 30 && PDM_DATA_GPIO+11 < 30);
    uint off = pio_add_program(pio, &pdm_sample_program); sm = pio_claim_unused_sm(pio, true);
    pio_gpio_init(pio, PDM_CLK_GPIO); for (uint i=0;i<12;i++) pio_gpio_init(pio,PDM_DATA_GPIO+i);
    pio_sm_config c=pdm_sample_program_get_default_config(off); sm_config_set_sideset_pins(&c,PDM_CLK_GPIO); sm_config_set_in_pins(&c,PDM_DATA_GPIO);
    sm_config_set_in_shift(&c,false,true,24); sm_config_set_clkdiv(&c,sonar_pio_divider(clock_get_hz(clk_sys),PDM_STANDARD_HZ));
    pio_sm_set_consecutive_pindirs(pio,sm,PDM_CLK_GPIO,1,true); pio_sm_init(pio,sm,off,&c);
    dma_chan=dma_claim_unused_channel(true); discard_chan=dma_claim_unused_channel(true); dma_channel_config d=dma_channel_get_default_config(dma_chan); channel_config_set_transfer_data_size(&d,DMA_SIZE_32); channel_config_set_read_increment(&d,false); channel_config_set_write_increment(&d,true); channel_config_set_dreq(&d,pio_get_dreq(pio,sm,false));
    dma_channel_configure(dma_chan,&d,dma_words[0],&pio->rxf[sm],WINDOW_FRAMES,false); dma_channel_set_irq0_enabled(dma_chan,true); irq_set_exclusive_handler(DMA_IRQ_0,dma_done); irq_set_enabled(DMA_IRQ_0,true);
    channel_config_set_write_increment(&d,false); dma_channel_configure(discard_chan,&d,&discard_word,&pio->rxf[sm],PDM_DISCARD_FRAMES,false);
}
static void arm_capture(void) { active ^= 1; completed=-1; dma_channel_set_write_addr(dma_chan,dma_words[active],false); dma_channel_set_trans_count(dma_chan,WINDOW_FRAMES,false); pio_sm_clear_fifos(pio0,sm); pio_sm_restart(pio0,sm); pio_sm_set_enabled(pio0,sm,true); dma_start_channel_mask(1u<<dma_chan); }
static void discard(uint32_t n){dma_channel_set_trans_count(discard_chan,n,false);dma_channel_set_write_addr(discard_chan,&discard_word,false);dma_start_channel_mask(1u<<discard_chan);dma_channel_wait_for_finish_blocking(discard_chan);pio_sm_clear_fifos(pio0,sm);}
static void startup_mics(void){set_clock(PDM_STANDARD_HZ,true);discard(PDM_STANDARD_FRAMES);set_clock(PDM_STANDARD_HZ,false);sleep_us(2);set_clock(PDM_ULTRASONIC_HZ,true);discard(PDM_DISCARD_FRAMES);set_clock(PDM_ULTRASONIC_HZ,false);logical_frame+=PDM_STANDARD_FRAMES+PDM_DISCARD_FRAMES;}
static void cdc_write_snapshot(const uint8_t *payload, uint32_t frames) {
    sonar_snapshot_header_t h = {.sequence = sequence++, .first_frame = logical_frame,
        .clock_hz = 3072000, .channels = SONAR_CHANNELS, .data_lines = SONAR_DATA_LINES,
        .frame_count = frames, .payload_bytes = frames * SONAR_BYTES_PER_FRAME,
        .payload_crc32 = sonar_crc32(payload, frames * SONAR_BYTES_PER_FRAME)};
    uint8_t header[SONAR_SNAPSHOT_HEADER_BYTES];
    sonar_snapshot_encode_header(header, &h);
    const uint8_t *parts[]={header,payload}; uint32_t sizes[]={sizeof header,h.payload_bytes}; while (!tud_cdc_connected()) tud_task();
    for(int j=0;j<2;j++) for(uint32_t n=0;n<sizes[j];){ tud_task(); uint32_t w=tud_cdc_write(parts[j]+n,sizes[j]-n); n+=w; if(w) tud_cdc_write_flush(); }
}
int main(void) {
    stdio_init_all(); tusb_init(); configure_pio_dma(); startup_mics();
    while (true) { tud_task(); if(tud_cdc_available() && tud_cdc_read_char()=='C' && completed<0){startup_mics();arm_capture();} if(completed>=0){int i=completed; completed=-1; sonar_repack_pio_words(window[i],dma_words[i],WINDOW_FRAMES); cdc_write_snapshot(window[i],WINDOW_FRAMES); logical_frame+=WINDOW_FRAMES;} }
}
