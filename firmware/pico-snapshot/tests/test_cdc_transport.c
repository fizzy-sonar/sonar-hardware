#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "cdc_transport.h"

typedef struct {
    uint8_t output[64];
    uint32_t output_size;
    unsigned task_calls;
    unsigned available_calls;
    unsigned write_calls;
    bool connected;
    bool return_zero_once;
    bool overreport;
} fake_cdc_t;

static void fake_task(void *context) {
    fake_cdc_t *fake = context;
    ++fake->task_calls;
}

static bool fake_connected(void *context) {
    return ((fake_cdc_t *)context)->connected;
}

static uint32_t fake_available(void *context) {
    fake_cdc_t *fake = context;
    ++fake->available_calls;
    return fake->available_calls <= 2 ? 0u : 4u;
}

static uint32_t fake_write(void *context, const uint8_t *data, uint32_t size) {
    fake_cdc_t *fake = context;
    ++fake->write_calls;
    if (fake->overreport) {
        return size + 1u;
    }
    if (fake->return_zero_once) {
        fake->return_zero_once = false;
        return 0;
    }
    const uint32_t written = size > 3u ? 3u : size;
    memcpy(fake->output + fake->output_size, data, written);
    fake->output_size += written;
    return written;
}

static void fake_flush(void *context) {
    (void)context;
}

static sonar_cdc_io_t make_io(fake_cdc_t *fake) {
    const sonar_cdc_io_t io = {
        .context = fake,
        .task = fake_task,
        .connected = fake_connected,
        .write_available = fake_available,
        .write = fake_write,
        .flush = fake_flush,
    };
    return io;
}

int main(void) {
    const uint8_t input[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
    fake_cdc_t fake = {.connected = true, .return_zero_once = true};
    sonar_cdc_io_t io = make_io(&fake);
    assert(sonar_cdc_write_all(&io, input, sizeof(input)));
    assert(fake.task_calls >= 7);
    assert(fake.write_calls >= 5);
    assert(fake.output_size == sizeof(input));
    assert(memcmp(fake.output, input, sizeof(input)) == 0);

    fake_cdc_t disconnected = {0};
    io = make_io(&disconnected);
    assert(!sonar_cdc_write_all(&io, input, sizeof(input)));
    assert(disconnected.task_calls == 1);

    fake_cdc_t invalid_writer = {.connected = true, .overreport = true};
    io = make_io(&invalid_writer);
    assert(!sonar_cdc_write_all(&io, input, sizeof(input)));
    assert(sonar_cdc_write_all(&io, NULL, 0));
    assert(!sonar_cdc_write_all(NULL, input, sizeof(input)));
    return 0;
}
