"""Use Gemini to create synthetic sessions that expand the training data for train_model.py.

Synthetic data adds risky cases you can't safely act out many times.
train_model.py tests only on real recordings, so the reported results stay honest.

Setup:
    pip install google-genai
    export GEMINI_API_KEY=your_key
Usage:
    python make_synthetic.py --normal 20 --risky 20
"""
import argparse
import csv
import json
import os

from google import genai

PROMPT = """You are simulating a knee brace with a gyroscope and a flex sensor, sampled every 20 ms.
Return ONLY a JSON list of {n} pairs [rotation, flex]:
- rotation: rotation speed magnitude in deg/s (0 to 400)
- flex: flex sensor change from a straight leg, in Arduino analog units (0 to 600)
Movement: {movement}.
Include realistic sensor noise. Do not explain."""

NORMAL = ["slow walking", "climbing stairs", "sitting down", "standing up quickly", "jogging"]
RISKY = ["sudden inward knee twist while planting the foot",
         "pivoting hard on one leg during a basketball cut",
         "foot catching and the knee rotating sharply"]


def ask(client, movement, n):
    reply = client.models.generate_content(
        model="gemini-2.5-flash", contents=PROMPT.format(n=n, movement=movement))
    text = reply.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    pairs = [(float(m), float(fl)) for m, fl in json.loads(text)]
    if len(pairs) < n // 2 or not all(0 <= m <= 400 and 0 <= fl <= 1023 for m, fl in pairs):
        raise ValueError("unusable output")
    return pairs


def save(path, pairs, label):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ms", "mag_raw", "flex", "label"])
        for i, (m, fl) in enumerate(pairs):
            w.writerow([i * 20, m, fl, label])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--normal", type=int, default=10)
    p.add_argument("--risky", type=int, default=10)
    p.add_argument("--samples", type=int, default=250, help="250 x 20ms = 5 s per session")
    args = p.parse_args()

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    os.makedirs("synthetic", exist_ok=True)
    saved = skipped = readings = 0
    for label, count, movements in ((0, args.normal, NORMAL), (1, args.risky, RISKY)):
        for i in range(count):
            movement = movements[i % len(movements)]
            try:
                values = ask(client, movement, args.samples)
            except Exception as e:  # bad JSON or API error: skip this one, keep going
                print(f"skipped ({movement}): {e}")
                skipped += 1
                continue
            save(f"synthetic/{'normal' if label == 0 else 'risky'}_{i:02d}.csv", values, label)
            saved += 1
            readings += len(values)
    print(f"Saved {saved} sessions ({readings} readings) to synthetic/ ({skipped} skipped)")


if __name__ == "__main__":
    main()
