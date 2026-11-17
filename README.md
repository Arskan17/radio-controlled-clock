# KUPONG Wi-Fi Clock

Turns an IKEA **KUPONG** wall clock into a self-setting clock. An **ESP32-C3** replaces the quartz chip, drives the clock's stepper motor directly, and keeps the hands in sync with internet time (NTP) over Wi-Fi. Summer and winter time are handled automatically (Europe/Berlin).

Why not a "real" radio clock? The ESP32 has Wi-Fi and Bluetooth radios but no 77.5 kHz DCF77 receiver. NTP over Wi-Fi needs no extra parts.

> **Status:** prototype. The firmware is written but has **not been compiled or tested on hardware yet**.

## How it works

- A quartz clock movement is a *Lavet stepper motor*: one coil, and each pulse of **alternating polarity** advances the second hand one tick.
- The ESP32 pulses the coil from two GPIOs, once per second when in sync.
- It tracks where the hands are (`handPos` = seconds past 12:00:00 on the 12 h dial) and compares that with NTP time:
  - **Hands behind:** steps fast (default 80 ms/step) until caught up.
  - **Hands ahead** (e.g. autumn DST change): pauses until real time catches up.
  - It picks whichever option finishes sooner.
- The hand position survives a reboot (RTC memory) and a power loss (flash, saved every 30 s, so after a power cut it can be up to 30 s off; fix with `set`).
- NTP re-syncs hourly.

## Parts

| Part | Notes |
|---|---|
| ESP32-C3 SuperMini | ~€2 on AliExpress; buy a spare |
| IKEA KUPONG | buy a second one as a sacrificial test unit |
| Resistor(s) 220–470 Ω | to limit coil current, see below |
| 2× 1N4148 (optional) | flyback protection |
| Wire, USB-C cable, multimeter | |

## Hardware

1. Open the KUPONG movement. Find the coil (fine copper winding) and its two pads on the PCB.
2. Measure the coil resistance (expect roughly 150–300 Ω).
3. Cut the PCB traces between the quartz IC and the coil. Solder two wires to the coil pads.
4. Wire it up:

```
ESP32-C3                              KUPONG coil
GPIO 3 ──[ R ]──────────────┐
                           ( coil )
GPIO 4 ─────────────────────┘
GND, USB-C 5 V: power from USB
```

Pick **R ≈ 1.2 × coil resistance**, so the coil sees about the same current as with the original 1.5 V battery (3.3 V across R + coil). Avoid GPIO 2, 8 and 9 (strapping pins).

## Firmware

PlatformIO, Arduino framework.

```bash
cp include/secrets.example.h include/secrets.h   # then fill in Wi-Fi SSID/password
pio run -t upload
pio device monitor
```

On Linux your user needs to be in the `dialout` group to access `/dev/ttyACM0`.

### Serial commands

| Command | Effect |
|---|---|
| `set HH:MM:SS` | Tell the clock where the hands point right now (12 h dial) |
| `status` | Time, hand position, state, Wi-Fi, last NTP sync |
| `hold` / `run` | Stop / resume automatic stepping |
| `pulse N` | Step N times now (motor tests, best in `hold`) |
| `flip` | Invert the next pulse polarity (if a step was missed) |
| `width MS` | Coil pulse width, 5–100 ms (saved) |
| `speed MS` | Catch-up step interval, 30–500 ms (saved) |
| `help` | List commands |

On first boot the hand position is unknown, so the clock **holds**. Run `set` with what the hands show, then `run`.

## Bring-up checklist

1. **No clock:** flash, watch the monitor for Wi-Fi, NTP and state messages. An LED + resistor on each GPIO shows the alternating pulses.
2. **Motor on the spare KUPONG:** `hold`, then `pulse 10`. The second hand should move exactly 10 ticks. Tune `width` (shortest reliable) and `speed` (fastest reliable).
3. **Sync:** `set` the real hand position, `run`, compare with a phone after 1 h and 24 h.
4. **Edge cases:** reboot, unplug power, test DST by temporarily changing `TZ_INFO` in `src/main.cpp`.

## Ideas for later

- **Battery operation:** the ULP coprocessor steps the motor in deep sleep and Wi-Fi syncs once a day. Expect months, not a year, on batteries.
- **Automatic homing:** a Hall sensor + small magnet on the minute hand.
- **Setup without code changes:** a captive portal (WiFiManager) instead of `secrets.h`, and a small web page instead of serial commands.
