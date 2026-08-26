#include "snapshot_protocol.h"

/* PIO DMA words use bits 0..11 for rising-edge DATA[0..11] and bits 12..23 for
 * falling-edge DATA[0..11]. This conversion is deliberately separate from DMA so
 * the DMA writes aligned 32-bit words while CDC sees compact 3-byte frames. */
void sonar_repack_pio_words(uint8_t *out, const uint32_t *words, uint32_t frames) {
    /* IN shift-left: first/rising 12 bits occupy 23:12; second/falling 11:0. */
    for (uint32_t n = 0; n < frames; ++n) { uint32_t w=words[n], p=0; for(unsigned i=0;i<12;i++) p|=((w>>(12+i))&1u)<<(2*i), p|=((w>>i)&1u)<<(2*i+1); sonar_pack_frame(out+n*3u,p); }
}
