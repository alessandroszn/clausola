#!/usr/bin/env python3
"""
Clausola — marginal cost per document, calculated rather than asserted.

The course (unit 11) requires the revenue model to match the cost structure.
Checking that needs a number, not an impression.

This script produces one, with STATED ASSUMPTIONS. It is not a measurement: the
real measurement comes from litellm's llm.completion_cost() on the machine that
actually makes the calls. What it establishes is the ORDER OF MAGNITUDE, which
is what a revenue-model decision needs.

    python3 costs.py
"""
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# --- assumptions, all explicit ---------------------------------------------
CHARS_PER_TOKEN = 3.7       # English/Italian legal prose, current estimate
READINGS = 3                # the product reads every contract three times
PROMPT_TOKENS = 400         # the system prompt
OUTPUT_TOKENS = 1500        # twenty fields with quotes, per reading
USD_CHF = 0.88              # assumption

# Price per million tokens. Stated as an assumption: small hosted models. The
# real figure should be replaced with the actual provider's list price at the
# moment of the decision.
PRICES = [
    ("small hosted model",  0.20, 0.80),
    ("medium hosted model", 1.00, 4.00),
    ("model on the device", 0.00, 0.00),
]

CASES = [
    ("sample contract (this repository)", None),
    ("real short contract, ~6 pages", 15000),
    ("real long contract, ~12 pages", 30000),
]


DEFAULT_CHARS = 3000


def sample_chars():
    """Average length of the sample contracts. The contracts live one directory
    down, per language: contracts/en/*.txt, not contracts/*.txt. The earlier
    version of this line looked in the wrong place, found nothing and returned
    the default WITHOUT SAYING SO — a plausible figure with no provenance, which
    is the exact failure this product exists to catch. It now says so."""
    files = glob.glob(os.path.join(HERE, "..", "contracts", "en", "*.txt"))
    if not files:
        print(f"  (no sample contract found on disk — {DEFAULT_CHARS} characters"
              " used as a STATED default, not a measurement)")
        return DEFAULT_CHARS
    return sum(len(open(f, encoding="utf-8").read()) for f in files) / len(files)


def main():
    print("ASSUMPTIONS")
    print(f"  {CHARS_PER_TOKEN} characters per token · {READINGS} readings per contract")
    print(f"  {PROMPT_TOKENS} prompt tokens · {OUTPUT_TOKENS} output tokens per reading")
    print(f"  USD/CHF {USD_CHF}")
    print()

    for case, chars in CASES:
        if chars is None:
            chars = sample_chars()
        tok_in = (chars / CHARS_PER_TOKEN + PROMPT_TOKENS) * READINGS
        tok_out = OUTPUT_TOKENS * READINGS
        print(f"{case}  —  {int(chars)} characters")
        print(f"  input tokens: {int(tok_in):>7}   output: {int(tok_out):>6}")
        for label, p_in, p_out in PRICES:
            usd = tok_in / 1e6 * p_in + tok_out / 1e6 * p_out
            print(f"    {label:.<26} CHF {usd * USD_CHF:0.4f} per document")
        print()

    print("CONSEQUENCE")
    print("  The marginal cost per document is in the order of CENTIMES, not francs,")
    print("  even with a hosted model. So it is NOT the cost that decides the revenue")
    print("  model: it is the FREQUENCY of the need. A person signs an important")
    print("  financial contract once every two or three years, not every month.")


if __name__ == "__main__":
    main()
