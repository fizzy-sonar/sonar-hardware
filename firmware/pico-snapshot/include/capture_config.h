#pragma once

#include <stdbool.h>
#include <stdint.h>

#define PDM_STANDARD_HZ 1536000u
#define PDM_ULTRASONIC_HZ 3072000u
#define PDM_STANDARD_MS 50u
#define PDM_SETTLE_MS 10u
#define PDM_STANDARD_FRAMES                                                     \
    ((uint32_t)((uint64_t)PDM_STANDARD_HZ * PDM_STANDARD_MS / 1000u))
#define PDM_SETTLE_FRAMES                                                       \
    ((uint32_t)((uint64_t)PDM_ULTRASONIC_HZ * PDM_SETTLE_MS / 1000u))

/* Two balanced five-cycle half-periods in pdm_capture.pio. */
#define PDM_PIO_CYCLES_PER_FRAME 10u
#define PDM_MAX_CLOCK_ERROR_PPM 400

/* Bench defaults only. T-011's final generic-header map must override these. */
#ifndef PDM_CLK_GPIO
#define PDM_CLK_GPIO 2u
#endif

#ifndef PDM_DATA_GPIO_BASE
#define PDM_DATA_GPIO_BASE 3u
#endif

#define PDM_DATA_LINE_COUNT 12u
#define PICO2_GPIO_COUNT 30u

#if PDM_CLK_GPIO >= PICO2_GPIO_COUNT
#error "PDM_CLK_GPIO must be a Pico 2 GPIO in the range 0..29"
#endif

#if PDM_DATA_GPIO_BASE > (PICO2_GPIO_COUNT - PDM_DATA_LINE_COUNT)
#error "PDM_DATA_GPIO_BASE must leave room for 12 consecutive Pico 2 GPIOs"
#endif

#if (PDM_CLK_GPIO >= PDM_DATA_GPIO_BASE) &&                                    \
    (PDM_CLK_GPIO < (PDM_DATA_GPIO_BASE + PDM_DATA_LINE_COUNT))
#error "PDM_CLK_GPIO must not overlap the 12 PDM data GPIOs"
#endif

typedef struct {
    uint16_t divider_integer;
    uint8_t divider_fraction;
    uint32_t actual_hz;
    int32_t error_ppm;
} sonar_pio_clock_config_t;

/* Quantizes to the RP2350 PIO's actual 16.8 divider representation. */
bool sonar_pio_clock_config(uint32_t sys_hz, uint32_t requested_hz,
                            sonar_pio_clock_config_t *out);
