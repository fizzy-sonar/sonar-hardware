#include <stdbool.h>
#include <stdint.h>

#include "bsp/board_api.h"
#include "hardware/clocks.h"
#include "hardware/dma.h"
#include "hardware/pio.h"
#include "pico/platform.h"
#include "pico/stdlib.h"
#include "tusb.h"

#include "capture_config.h"
#include "cdc_transport.h"
#include "pdm_capture.pio.h"
#include "snapshot_protocol.h"

/* Two one-shot buffers alternate. This is not continuous/chained DMA. */
#define WINDOW_FRAMES 16384u
#define WINDOW_BYTES (WINDOW_FRAMES * SONAR_BYTES_PER_FRAME)

_Static_assert(PDM_DATA_LINE_COUNT == SONAR_DATA_LINES,
               "PIO data-line count must match the SNP1 contract");

static uint32_t dma_words[2][WINDOW_FRAMES] __attribute__((aligned(4)));
static uint8_t packed_windows[2][WINDOW_BYTES] __attribute__((aligned(4)));

static const PIO capture_pio = pio0;
static int capture_dma_channel;
static int discard_dma_channel;
static uint capture_sm;
static uint capture_program_offset;
static pio_sm_config capture_sm_config;
static uint32_t discard_word;

static volatile int completed_buffer = -1;
static volatile bool capture_active;
static int active_buffer;
static int next_buffer;
static uint64_t capture_first_frame[2];
static uint64_t ultrasonic_frame_counter;
static uint32_t capture_sequence;
static sonar_pio_clock_config_t active_clock;

void sonar_repack_pio_words(uint8_t *out, const uint32_t *words,
                            uint32_t frames);

static void stop_clock_low(void) {
    pio_sm_set_enabled(capture_pio, capture_sm, false);
    pio_sm_set_pins_with_mask(capture_pio, capture_sm, 0u,
                              1u << PDM_CLK_GPIO);
}

static void prepare_one_shot(uint32_t requested_hz, uint32_t frames) {
    hard_assert(frames != 0);
    stop_clock_low();

    hard_assert(sonar_pio_clock_config(clock_get_hz(clk_sys), requested_hz,
                                       &active_clock));
    pio_sm_config config = capture_sm_config;
    sm_config_set_clkdiv_int_frac8(&config, active_clock.divider_integer,
                                   active_clock.divider_fraction);
    pio_sm_init(capture_pio, capture_sm, capture_program_offset, &config);
    pio_sm_put_blocking(capture_pio, capture_sm, frames - 1u);
}

static void start_dma_then_sampling(int dma_channel) {
    dma_start_channel_mask(1u << dma_channel);
    pio_sm_set_enabled(capture_pio, capture_sm, true);
}

static void __isr capture_dma_done(void) {
    dma_channel_acknowledge_irq0(capture_dma_channel);
    stop_clock_low();
    __compiler_memory_barrier();
    completed_buffer = active_buffer;
    capture_active = false;
}

static void configure_pio_dma(void) {
    capture_program_offset =
        pio_add_program(capture_pio, &pdm_sample_program);
    capture_sm = pio_claim_unused_sm(capture_pio, true);

    pio_gpio_init(capture_pio, PDM_CLK_GPIO);
    for (uint pin = PDM_DATA_GPIO_BASE;
         pin < PDM_DATA_GPIO_BASE + PDM_DATA_LINE_COUNT; ++pin) {
        pio_gpio_init(capture_pio, pin);
    }

    capture_sm_config =
        pdm_sample_program_get_default_config(capture_program_offset);
    sm_config_set_sideset_pins(&capture_sm_config, PDM_CLK_GPIO);
    sm_config_set_in_pins(&capture_sm_config, PDM_DATA_GPIO_BASE);
    sm_config_set_in_shift(&capture_sm_config, false, true, 24);

    sonar_pio_clock_config_t initial_clock;
    hard_assert(sonar_pio_clock_config(clock_get_hz(clk_sys), PDM_STANDARD_HZ,
                                       &initial_clock));
    sm_config_set_clkdiv_int_frac8(&capture_sm_config,
                                   initial_clock.divider_integer,
                                   initial_clock.divider_fraction);
    pio_sm_init(capture_pio, capture_sm, capture_program_offset,
                &capture_sm_config);
    pio_sm_set_consecutive_pindirs(capture_pio, capture_sm, PDM_CLK_GPIO, 1,
                                   true);
    pio_sm_set_consecutive_pindirs(capture_pio, capture_sm,
                                   PDM_DATA_GPIO_BASE, PDM_DATA_LINE_COUNT,
                                   false);
    stop_clock_low();

    capture_dma_channel = dma_claim_unused_channel(true);
    discard_dma_channel = dma_claim_unused_channel(true);

    dma_channel_config dma_config =
        dma_channel_get_default_config(capture_dma_channel);
    channel_config_set_transfer_data_size(&dma_config, DMA_SIZE_32);
    channel_config_set_read_increment(&dma_config, false);
    channel_config_set_write_increment(&dma_config, true);
    channel_config_set_dreq(
        &dma_config, pio_get_dreq(capture_pio, capture_sm, false));
    dma_channel_configure(capture_dma_channel, &dma_config, dma_words[0],
                          &capture_pio->rxf[capture_sm], WINDOW_FRAMES, false);

    dma_channel_config discard_config =
        dma_channel_get_default_config(discard_dma_channel);
    channel_config_set_transfer_data_size(&discard_config, DMA_SIZE_32);
    channel_config_set_read_increment(&discard_config, false);
    channel_config_set_write_increment(&discard_config, false);
    channel_config_set_dreq(
        &discard_config, pio_get_dreq(capture_pio, capture_sm, false));
    dma_channel_configure(discard_dma_channel, &discard_config, &discard_word,
                          &capture_pio->rxf[capture_sm], PDM_SETTLE_FRAMES,
                          false);

    dma_channel_set_irq0_enabled(capture_dma_channel, true);
    irq_set_exclusive_handler(DMA_IRQ_0, capture_dma_done);
    irq_set_enabled(DMA_IRQ_0, true);
}

static void discard_frames(uint32_t requested_hz, uint32_t frames) {
    hard_assert(!capture_active);
    hard_assert(!dma_channel_is_busy(discard_dma_channel));
    prepare_one_shot(requested_hz, frames);
    dma_channel_set_write_addr(discard_dma_channel, &discard_word, false);
    dma_channel_set_trans_count(discard_dma_channel, frames, false);
    start_dma_then_sampling(discard_dma_channel);
    while (dma_channel_is_busy(discard_dma_channel)) {
        tud_task();
        tight_loop_contents();
    }
    stop_clock_low();
    pio_sm_clear_fifos(capture_pio, capture_sm);
}

static void startup_mics_for_capture(void) {
    /* Standard-mode clocks do not belong to the ultrasonic frame counter. */
    discard_frames(PDM_STANDARD_HZ, PDM_STANDARD_FRAMES);
    sleep_us(2);
    discard_frames(PDM_ULTRASONIC_HZ, PDM_SETTLE_FRAMES);
    ultrasonic_frame_counter += PDM_SETTLE_FRAMES;
}

static void arm_capture(void) {
    hard_assert(!capture_active && completed_buffer < 0);
    active_buffer = next_buffer;
    next_buffer ^= 1;
    capture_first_frame[active_buffer] = ultrasonic_frame_counter;

    prepare_one_shot(PDM_ULTRASONIC_HZ, WINDOW_FRAMES);
    dma_channel_set_write_addr(capture_dma_channel,
                               dma_words[active_buffer], false);
    dma_channel_set_trans_count(capture_dma_channel, WINDOW_FRAMES, false);
    capture_active = true;
    start_dma_then_sampling(capture_dma_channel);
}

static void tinyusb_task(void *context) {
    (void)context;
    tud_task();
}

static bool tinyusb_connected(void *context) {
    (void)context;
    return tud_cdc_connected();
}

static uint32_t tinyusb_write_available(void *context) {
    (void)context;
    return tud_cdc_write_available();
}

static uint32_t tinyusb_write(void *context, const uint8_t *data,
                              uint32_t size) {
    (void)context;
    return tud_cdc_write(data, size);
}

static void tinyusb_flush(void *context) {
    (void)context;
    (void)tud_cdc_write_flush();
}

static const sonar_cdc_io_t tinyusb_cdc = {
    .task = tinyusb_task,
    .connected = tinyusb_connected,
    .write_available = tinyusb_write_available,
    .write = tinyusb_write,
    .flush = tinyusb_flush,
};

static bool cdc_write_snapshot(const uint8_t *payload, uint32_t frames,
                               uint64_t first_frame) {
    sonar_snapshot_header_t header_fields = {
        .sequence = capture_sequence++,
        .first_frame = first_frame,
        .clock_hz = active_clock.actual_hz,
        .channels = SONAR_CHANNELS,
        .data_lines = SONAR_DATA_LINES,
        .frame_count = frames,
        .payload_bytes = frames * SONAR_BYTES_PER_FRAME,
        .payload_crc32 =
            sonar_crc32(payload, frames * SONAR_BYTES_PER_FRAME),
    };
    uint8_t header[SONAR_SNAPSHOT_HEADER_BYTES];
    hard_assert(sonar_snapshot_encode_header(header, &header_fields));
    return sonar_cdc_write_all(&tinyusb_cdc, header, sizeof(header)) &&
           sonar_cdc_write_all(&tinyusb_cdc, payload,
                               header_fields.payload_bytes);
}

static void handle_completed_capture(void) {
    const int buffer = completed_buffer;
    completed_buffer = -1;
    sonar_repack_pio_words(packed_windows[buffer], dma_words[buffer],
                           WINDOW_FRAMES);
    ultrasonic_frame_counter += WINDOW_FRAMES;
    (void)cdc_write_snapshot(packed_windows[buffer], WINDOW_FRAMES,
                             capture_first_frame[buffer]);
}

int main(void) {
    board_init();
    tusb_init();
    configure_pio_dma();

    while (true) {
        tud_task();
        if (completed_buffer >= 0) {
            handle_completed_capture();
            continue;
        }
        if (!capture_active && tud_cdc_available() != 0 &&
            tud_cdc_read_char() == 'C') {
            startup_mics_for_capture();
            arm_capture();
        }
    }
}
