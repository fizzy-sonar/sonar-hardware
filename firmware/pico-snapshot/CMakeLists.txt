cmake_minimum_required(VERSION 3.13)
include(pico_sdk_import.cmake)
project(sonar_pico_snapshot C CXX ASM)
pico_sdk_init()

add_executable(
    sonar_pico_snapshot
    src/capture_core.c
    src/cdc_transport.c
    src/main.c
    src/pdm_dma.c
    src/snapshot_protocol.c
    src/usb_descriptors.c
)
pico_generate_pio_header(sonar_pico_snapshot ${CMAKE_CURRENT_LIST_DIR}/pio/pdm_capture.pio)
target_include_directories(sonar_pico_snapshot PRIVATE include)
target_compile_features(sonar_pico_snapshot PRIVATE c_std_11)
target_compile_options(sonar_pico_snapshot PRIVATE -Wall -Wextra -Werror)
target_link_libraries(
    sonar_pico_snapshot
    hardware_clocks
    hardware_dma
    hardware_pio
    pico_stdlib
    tinyusb_board
    tinyusb_device
)
pico_add_extra_outputs(sonar_pico_snapshot)
