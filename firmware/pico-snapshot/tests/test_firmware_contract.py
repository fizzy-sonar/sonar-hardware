from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def instruction_cycles(line: str) -> int:
    delay = re.search(r"\[(\d+)]", line)
    return 1 + (int(delay.group(1)) if delay else 0)


def test_pio_timing() -> None:
    source = (ROOT / "pio/pdm_capture.pio").read_text()
    frame = source.split("frame:\n", 1)[1].split("\n.wrap", 1)[0]
    instructions = [
        line.strip()
        for line in frame.splitlines()
        if line.strip() and not line.lstrip().startswith(";")
    ]
    assert instructions == [
        "nop side 1 [1]",
        "in pins, 12 side 1 [2]",
        "nop side 0 [1]",
        "in pins, 12 side 0",
        "jmp x-- frame side 0 [1]",
    ]
    high = sum(instruction_cycles(line) for line in instructions if "side 1" in line)
    low = sum(instruction_cycles(line) for line in instructions if "side 0" in line)
    assert high == low == 5
    assert sum(map(instruction_cycles, instructions)) == 10


def compile_pin_configuration(*definitions: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as temporary_directory:
        source = Path(temporary_directory) / "pins.c"
        source.write_text('#include "capture_config.h"\nint main(void) { return 0; }\n')
        return subprocess.run(
            [
                "cc",
                "-std=c11",
                "-fsyntax-only",
                f"-I{ROOT / 'include'}",
                *definitions,
                str(source),
            ],
            check=False,
            capture_output=True,
            text=True,
        )


def test_pin_guards() -> None:
    assert compile_pin_configuration().returncode == 0
    assert compile_pin_configuration("-DPDM_CLK_GPIO=20").returncode == 0
    assert compile_pin_configuration("-DPDM_DATA_GPIO_BASE=10").returncode == 0
    assert compile_pin_configuration("-DPDM_CLK_GPIO=30").returncode != 0
    assert compile_pin_configuration("-DPDM_DATA_GPIO_BASE=19").returncode != 0
    assert (
        compile_pin_configuration(
            "-DPDM_CLK_GPIO=7", "-DPDM_DATA_GPIO_BASE=3"
        ).returncode
        != 0
    )
    assert (
        compile_pin_configuration(
            "-DPDM_CLK_GPIO=20", "-DPDM_DATA_GPIO_BASE=3"
        ).returncode
        == 0
    )


def test_firmware_ordering_and_usb_ownership() -> None:
    main = (ROOT / "src/main.c").read_text()
    cmake = (ROOT / "CMakeLists.txt").read_text()
    tinyusb_config = (ROOT / "include/tusb_config.h").read_text()
    descriptors = (ROOT / "src/usb_descriptors.c").read_text()

    assert "stdio_init_all" not in main
    assert "pico_enable_stdio_usb" not in cmake
    assert "board_init();" in main and "tusb_init();" in main
    assert "tud_task();" in main
    assert "#define CFG_TUD_CDC 1" in tinyusb_config
    assert "tud_descriptor_device_cb" in descriptors
    assert "tud_descriptor_configuration_cb" in descriptors
    assert "tud_descriptor_string_cb" in descriptors
    assert "hardware/clocks.h" in main
    assert "gpio_put" not in main
    assert "pio_sm_set_pins_with_mask" in main
    assert "PDM_DATA_LINE_COUNT,\n                                   false" in main
    assert "dma_channel_get_default_config(discard_dma_channel)" in main

    start = main.split("static void start_dma_then_sampling", 1)[1].split("}\n", 1)[0]
    assert start.index("dma_start_channel_mask") < start.index("pio_sm_set_enabled")
    irq = main.split("static void __isr capture_dma_done", 1)[1].split("}\n", 1)[0]
    assert "dma_channel_acknowledge_irq0" in irq
    assert "stop_clock_low();" in irq
    assert "__compiler_memory_barrier();" in irq
    assert "completed_buffer = active_buffer;" in irq
    assert "capture_active = false;" in irq
    main_function = main.split("int main(void)", 1)[1]
    assert main_function.count("startup_mics_for_capture();") == 1
    assert main_function.index("tud_cdc_read_char() == 'C'") < main_function.index(
        "startup_mics_for_capture();"
    )

    startup = main.split("static void startup_mics_for_capture", 1)[1].split("}\n", 1)[
        0
    ]
    assert startup.index("PDM_STANDARD_FRAMES") < startup.index("PDM_SETTLE_FRAMES")
    assert "ultrasonic_frame_counter += PDM_SETTLE_FRAMES" in startup
    assert (
        "PDM_STANDARD_FRAMES" not in startup.split("ultrasonic_frame_counter +=", 1)[1]
    )


def main() -> None:
    test_pio_timing()
    test_pin_guards()
    test_firmware_ordering_and_usb_ownership()


if __name__ == "__main__":
    main()
