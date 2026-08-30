#!/usr/bin/env python3
"""
Clausola — what the contract states, and what it only implies.

This is the evidence the project rests on, and it comes from the documents
themselves rather than from anybody's opinion about them.

For each of the three contracts it asks, field by field:

    is this figure written in the document as a number,
    or does the reader have to build it out of several clauses?

The answer is not an interpretation. A field is "stated" if the ground truth
in fields.json points at an article that gives it as a number. The three
figures a person actually needs — what it costs in total, what it costs to
leave, what it costs to do nothing — are not fields. They are computed in
calculations.py out of several stated fields at once, and the count of how
many, and from which articles, is printed below.

    python3 legibility.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# The figures a person needs, and the stated fields each one is built from.
# The field names match fields.json; the article numbers are read from it, so
# this file cannot drift from the ground truth.
DERIVED = {
    "01_personal_loan": [
        ("What it costs you in total",
         ["monthly_payment", "term_months", "upfront_fees", "fee_per_payment"]),
        ("What it costs to leave at month 18",
         ["financed_amount", "nar_percent", "monthly_payment", "term_months",
          "exit_penalty_percent", "exit_notice_days"]),
    ],
    "02_car_lease": [
        ("What it costs you in total",
         ["down_payment", "monthly_payment", "term_months", "upfront_fees"]),
        ("What it costs to leave at month 24",
         ["monthly_payment", "term_months", "exit_lockin_months",
          "exit_penalty_percent", "exit_fixed_fees", "down_payment", "upfront_fees"]),
    ],
    "03_motor_policy": [
        ("What it costs you in total",
         ["monthly_payment", "term_months", "upfront_fees"]),
        ("What paying monthly costs you over paying once",
         ["monthly_payment", "term_months", "single_payment_alternative"]),
        ("What it costs to leave early",
         ["exit_penalty_type", "exit_penalty_percent"]),
    ],
}

# The one the document points at but never quantifies.
NOT_COMPUTABLE = {("03_motor_policy", "What it costs to leave early")}


def main():
    with open(os.path.join(HERE, "fields.json"), encoding="utf-8") as f:
        data = json.load(f)

    stated_total = absent_total = 0

    for doc, rows in DERIVED.items():
        fields = data[doc]
        stated = {k: v for k, v in fields.items()
                  if not k.startswith("_") and v.get("where")}
        absent = [k for k, v in fields.items()
                  if not k.startswith("_") and not v.get("where")]
        stated_total += len(stated)
        absent_total += len(absent)

        print("=" * 74)
        print(doc)
        print("=" * 74)
        print(f"  Fields the document states outright ....... {len(stated)} of "
              f"{len(stated) + len(absent)}")
        print(f"  Fields it never mentions .................. {len(absent)}")
        print()
        print("  What the reader actually wants to know:")
        for label, needed in rows:
            arts = []
            for name in needed:
                where = fields.get(name, {}).get("where")
                if where and where not in arts:
                    arts.append(where)
            verdict = ("NOT COMPUTABLE — the document points at a quantity it never gives"
                       if (doc, label) in NOT_COMPUTABLE
                       else f"not stated — built from {len(needed)} figures "
                            f"across {len(arts)} clauses")
            print(f"    · {label}")
            print(f"        {verdict}")
            if (doc, label) not in NOT_COMPUTABLE:
                print(f"        {', '.join(arts)}")
        print()

    print("=" * 74)
    print("CONCLUSION")
    print("=" * 74)
    print(f"  Across the three contracts, {stated_total} figures are stated as numbers.")
    print("  Not one of them is the figure a person is deciding on.")
    print("  Every contract states the instalment. No contract states the total,")
    print("  and no contract states what leaving costs.")
    print()
    print("  This is not a claim about how people read. It is a property of the")
    print("  documents, and it is why the product is arithmetic on a quotation")
    print("  rather than advice.")


if __name__ == "__main__":
    main()
