# KUPONG Wi-Fi Clock

Makes an IKEA **KUPONG**, a €1 digital LCD alarm clock, set itself. An **ESP32-C3** gets the exact time over Wi-Fi (NTP) and **presses the clock's SET and + buttons through two optocouplers**, the way a person would. The original display, alarm and case stay as they are. Summer and winter time are handled automatically (Europe/Berlin).

Why not a "real" radio clock? The ESP32 has Wi-Fi and Bluetooth radios but no 77.5 kHz DCF77 receiver. NTP over Wi-Fi needs no extra parts.

> [!IMPORTANT]
> **Status: hardware design documented, firmware not yet adapted.**
> `src/main.cpp` is an early prototype written for an *analog* clock movement (stepper-motor pulses), based on the wrong assumption that the KUPONG is a wall clock. It has never been compiled or tested, and it will be rewritten for button injection. See the hardware doc for the design it will follow.

## Hardware documentation

**→ [docs/kupong-hardware.md](docs/kupong-hardware.md)** covers what's inside the KUPONG, where to tap, wiring, an animated explanation of how a press is injected, the sync procedure, and a checklist for verifying it on your board.

[![How one button press is injected](docs/img/kupong-press-animation.svg)](docs/kupong-hardware.md#how-a-press-is-injected)

## How it works (short)

1. The KUPONG keeps time with its own 32.768 kHz crystal and drifts a few seconds per week.
2. Once a day the ESP32 enters the clock's time-setting menu and steps the hours and minutes with simulated **+** presses. It confirms with the final **SET** exactly on a minute boundary.
3. Optionally the ESP also powers the clock from a 1.5 V regulator, so it can power-cycle it to a known starting display.

## Parts

| Part | Notes |
|---|---|
| IKEA KUPONG | buy a second one as a sacrificial test unit (€1) |
| ESP32-C3 SuperMini | ~€2 on AliExpress, USB-C powered |
| 2× PC817 optocoupler | one per button, isolates the 3.3 V ESP from the 1.5 V clock |
| 2× 1 kΩ resistor | opto LED current, ~2 mA |
| 1.5 V LDO (optional) | e.g. XC6206P152, replaces the AAA so the ESP can reset the clock |
| 30 AWG wire, hot glue, multimeter | thin wire and strain relief for the tiny pads |

## Firmware (to be rewritten)

PlatformIO, Arduino framework, ESP32-C3.

```bash
cp include/secrets.example.h include/secrets.h   # then fill in Wi-Fi SSID/password
pio run -t upload
pio device monitor
```

The Wi-Fi, NTP, timezone, settings-storage and serial-command plumbing in `src/main.cpp` will be reused. The motor driver is replaced by:
- `press(button, ms)`: pulse an optocoupler GPIO.
- A set-time routine following the [sync procedure](docs/kupong-hardware.md#sync-procedure).

On Linux your user needs to be in the `dialout` group to access `/dev/ttyACM0`.

## Ideas for later

- A third optocoupler on the buzzer: detect "alarm ringing" and notify (e.g. Home Assistant).
- Set the KUPONG's alarm remotely through the same two buttons.
- A captive portal (WiFiManager) instead of `secrets.h`.
- DCF77 receiver instead of Wi-Fi, using the same button injection.
