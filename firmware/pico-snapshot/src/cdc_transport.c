#include "cdc_transport.h"

bool sonar_cdc_write_all(const sonar_cdc_io_t *io, const uint8_t *data,
                         size_t size) {
    if (io == NULL || io->task == NULL || io->connected == NULL ||
        io->write_available == NULL || io->write == NULL || io->flush == NULL ||
        (data == NULL && size != 0)) {
        return false;
    }

    size_t offset = 0;
    while (offset < size) {
        io->task(io->context);
        if (!io->connected(io->context)) {
            return false;
        }

        uint32_t request = io->write_available(io->context);
        const size_t remaining = size - offset;
        if (request > remaining) {
            request = (uint32_t)remaining;
        }
        if (request == 0) {
            continue;
        }

        const uint32_t written = io->write(io->context, data + offset, request);
        if (written > request) {
            return false;
        }
        if (written != 0) {
            offset += written;
            io->flush(io->context);
        }
    }
    return true;
}
