#include <stddef.h>
#include <string.h>

#include "tusb.h"

enum {
    STRING_LANGUAGE = 0,
    STRING_MANUFACTURER,
    STRING_PRODUCT,
    STRING_SERIAL,
    STRING_CDC,
};

static const tusb_desc_device_t device_descriptor = {
    .bLength = sizeof(tusb_desc_device_t),
    .bDescriptorType = TUSB_DESC_DEVICE,
    .bcdUSB = 0x0200,
    .bDeviceClass = TUSB_CLASS_MISC,
    .bDeviceSubClass = MISC_SUBCLASS_COMMON,
    .bDeviceProtocol = MISC_PROTOCOL_IAD,
    .bMaxPacketSize0 = CFG_TUD_ENDPOINT0_SIZE,
    /* TinyUSB's development VID/PID range; replace before product release. */
    .idVendor = 0xcafe,
    .idProduct = 0x4011,
    .bcdDevice = 0x0100,
    .iManufacturer = STRING_MANUFACTURER,
    .iProduct = STRING_PRODUCT,
    .iSerialNumber = STRING_SERIAL,
    .bNumConfigurations = 1,
};

enum {
    INTERFACE_CDC_CONTROL = 0,
    INTERFACE_CDC_DATA,
    INTERFACE_COUNT,
};

#define CONFIGURATION_LENGTH (TUD_CONFIG_DESC_LEN + TUD_CDC_DESC_LEN)
#define ENDPOINT_CDC_NOTIFICATION 0x81
#define ENDPOINT_CDC_OUT 0x02
#define ENDPOINT_CDC_IN 0x82

static const uint8_t configuration_descriptor[] = {
    TUD_CONFIG_DESCRIPTOR(1, INTERFACE_COUNT, 0, CONFIGURATION_LENGTH, 0x00,
                          100),
    TUD_CDC_DESCRIPTOR(INTERFACE_CDC_CONTROL, STRING_CDC,
                       ENDPOINT_CDC_NOTIFICATION, 8, ENDPOINT_CDC_OUT,
                       ENDPOINT_CDC_IN, 64),
};

static const char *const string_descriptors[] = {
    [STRING_MANUFACTURER] = "Sonar",
    [STRING_PRODUCT] = "Pico 2 PDM Snapshot",
    [STRING_SERIAL] = "T009-DEV",
    [STRING_CDC] = "SNP1 capture",
};

const uint8_t *tud_descriptor_device_cb(void) {
    return (const uint8_t *)&device_descriptor;
}

const uint8_t *tud_descriptor_configuration_cb(uint8_t index) {
    (void)index;
    return configuration_descriptor;
}

const uint16_t *tud_descriptor_string_cb(uint8_t index, uint16_t language_id) {
    (void)language_id;
    static uint16_t descriptor[32];
    size_t character_count;

    if (index == STRING_LANGUAGE) {
        descriptor[1] = 0x0409;
        character_count = 1;
    } else {
        if (index >= sizeof(string_descriptors) / sizeof(string_descriptors[0]) ||
            string_descriptors[index] == NULL) {
            return NULL;
        }
        character_count = strlen(string_descriptors[index]);
        if (character_count > 31) {
            character_count = 31;
        }
        for (size_t i = 0; i < character_count; ++i) {
            descriptor[1 + i] = (uint8_t)string_descriptors[index][i];
        }
    }

    descriptor[0] =
        (uint16_t)((TUSB_DESC_STRING << 8) | (2 * character_count + 2));
    return descriptor;
}
