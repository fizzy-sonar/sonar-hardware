#pragma once
#include <stdint.h>
#define PDM_STANDARD_HZ 1536000u
#define PDM_ULTRASONIC_HZ 3072000u
#define PDM_STANDARD_MS 50u
#define PDM_SETTLE_MS 10u
#define PDM_DISCARD_FRAMES ((uint32_t)((uint64_t)PDM_ULTRASONIC_HZ*PDM_SETTLE_MS/1000u))
/* pdm_sample loop is six SM cycles: nop[1], in, nop[1], in. */
#define PDM_PIO_CYCLES_PER_FRAME 6u
static inline float sonar_pio_divider(uint32_t sys_hz,uint32_t pdm_hz){return (float)sys_hz/(PDM_PIO_CYCLES_PER_FRAME*pdm_hz);}
