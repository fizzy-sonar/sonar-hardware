#include "capture_config.h"

#include <stddef.h>

static int32_t divide_round_nearest(int64_t numerator, int64_t denominator) {
    if (numerator < 0) {
        return (int32_t)-((-numerator + denominator / 2) / denominator);
    }
    return (int32_t)((numerator + denominator / 2) / denominator);
}

bool sonar_pio_clock_config(uint32_t sys_hz, uint32_t requested_hz,
                            sonar_pio_clock_config_t *out) {
    if (sys_hz == 0 || requested_hz == 0 || out == NULL) {
        return false;
    }

    const uint64_t requested_denominator =
        (uint64_t)PDM_PIO_CYCLES_PER_FRAME * requested_hz;
    const uint64_t scaled_system_hz = (uint64_t)sys_hz * 256u;
    const uint64_t divider256 =
        (scaled_system_hz + requested_denominator / 2u) /
        requested_denominator;

    /* Integer zero has special hardware meaning; it is never useful here. */
    if (divider256 < 256u || divider256 > 0xffffffu) {
        return false;
    }

    const uint64_t actual_denominator =
        (uint64_t)PDM_PIO_CYCLES_PER_FRAME * divider256;
    const uint64_t ppm_denominator = requested_hz * actual_denominator;
    const int64_t ppm_numerator =
        (int64_t)scaled_system_hz -
        (int64_t)(requested_hz * actual_denominator);
    const int32_t error_ppm = divide_round_nearest(
        ppm_numerator * 1000000ll, (int64_t)ppm_denominator);

    out->divider_integer = (uint16_t)(divider256 >> 8u);
    out->divider_fraction = (uint8_t)divider256;
    out->actual_hz =
        (uint32_t)((scaled_system_hz + actual_denominator / 2u) /
                   actual_denominator);
    out->error_ppm = error_ppm;
    return error_ppm >= -PDM_MAX_CLOCK_ERROR_PPM &&
           error_ppm <= PDM_MAX_CLOCK_ERROR_PPM;
}
