"""Record one labelled session from the brace to a CSV.

Example (find your port in Arduino IDE > Tools > Port):
    python log_serial.py /dev/cu.usbmodem1101 data/walk_01.csv --label 0 --seconds 60
    python log_serial.py /dev/cu.usbmodem1101 data/twist_01.csv --label 1 --seconds 10

label 0 = normal movement (walking, sitting, stairs)
label 1 = a risky twist you act out safely
"""
import argparse
import csv
import time

import serial  # pip install pyserial

FIELDS = ["ms", "mag_raw", "mag_ema", "flex", "tight"]

p = argparse.ArgumentParser()
p.add_argument("port")
p.add_argument("out")
p.add_argument("--label", type=int, choices=[0, 1], required=True)
p.add_argument("--seconds", type=float, default=30)
args = p.parse_args()

import os
os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

rows = 0
with serial.Serial(args.port, 115200, timeout=1) as port, open(args.out, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(FIELDS + ["label"])
    end = time.time() + args.seconds
    while time.time() < end:
        line = port.readline().decode(errors="ignore").strip()
        parts = line.split(",")
        if len(parts) != len(FIELDS):
            continue  # skips the header and calibration messages
        try:
            [float(x) for x in parts]
        except ValueError:
            continue
        writer.writerow(parts + [args.label])
        rows += 1

print(f"Saved {rows} readings to {args.out}")
