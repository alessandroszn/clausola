#!/usr/bin/env python3
"""
Clausola — measuring extraction accuracy.

Compares the readings produced by extractor.py against the hand-marked ground
truth in truth.json and prints one thing:

    out of N fields, how many are right — and how many of the wrong ones the
    system had already flagged by itself as unstable.

The second figure is the one that matters for the pitch. A flagged error is not
a silent error: the user knows to check that line.

    python3 evaluate.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def majority(readings, field):
    """Most frequent value across the readings, and how many agreed on it.

    A model that drops a field altogether is a reading like any other: it is
    counted as null rather than crashing the evaluation, because a run that
    stops halfway measures nothing.
    """
    tally = {}
    for r in readings:
        d = r.get(field) if isinstance(r, dict) else None
        value = d.get("value") if isinstance(d, dict) else None
        c = json.dumps(value, ensure_ascii=False)
        tally[c] = tally.get(c, 0) + 1
    best = max(tally, key=tally.get)
    return json.loads(best), tally[best]


def never_stated(ref):
    """True where the contract does not state this figure at all.

    The ground truth records the value the arithmetic needs — a down payment
    nobody asked for is 0, an insurance nobody imposes is false — and marks the
    article as null because there is none. The prompt tells the model the
    opposite: "if a value is not written in the contract, the field is null".

    Both are right, for different purposes, and eighteen of the hundred and
    twenty fields are in this position. Counting the model wrong for obeying
    its own instruction would put fifteen points of invented error into the one
    number this file exists to report — and, since all three readings would
    agree on null, it would put them into the SILENT column, which is the
    number the whole project turns on.

    So null is accepted here, and the count is printed rather than absorbed.
    """
    return ref.get("where") is None and ref.get("value") in (0, False)


def main():
    with open(os.path.join(HERE, "truth.json"), encoding="utf-8") as f:
        truth = json.load(f)
    folder = os.path.join(HERE, "readings")
    if not os.path.isdir(folder):
        raise SystemExit(
            "No readings to evaluate.\n"
            "Run extractor.py first, on a machine with LM Studio on:\n"
            "    python3 extractor.py ../contracts/en/01_personal_loan.txt")

    total = right = wrong_flagged = wrong_silent = convention = 0
    detail = []

    for name, expected in truth.items():
        if name.startswith("_"):
            continue
        path = os.path.join(folder, name + ".json")
        if not os.path.exists(path):
            print(f"  ({name}.json missing — skipped)")
            continue
        with open(path, encoding="utf-8") as f:
            readings = json.load(f)

        for field, ref in expected.items():
            if field.startswith("_"):
                continue
            total += 1
            value, agreement = majority(readings, field)
            if value == ref["value"]:
                right += 1
            elif value is None and never_stated(ref):
                right += 1
                convention += 1
            elif agreement < len(readings):
                wrong_flagged += 1
                detail.append((name, field, ref["value"], value, "flagged"))
            else:
                wrong_silent += 1
                detail.append((name, field, ref["value"], value, "SILENT"))

    if not total:
        raise SystemExit("No field compared.")

    print("=" * 62)
    print(f"fields compared ................. {total}")
    print(f"extracted correctly ............. {right}  ({100*right/total:.1f}%)")
    print(f"  of which null on a figure the contract never states: {convention}")
    print(f"wrong BUT flagged ............... {wrong_flagged}")
    print(f"wrong and NOT flagged ........... {wrong_silent}"
          f"  ({100*wrong_silent/total:.1f}%)  <- the only dangerous number")
    print("=" * 62)
    for row in detail:
        print(f"  {row[4]:<8} {row[0]}.{row[1]}: expected {row[2]!r}, got {row[3]!r}")

    # The deck reads this file. If it is absent the risk slide says the
    # measurement has not been made; if it is present the slide prints the
    # number instead. Nothing has to be edited by hand in between.
    summary = {
        "contracts": sorted({d[0] for d in detail} |
                            {n for n in truth if not n.startswith("_")
                             and os.path.exists(os.path.join(folder, n + ".json"))}),
        "fields_compared": total,
        "correct": right,
        "correct_by_null_convention": convention,
        "wrong_flagged": wrong_flagged,
        "wrong_silent": wrong_silent,
        "accuracy_pct": round(100 * right / total, 1),
        "silent_error_pct": round(100 * wrong_silent / total, 1),
    }
    out = os.path.join(HERE, "accuracy.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print(f"\nwritten {out} — regenerate the deck and slide 22 picks it up:")
    print("    cd deck && node generate.js")


if __name__ == "__main__":
    main()
