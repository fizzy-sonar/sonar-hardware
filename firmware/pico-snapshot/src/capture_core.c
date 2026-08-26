#include "snapshot_protocol.h"

/* Hardware-independent DMA-window finalizer. PIO/DMA writes exactly 3 bytes/frame. */
bool sonar_capture_window_valid(const uint8_t *payload, uint32_t frames) {
    return payload != NULL && frames != 0 && frames <= UINT32_MAX / SONAR_BYTES_PER_FRAME;
}
