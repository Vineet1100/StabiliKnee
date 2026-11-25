// StabiliKnee - MakeUofT 2026 (3rd place). Rebuilt Nov 2026 after the original files were lost.
// Tightens a knee brace when a small neural network (model.h) flags a risky movement.
// Until model.h is trained, it falls back to a plain gyro threshold.

#include <Wire.h>
#include <Servo.h>
#include <math.h>
#include "model.h"

const int SERVO_PIN = 9;
const int FLEX_PIN = A0;          // 5V -> flex sensor -> A0 -> 10k -> GND

// ITG-3200 gyroscope
const byte GYRO_ADDR = 0x68;
const byte REG_PWR_MGM = 0x3E;
const byte REG_DLPF_FS = 0x16;
const byte REG_GYRO_XOUT_H = 0x1D;
const float GYRO_SCALE = 14.375f; // raw units per deg/s

const int CALIBRATION_SAMPLES = 1500;
const unsigned long LOOP_MS = 20;

// Thresholds on smoothed rotation speed (deg/s).
// Two thresholds (hysteresis) stop the brace flickering near one value.
const float RISK_ON = 80.0f;
const float RISK_OFF = 25.0f;
const unsigned long HOLD_MS = 700;     // stay tight at least this long after a risky reading
const unsigned long RELEASE_MS = 1000; // must be calm this long before releasing
const float EMA_ALPHA = 0.25f;         // smoothing: higher = reacts faster, noisier

const int SERVO_RELAX = 180;
const int SERVO_TIGHT = 0;

Servo brace;
float offsetX = 0, offsetY = 0, offsetZ = 0;
int flexBaseline = 0;

void writeRegister(byte reg, byte value) {
  Wire.beginTransmission(GYRO_ADDR);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

bool readGyro(int16_t &x, int16_t &y, int16_t &z) {
  Wire.beginTransmission(GYRO_ADDR);
  Wire.write(REG_GYRO_XOUT_H);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(GYRO_ADDR, (byte)6, (byte)true) != 6) return false;
  x = (Wire.read() << 8) | Wire.read();
  y = (Wire.read() << 8) | Wire.read();
  z = (Wire.read() << 8) | Wire.read();
  return true;
}

// Keep the leg still: averages resting readings to remove gyro drift.
void calibrate() {
  long sx = 0, sy = 0, sz = 0;
  int n = 0;
  for (int i = 0; i < CALIBRATION_SAMPLES; i++) {
    int16_t x, y, z;
    if (readGyro(x, y, z)) { sx += x; sy += y; sz += z; n++; }
    delay(10);
  }
  if (n > 0) { offsetX = (float)sx / n; offsetY = (float)sy / n; offsetZ = (float)sz / n; }
  delay(1000);
  flexBaseline = analogRead(FLEX_PIN); // leg straight
}

#if MODEL_READY
// Forward pass of the trained network: 3 inputs -> HIDDEN ReLU units -> 1 sigmoid output.
float riskProbability(float mag, float jerk, float flex) {
  float in[3] = {mag, jerk, flex};
  for (int i = 0; i < 3; i++) in[i] = (in[i] - FEAT_MEAN[i]) / FEAT_STD[i];
  float out = B2;
  for (int h = 0; h < HIDDEN; h++) {
    float a = B1[h];
    for (int i = 0; i < 3; i++) a += in[i] * W1[i * HIDDEN + h];
    if (a > 0) out += a * W2[h];
  }
  return 1.0f / (1.0f + expf(-out));
}
#endif

void setup() {
  Serial.begin(115200);
  Wire.begin();
  brace.attach(SERVO_PIN);
  brace.write(SERVO_RELAX);

  writeRegister(REG_PWR_MGM, 0x00);
  delay(50);
  writeRegister(REG_DLPF_FS, 0x18); // full-scale range
  delay(50);

  calibrate();
  Serial.println("ms,mag_raw,mag_ema,flex,tight"); // CSV header read by extension/log_serial.py
}

void loop() {
  static float magEma = 0, prevMag = 0;
  static bool tight = false;
  static unsigned long lastRiskMs = 0, calmStartMs = 0;

  int16_t rx, ry, rz;
  if (!readGyro(rx, ry, rz)) { delay(LOOP_MS); return; }

  float gx = (rx - offsetX) / GYRO_SCALE;
  float gy = (ry - offsetY) / GYRO_SCALE;
  float gz = (rz - offsetZ) / GYRO_SCALE;
  float mag = sqrtf(gx * gx + gy * gy + gz * gz);
  magEma = EMA_ALPHA * mag + (1 - EMA_ALPHA) * magEma;

  int flex = analogRead(FLEX_PIN) - flexBaseline;
  float jerk = (mag - prevMag) / (LOOP_MS / 1000.0f);
  prevMag = mag;

#if MODEL_READY
  bool risky = riskProbability(mag, jerk, flex / 1023.0f) > 0.5f;
#else
  bool risky = magEma > RISK_ON;
#endif

  unsigned long now = millis();
  if (risky) { lastRiskMs = now; calmStartMs = 0; }

  bool shouldTighten;
  if (now - lastRiskMs < HOLD_MS) {
    shouldTighten = true;
  } else if (magEma < RISK_OFF) {
    if (calmStartMs == 0) calmStartMs = now;
    shouldTighten = (now - calmStartMs < RELEASE_MS);
  } else {
    calmStartMs = 0;
    shouldTighten = tight; // between thresholds: keep current state
  }

  if (shouldTighten != tight) {
    tight = shouldTighten;
    brace.write(tight ? SERVO_TIGHT : SERVO_RELAX);
  }

  Serial.print(now); Serial.print(',');
  Serial.print(mag, 1); Serial.print(',');
  Serial.print(magEma, 1); Serial.print(',');
  Serial.print(flex); Serial.print(',');
  Serial.println(tight ? 1 : 0);

  delay(LOOP_MS);
}
