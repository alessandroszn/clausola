#!/usr/bin/env python3
"""
Clausola — reference implementation of the deterministic calculations.

Architectural rule of the project: the LLM extracts, the code calculates.
This file is the Python version of the same arithmetic implemented in
JavaScript inside clausola.html. It exists so the two implementations can be
checked against each other.

No model calls. No network.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def val(fields, name, default=None):
    f = fields.get(name)
    if f is None:
        return default
    v = f.get("value")
    return default if v is None else v


def outstanding_capital(payment, nar_pct, term, k):
    """Capital still owed after k payments, standard amortisation."""
    n = term - k
    if n <= 0:
        return 0.0
    if not nar_pct:
        return payment * n
    i = nar_pct / 1200.0
    return payment * (1 - (1 + i) ** (-n)) / i


def analyse(fields):
    kind = val(fields, "type", "other")
    pay = val(fields, "monthly_payment", 0) or 0
    term = val(fields, "term_months", 0) or 0
    nar = val(fields, "nar_percent")
    upfront = val(fields, "upfront_fees", 0) or 0
    per_pay = val(fields, "fee_per_payment", 0) or 0
    down = val(fields, "down_payment", 0) or 0
    buyout = val(fields, "buyout_value", 0) or 0
    financed = val(fields, "financed_amount")
    lockin = val(fields, "exit_lockin_months", 0) or 0
    pen_type = val(fields, "exit_penalty_type", "none")
    pen_pct = val(fields, "exit_penalty_percent", 0) or 0
    pen_fixed = val(fields, "exit_fixed_fees", 0) or 0
    renewal = val(fields, "auto_renewal", False)
    single = val(fields, "single_payment_alternative")

    r = {}

    # 1. Total cost if you see it through
    total = down + pay * term + upfront + per_pay * term
    r["total_cost"] = total
    r["total_cost_with_buyout"] = total + buyout if buyout else None

    # 2. Mark-up over the value received
    if financed and kind == "consumer_credit":
        r["markup"] = total - financed
    elif financed and kind == "lease":
        r["markup"] = (total + buyout) - financed
    else:
        r["markup"] = None
    if r["markup"] is not None and financed:
        r["markup_pct"] = 100.0 * r["markup"] / financed

    # 3. Cost of getting out halfway
    k = max(lockin, term // 2)
    r["exit_month"] = k
    paid = down + upfront + (pay + per_pay) * k

    if pen_type == "percent_of_outstanding_capital":
        rest = outstanding_capital(pay, nar, term, k)
        # A contract can waive the charge near the end of the term (personal loan,
        # Art. 5.3: "where the remaining term is 12 months or less, no charge is
        # due"). That threshold is not one of the twenty extracted fields; it is
        # carried as contract metadata, and the schema not holding it is a stated
        # limitation, not an oversight.
        waiver = fields.get("_exit_penalty_waiver_months")
        penalty = 0.0 if (waiver is not None and term - k <= waiver) else rest * pen_pct / 100.0
        r["exit_cost"] = paid + rest + penalty + pen_fixed
        r["exit_breakdown"] = {"already paid": paid, "capital still owed": rest,
                               "penalty": penalty, "fees": pen_fixed}
    elif pen_type == "remaining_instalments_plus_percent":
        rest = pay * (term - k)
        penalty = rest * pen_pct / 100.0
        r["exit_cost"] = paid + rest + penalty + pen_fixed
        r["exit_breakdown"] = {"already paid": paid, "instalments left": rest,
                               "penalty": penalty, "fees": pen_fixed}
    elif pen_type == "repay_discounts":
        # The contract points at a quantity the extracted fields do not contain
        # (how many annual periods received the discount, and on what full
        # premium). The product does NOT estimate: it states it cannot be
        # calculated.
        r["exit_cost"] = None
        r["exit_breakdown"] = None
        r["exit_not_computable"] = (
            "The contract requires you to repay the discounts already received, "
            "but does not say how much: it depends on how many annual periods "
            "you benefited from the discount. The contract does not give that "
            "figure, and we do not invent it.")
    else:
        r["exit_cost"] = None
        r["exit_breakdown"] = None

    if r["exit_cost"] is not None:
        # Comparison base: the scenario that ends in the same situation. In a
        # lease, leaving means handing the vehicle back, so the correct
        # comparison is with natural expiry WITHOUT the buyout.
        r["saving_by_leaving"] = r["total_cost"] - r["exit_cost"]
        r["saving_pct"] = 100.0 * r["saving_by_leaving"] / r["total_cost"]

    # 4. Cost of automatic renewal
    r["auto_renewal_cost"] = pay * term if renewal else None

    # 5. Cost of paying by instalments, where the contract offers a single payment
    if single:
        r["instalment_surcharge"] = pay * 12 - single
        r["instalment_surcharge_pct"] = 100.0 * (pay * 12 - single) / single
    else:
        r["instalment_surcharge"] = None

    return r


def chf(x):
    if x is None:
        return "—"
    return f"CHF {x:,.2f}".replace(",", "'")


if __name__ == "__main__":
    with open(os.path.join(HERE, "truth.json"), encoding="utf-8") as f:
        data = json.load(f)

    for name, fields in data.items():
        if name.startswith("_"):
            continue
        r = analyse(fields)
        print("=" * 68)
        print(name)
        print("=" * 68)
        print(f"  Total cost if you see it through .. {chf(r['total_cost'])}")
        if r["total_cost_with_buyout"]:
            print(f"  ... with the final buyout ......... {chf(r['total_cost_with_buyout'])}")
        if r["markup"] is not None:
            print(f"  Mark-up over the value ............ {chf(r['markup'])}"
                  f"  ({r['markup_pct']:.1f}%)")
        if r["exit_cost"] is not None:
            print(f"  Leaving at month {r['exit_month']:>2} .............. {chf(r['exit_cost'])}")
            for kk, vv in r["exit_breakdown"].items():
                print(f"      {kk:.<28} {chf(vv)}")
            word = "YOU SAVE" if r["saving_by_leaving"] >= 0 else "YOU PAY MORE"
            print(f"  Leaving halfway: {word} ....... {chf(abs(r['saving_by_leaving']))}"
                  f"  ({abs(r['saving_pct']):.1f}%)")
        if r.get("exit_not_computable"):
            print("  Early exit ........................ NOT COMPUTABLE")
        if r["auto_renewal_cost"]:
            print(f"  Cost of automatic renewal ......... {chf(r['auto_renewal_cost'])}")
        if r.get("instalment_surcharge"):
            print(f"  Cost of paying by instalments ..... {chf(r['instalment_surcharge'])}"
                  f"  (+{r['instalment_surcharge_pct']:.1f}%)")
        print()
