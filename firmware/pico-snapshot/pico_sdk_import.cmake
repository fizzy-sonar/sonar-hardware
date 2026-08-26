# Minimal offline Pico SDK import: dependency acquisition is intentionally not done
# by this repository. Point PICO_SDK_PATH at an RP2350-capable checked-out SDK.
if (NOT PICO_SDK_PATH AND DEFINED ENV{PICO_SDK_PATH})
    set(PICO_SDK_PATH "$ENV{PICO_SDK_PATH}")
endif()
if (NOT PICO_SDK_PATH OR NOT EXISTS "${PICO_SDK_PATH}/pico_sdk_init.cmake")
    message(FATAL_ERROR "Set PICO_SDK_PATH to an RP2350-capable Pico SDK checkout")
endif()
include("${PICO_SDK_PATH}/pico_sdk_init.cmake")
