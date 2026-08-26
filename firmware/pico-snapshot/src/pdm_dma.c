#include "snapshot_protocol.h"

/* IN shift-left leaves rising DATA[0..11] in 23:12 and falling DATA[0..11]
 * in 11:0. Conversion stays separate so DMA uses aligned 32-bit writes. */
void sonar_repack_pio_words(uint8_t *out, const uint32_t *words, uint32_t frames) {
    for (uint32_t frame = 0; frame < frames; ++frame) {
        const uint32_t pio_word = words[frame];
        uint32_t packed = 0;
        for (unsigned line = 0; line < SONAR_DATA_LINES; ++line) {
            packed |= ((pio_word >> (12u + line)) & 1u) << (2u * line);
            packed |= ((pio_word >> line) & 1u) << (2u * line + 1u);
        }
        sonar_pack_frame(out + frame * SONAR_BYTES_PER_FRAME, packed);
    }
}
