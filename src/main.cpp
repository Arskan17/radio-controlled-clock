// KUPONG Wi-Fi clock: an ESP32-C3 drives the clock's Lavet stepper motor
// directly and keeps the hands in sync with NTP time.
//
// Wiring: GPIO_A -- R -- coil -- GPIO_B  (quartz IC disconnected from the coil)
// Serial commands: type "help" in the monitor.

#include <Arduino.h>
#include <WiFi.h>
#include <Preferences.h>
#include <time.h>
#include <esp_sntp.h>
#include "secrets.h"

// ---------- configuration ----------
constexpr int PIN_A = 3;
constexpr int PIN_B = 4;
constexpr uint32_t TWELVE_H = 12UL * 3600UL;              // hand positions on the dial
constexpr const char *TZ_INFO = "CET-1CEST,M3.5.0,M10.5.0/3";  // Europe/Berlin incl. DST
constexpr uint32_t NVS_SAVE_INTERVAL_MS = 30UL * 1000UL;  // ~6 page erases/day: flash-safe
constexpr uint32_t RTC_MAGIC = 0x4B55504F;                // "KUPO"

// ---------- state ----------
// RTC_NOINIT memory survives a soft reset/crash (not a power loss).
RTC_NOINIT_ATTR uint32_t rtcMagic;
RTC_NOINIT_ATTR uint32_t rtcHandPos;
RTC_NOINIT_ATTR uint32_t rtcHandPosCheck;
RTC_NOINIT_ATTR uint8_t rtcPolarity;

Preferences prefs;

uint32_t handPos = 0;        // seconds past 12:00:00 the hands currently show
uint8_t polarity = 0;        // polarity of the NEXT pulse; a Lavet motor needs alternation
bool autoRun = true;         // false = hold (manual testing)
uint16_t pulseWidthMs = 30;  // coil on-time per step
uint16_t fastIntervalMs = 80;  // minimum time between steps while catching up
uint32_t lastPulseMs = 0;
uint32_t lastNvsSaveMs = 0;
uint32_t lastSavedPos = UINT32_MAX;
volatile time_t lastSyncEpoch = 0;

enum class State { NoTime, Hold, Synced, CatchingUp, Waiting };
State state = State::NoTime;

// ---------- persistence ----------
void saveRtc() {
  rtcMagic = RTC_MAGIC;
  rtcHandPos = handPos;
  rtcHandPosCheck = ~handPos;
  rtcPolarity = polarity;
}

void saveNvs() {
  prefs.putUInt("pos", handPos);
  prefs.putUChar("pol", polarity);
  lastSavedPos = handPos;
  lastNvsSaveMs = millis();
}

void loadState() {
  prefs.begin("clock", false);
  pulseWidthMs = prefs.getUShort("width", pulseWidthMs);
  fastIntervalMs = prefs.getUShort("speed", fastIntervalMs);

  if (rtcMagic == RTC_MAGIC && rtcHandPosCheck == ~rtcHandPos && rtcHandPos < TWELVE_H) {
    handPos = rtcHandPos;
    polarity = rtcPolarity & 1;
    Serial.println("[boot] hand position restored from RTC memory (soft reset)");
  } else if (prefs.isKey("pos")) {
    handPos = prefs.getUInt("pos", 0) % TWELVE_H;
    polarity = prefs.getUChar("pol", 0) & 1;
    Serial.println("[boot] hand position restored from flash (may be up to 30 s stale; "
                   "use 'set' if the hands disagree)");
  } else {
    autoRun = false;
    Serial.println("[boot] hand position UNKNOWN - holding. Use 'set HH:MM:SS' "
                   "with the time the hands show, then 'run'.");
  }
  saveRtc();
}

// ---------- motor ----------
void pulse() {
  const int pin = polarity ? PIN_B : PIN_A;
  digitalWrite(pin, HIGH);
  delay(pulseWidthMs);
  digitalWrite(pin, LOW);
  polarity ^= 1;
  handPos = (handPos + 1) % TWELVE_H;
  lastPulseMs = millis();
  saveRtc();
}

// ---------- time ----------
bool timeValid() { return lastSyncEpoch != 0; }

void onTimeSync(struct timeval *tv) { lastSyncEpoch = tv->tv_sec; }

uint32_t targetPos() {
  time_t now = time(nullptr);
  struct tm t;
  localtime_r(&now, &t);
  return (t.tm_hour % 12) * 3600UL + t.tm_min * 60UL + t.tm_sec;
}

String fmtPos(uint32_t p) {
  char buf[12];
  snprintf(buf, sizeof buf, "%02lu:%02lu:%02lu", (unsigned long)(p / 3600 == 0 ? 12 : p / 3600),
           (unsigned long)(p / 60 % 60), (unsigned long)(p % 60));
  return String(buf);
}

const char *stateName(State s) {
  switch (s) {
    case State::NoTime: return "waiting for NTP";
    case State::Hold: return "HOLD (manual)";
    case State::Synced: return "synced";
    case State::CatchingUp: return "catching up";
    case State::Waiting: return "waiting for time to catch up with hands";
  }
  return "?";
}

void setState(State s) {
  if (s == state) return;
  state = s;
  Serial.printf("[state] %s  (hands %s, time %s)\n", stateName(s), fmtPos(handPos).c_str(),
                timeValid() ? fmtPos(targetPos()).c_str() : "--:--:--");
}

// ---------- serial commands ----------
void printStatus() {
  time_t now = time(nullptr);
  struct tm t;
  localtime_r(&now, &t);
  char clock[32];
  strftime(clock, sizeof clock, "%Y-%m-%d %H:%M:%S %Z", &t);
  Serial.printf("time:     %s%s\n", clock, timeValid() ? "" : "  (NOT synced)");
  Serial.printf("hands:    %s  (pos %lu, next polarity %u)\n", fmtPos(handPos).c_str(),
                (unsigned long)handPos, polarity);
  Serial.printf("state:    %s\n", stateName(state));
  Serial.printf("wifi:     %s  %s  RSSI %d\n", WiFi.isConnected() ? "connected" : "DISCONNECTED",
                WiFi.localIP().toString().c_str(), WiFi.RSSI());
  if (timeValid()) {
    Serial.printf("ntp:      last sync %ld s ago\n", (long)(now - lastSyncEpoch));
  }
  Serial.printf("width:    %u ms   speed: %u ms/step\n", pulseWidthMs, fastIntervalMs);
}

void printHelp() {
  Serial.println(
      "commands:\n"
      "  set HH:MM:SS  tell the clock where the hands point now (12h dial)\n"
      "  status        show time, hand position, Wi-Fi, NTP\n"
      "  hold | run    stop / resume automatic stepping\n"
      "  pulse N       step N times now (for motor tests; best in hold)\n"
      "  flip          invert next pulse polarity (if one step was missed)\n"
      "  width MS      coil pulse width, 5..100 (saved)\n"
      "  speed MS      catch-up step interval, 30..500 (saved)\n"
      "  help");
}

void handleCommand(String line) {
  line.trim();
  if (line.isEmpty()) return;
  int sp = line.indexOf(' ');
  String cmd = sp < 0 ? line : line.substring(0, sp);
  String arg = sp < 0 ? "" : line.substring(sp + 1);
  cmd.toLowerCase();
  arg.trim();

  if (cmd == "set") {
    unsigned h, m, s;
    if (sscanf(arg.c_str(), "%u:%u:%u", &h, &m, &s) == 3 && h <= 24 && m < 60 && s < 60) {
      handPos = ((h % 12) * 3600UL + m * 60UL + s) % TWELVE_H;
      saveRtc();
      saveNvs();
      Serial.printf("hands set to %s\n", fmtPos(handPos).c_str());
    } else {
      Serial.println("usage: set HH:MM:SS");
    }
  } else if (cmd == "status") {
    printStatus();
  } else if (cmd == "hold") {
    autoRun = false;
    saveNvs();
  } else if (cmd == "run") {
    autoRun = true;
  } else if (cmd == "pulse") {
    long n = arg.toInt();
    if (n < 1 || n > 43200) {
      Serial.println("usage: pulse N  (1..43200)");
      return;
    }
    for (long i = 0; i < n; i++) {
      pulse();
      if (i + 1 < n) delay(fastIntervalMs - pulseWidthMs);
    }
    saveNvs();
    Serial.printf("%ld pulses, hands now %s\n", n, fmtPos(handPos).c_str());
  } else if (cmd == "flip") {
    polarity ^= 1;
    saveRtc();
    Serial.printf("next polarity now %u\n", polarity);
  } else if (cmd == "width") {
    long v = arg.toInt();
    if (v >= 5 && v <= 100 && v + 20 <= fastIntervalMs) {
      pulseWidthMs = v;
      prefs.putUShort("width", pulseWidthMs);
      Serial.printf("width = %u ms\n", pulseWidthMs);
    } else {
      Serial.println("usage: width MS  (5..100, and at least 20 ms below speed)");
    }
  } else if (cmd == "speed") {
    long v = arg.toInt();
    if (v >= 30 && v <= 500 && v >= pulseWidthMs + 20) {
      fastIntervalMs = v;
      prefs.putUShort("speed", fastIntervalMs);
      Serial.printf("speed = %u ms/step\n", fastIntervalMs);
    } else {
      Serial.println("usage: speed MS  (30..500, and at least 20 ms above width)");
    }
  } else if (cmd == "help") {
    printHelp();
  } else {
    Serial.println("unknown command, try 'help'");
  }
}

void pollSerial() {
  static String buf;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      handleCommand(buf);
      buf = "";
    } else if (buf.length() < 64) {
      buf += c;
    }
  }
}

// ---------- main ----------
void setup() {
  pinMode(PIN_A, OUTPUT);
  pinMode(PIN_B, OUTPUT);
  digitalWrite(PIN_A, LOW);
  digitalWrite(PIN_B, LOW);

  Serial.begin(115200);
  delay(1500);  // give USB CDC a moment so boot messages are visible
  Serial.println("\nKUPONG Wi-Fi clock - type 'help'");

  loadState();

  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  sntp_set_time_sync_notification_cb(onTimeSync);
  configTzTime(TZ_INFO, "de.pool.ntp.org", "pool.ntp.org");  // re-syncs hourly by default
}

void loop() {
  pollSerial();

  static bool wasConnected = false;
  if (WiFi.isConnected() != wasConnected) {
    wasConnected = WiFi.isConnected();
    Serial.printf("[wifi] %s %s\n", wasConnected ? "connected," : "disconnected",
                  wasConnected ? WiFi.localIP().toString().c_str() : "");
  }

  if (!timeValid()) {
    setState(State::NoTime);
  } else if (!autoRun) {
    setState(State::Hold);
  } else {
    const uint32_t behind = (targetPos() + TWELVE_H - handPos) % TWELVE_H;  // steps needed
    if (behind == 0) {
      setState(State::Synced);
    } else {
      // Either step forward fast, or stop and let real time catch up with the
      // hands (e.g. DST fall-back). Pick whichever finishes sooner.
      const float gainPerSec = 1000.0f / fastIntervalMs - 1.0f;
      const float stepSeconds = behind / gainPerSec;
      const uint32_t waitSeconds = TWELVE_H - behind;
      if (stepSeconds <= waitSeconds) {
        setState(behind > 2 ? State::CatchingUp : State::Synced);
        if (millis() - lastPulseMs >= fastIntervalMs) pulse();
      } else {
        setState(State::Waiting);
      }
    }
  }

  if (handPos != lastSavedPos && millis() - lastNvsSaveMs >= NVS_SAVE_INTERVAL_MS) saveNvs();

  delay(2);
}
