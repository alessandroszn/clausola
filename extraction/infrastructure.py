#!/usr/bin/env python3
"""
Clausola — where should the model run?

Three answers are possible and only one of them is right at a given volume.
This script says which, by arithmetic rather than by preference.

    on the device      marginal cost 0, fixed cost 0, quality lower
    hosted API         marginal cost per document, fixed cost 0
    our own GPU        marginal cost ~0, fixed cost every month whether used or not

The question "should we run our own infrastructure" is therefore not an
architecture question, it is a break-even question: below a certain number of
documents a month, a GPU we rent is a bill we pay for capacity nobody used.

    python3 infrastructure.py
"""

# --- assumptions, all explicit ---------------------------------------------
# Marginal cost per document, from costs.py (12-page contract, three readings).
API_SMALL = 0.0077          # CHF, small hosted model
API_MEDIUM = 0.0383         # CHF, medium hosted model
# Monthly cost of one GPU instance able to serve a 7B model in the EU or
# Switzerland, including the hours nobody uses it. A range, not a quote.
GPU_MONTHLY = [250.0, 350.0, 450.0]
PRICE_PER_REPORT = 6.0      # our single-report price


def rows():
    for gpu in GPU_MONTHLY:
        for label, api in (("small hosted model", API_SMALL),
                           ("medium hosted model", API_MEDIUM)):
            docs = gpu / api
            yield gpu, label, docs, docs * PRICE_PER_REPORT


def main():
    print("ASSUMPTIONS")
    print(f"  hosted marginal cost per document: CHF {API_SMALL:.4f} (small) / "
          f"CHF {API_MEDIUM:.4f} (medium)")
    print(f"  own GPU, monthly, EU/CH: CHF {GPU_MONTHLY[0]:.0f}–{GPU_MONTHLY[-1]:.0f}")
    print(f"  single-report price: CHF {PRICE_PER_REPORT:.2f}")
    print()
    print("BREAK-EVEN — below this volume, renting a GPU costs more than paying per call")
    print(f"  {'GPU / month':>12}  {'against':<21} {'documents / month':>19} {'≈ revenue at that volume':>26}")
    for gpu, label, docs, rev in rows():
        print(f"  {'CHF '+format(gpu,'.0f'):>12}  {label:<21} {docs:>19,.0f} {'CHF '+format(rev,',.0f'):>26}"
              .replace(",", "'"))
    print()
    print("CONSEQUENCE")
    print("  Our own infrastructure is the wrong answer until we are reading roughly")
    print(f"  {min(g/API_MEDIUM for g in GPU_MONTHLY):,.0f}–{max(g/API_SMALL for g in GPU_MONTHLY):,.0f} documents a month."
          .replace(",", "'"))
    print("  Until then: on the device by default, a hosted API as the fallback.")
    print("  The model is the replaceable part — the schema is the interface.")


if __name__ == "__main__":
    main()
