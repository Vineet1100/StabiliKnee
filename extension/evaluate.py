"""Compare two trigger rules on recorded (or synthetic) sessions.

  basic  : tighten whenever raw rotation speed > 80 deg/s
  brace  : the firmware's rule (smoothing + two thresholds + hold/release)

Usage:
    python evaluate.py data/*.csv
    python evaluate.py synthetic/*.csv

Each CSV needs at least: ms, mag_raw, label  (label 0 = normal, 1 = risky)
"""
import csv
import sys

# Must match stabiliknee.ino
RISK_ON, RISK_OFF = 80.0, 25.0
HOLD_MS, RELEASE_MS = 700, 1000
EMA_ALPHA = 0.25


def basic_rule(ms, mags):
    return [m > RISK_ON for m in mags]


def brace_rule(ms, mags):
    ema, tight, last_risk, calm_start = 0.0, False, None, None
    out = []
    for t, m in zip(ms, mags):
        ema = EMA_ALPHA * m + (1 - EMA_ALPHA) * ema
        if ema > RISK_ON:
            last_risk, calm_start = t, None
        if last_risk is not None and t - last_risk < HOLD_MS:
            tight = True
        elif ema < RISK_OFF:
            calm_start = t if calm_start is None else calm_start
            tight = tight and t - calm_start < RELEASE_MS
        else:
            calm_start = None
        out.append(tight)
    return out


def triggers(states):
    """Number of times the brace goes from relaxed to tight."""
    return sum(1 for prev, cur in zip([False] + states, states) if cur and not prev)


def first_trigger_ms(ms, states):
    return next((t for t, s in zip(ms, states) if s), None)


def load(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path} is empty")
    ms = [float(r["ms"]) for r in rows]
    mags = [float(r["mag_raw"]) for r in rows]
    return ms, mags, int(rows[0]["label"])


def main(paths):
    totals = {name: {"false_alarms": 0, "detected": 0, "delays": []} for name in ("basic", "brace")}
    normal_min, risky_sessions = 0.0, 0

    for path in paths:
        ms, mags, label = load(path)
        if label == 0:
            normal_min += (ms[-1] - ms[0]) / 60000
        else:
            risky_sessions += 1
            onset = next((t for t, m in zip(ms, mags) if m > RISK_ON), None)
        for name, rule in (("basic", basic_rule), ("brace", brace_rule)):
            states = rule(ms, mags)
            if label == 0:
                totals[name]["false_alarms"] += triggers(states)
            else:
                hit = first_trigger_ms(ms, states)
                if hit is not None:
                    totals[name]["detected"] += 1
                    if onset is not None:
                        totals[name]["delays"].append(hit - onset)

    print(f"Normal data: {normal_min:.1f} min | Risky sessions: {risky_sessions}\n")
    for name, r in totals.items():
        fa_rate = r["false_alarms"] / normal_min if normal_min else float("nan")
        det = 100 * r["detected"] / risky_sessions if risky_sessions else float("nan")
        delay = sum(r["delays"]) / len(r["delays"]) if r["delays"] else float("nan")
        print(f"{name:6} false alarms/min: {fa_rate:5.2f} | risky detected: {det:5.1f}% | "
              f"avg delay after first >80 reading: {delay:.0f} ms")

    b, f = totals["basic"]["false_alarms"], totals["brace"]["false_alarms"]
    if b:
        print(f"\nFalse alarms cut by {100 * (b - f) / b:.0f}% (brace vs basic)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
