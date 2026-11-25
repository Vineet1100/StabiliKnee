# StabiliKnee

A knee brace that tightens automatically when a small on-device neural network detects a risky knee movement.
Built with a team at **MakeUofT 2026** (3rd place). Original team repo: `ShivamJKhatri/StabiliKnee`.

> **Rebuilt Nov 2026.** The training data, Gemini script and trained model from the hackathon were lost
> afterwards. This repo rebuilds that pipeline so it can be run again from scratch.

## How it works

1. An **ITG-3200 gyroscope** measures knee rotation speed, and a **flex sensor** measures knee bend.
2. On startup, the gyro averages **1,500** resting readings to remove drift.
3. Every **20 ms**, the brace computes three features: rotation speed, jerk (how fast that speed changes) and bend.
4. A **TinyML** model (3 inputs → 6 hidden units → 1 output) runs on the Arduino and outputs a risk probability.
5. Above **0.5**, a servo tightens the brace. It stays tight for at least **700 ms** and releases after
   **1 s** of calm, so it doesn't flicker on and off.
6. Until a model is trained, the brace falls back to a plain threshold (smoothed rotation above **80 deg/s**).

## Hardware

Arduino Uno R3 · ITG-3200 3-axis gyroscope (ATAVRSBIN1 board) · flex sensor (A0) · SG90 servo · 10 kΩ resistor

## Rebuild the model

```bash
cd extension
pip install -r requirements.txt

# 1. Upload stabiliknee/stabiliknee.ino, then record labelled sessions
#    label 0 = normal movement (walking, stairs, sitting), label 1 = a risky twist acted out safely
python log_serial.py /dev/cu.usbmodem1101 data/walk_01.csv --label 0 --seconds 60
python log_serial.py /dev/cu.usbmodem1101 data/twist_01.csv --label 1 --seconds 10

# 2. Add synthetic stress-pattern data with Gemini (needs GEMINI_API_KEY)
python make_synthetic.py --normal 20 --risky 20

# 3. Train, test on unseen real sessions, and export stabiliknee/model.h
python train_model.py

# 4. Re-upload stabiliknee.ino: the brace now runs the trained model
```

`train_model.py` reports false alarms per minute and the % of risky sessions caught, for the model and for a
basic 80 deg/s threshold. It tests only on real recordings it never trained on.
`evaluate.py` is an optional check of the threshold-only rule.

## Limitations

- Powered over USB: one 9V battery was not enough for the sensors and servo.
- Training labels come from acted-out movements, not real dislocations. This is a prototype, not a medical device.
