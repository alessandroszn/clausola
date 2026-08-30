#!/usr/bin/env python3
"""
Clausola — clause extraction with a local model.

Run on a machine with LM Studio on:
    Developer -> Start Server (port 1234), a model loaded.

    pip install litellm pymupdf
    python3 extractor.py ../contracts/en/01_personal_loan.txt

It performs THREE independent readings of the same contract and saves them to
readings/<name>.json, in the shape the prototype expects.

Why three: LLMs are not deterministic (deck 06 GenAI, point 2: "how to notice —
ask the same question twice"). One reading says nothing about its own
reliability. Three readings say where the system is stable and where it is not,
and that is information for the user.

The LLM does one thing here: find sentences and put them into fields.
It calculates nothing. The calculations live in calculations.py and clausola.html.
"""
import json
import os
import sys

try:
    from litellm import completion
except ImportError:
    sys.exit("litellm is missing.  pip install litellm")

HERE = os.path.dirname(os.path.abspath(__file__))

# Which model runs is a configuration, not an architecture decision. The
# interface between this project and any model is the strict JSON schema
# below: twenty fields, each {value, quote, where}. Anything that can fill
# that schema is interchangeable, and litellm normalises the call. Switching
# provider is two environment variables — that is deliberate, and it is what
# keeps the one input we cannot substitute from becoming a dependency.
#
#   on the device (default, and what the demo uses)
#       CLAUSOLA_API_BASE=http://localhost:1234/v1   CLAUSOLA_MODEL=openai/local-model
#   an EU-hosted open-weights provider
#       CLAUSOLA_API_BASE=<provider endpoint>        CLAUSOLA_MODEL=openai/<served name>
#   our own GPU serving the same open weights (vLLM speaks the same API)
#       CLAUSOLA_API_BASE=https://<our host>/v1      CLAUSOLA_MODEL=openai/<served name>
#   a proprietary API
#       CLAUSOLA_MODEL=<provider>/<model>            (litellm resolves the endpoint)
#
# See infrastructure.py for the volume at which running our own GPU stops
# being more expensive than paying per call.
API_BASE = os.environ.get("CLAUSOLA_API_BASE", "http://localhost:1234/v1")
MODEL = os.environ.get("CLAUSOLA_MODEL", "openai/local-model")
N_READINGS = 3

NUMERIC = [
    "financed_amount", "monthly_payment", "term_months", "nar_percent",
    "apr_percent", "down_payment", "upfront_fees", "fee_per_payment",
    "buyout_value", "single_payment_alternative", "cancellation_notice_days",
    "exit_lockin_months", "exit_notice_days", "exit_penalty_percent",
    "exit_fixed_fees", "insurance_monthly_cost",
]
BOOLEAN = ["auto_renewal", "insurance_required"]
TEXTUAL = ["type", "exit_penalty_type"]
FIELDS = TEXTUAL[:1] + NUMERIC + BOOLEAN + TEXTUAL[1:]

PROMPT = """# Who you are
You extract clauses from consumer financial contracts.

# What you do
You read the contract and report the fields required by the JSON schema.
For every field you also report the LITERAL sentence of the contract you took
it from, and its location (article or point).

# How you do it
- You calculate nothing. You do not add, multiply or estimate.
- If a value is not written in the contract, the field is null and so is the quote.
- You do not derive one value from another. If the contract does not say it,
  neither do you.
- The quote is copied from the text, not rewritten.
- Amounts are numbers, with no currency symbol and no thousands separator.

# Allowed values
- type: consumer_credit | lease | mortgage | insurance | instalment_card |
  bnpl | other
- exit_penalty_type: percent_of_outstanding_capital |
  remaining_instalments_plus_percent | repay_discounts | fixed_amount | none
"""


def schema():
    props = {}
    for name in FIELDS:
        if name in NUMERIC:
            t = "number"
        elif name in BOOLEAN:
            t = "boolean"
        else:
            t = "string"
        props[name] = {
            "type": "object", "additionalProperties": False,
            "properties": {
                "value": {"type": [t, "null"]},
                "quote": {"type": ["string", "null"]},
                "where": {"type": ["string", "null"]},
            },
            "required": ["value", "quote", "where"],
        }
    return {"type": "object", "additionalProperties": False,
            "properties": props, "required": FIELDS}


def read_text(path):
    if path.lower().endswith(".pdf"):
        import fitz  # PyMuPDF
        with fitz.open(path) as doc:
            return "\n".join(p.get_text() for p in doc)
    with open(path, encoding="utf-8") as f:
        return f.read()


def one_reading(text, index):
    response = completion(
        model=MODEL,
        api_base=API_BASE,
        api_key="not-needed",     # LM Studio does not check it: no key in the repo
        temperature=0.3,
        messages=[{"role": "system", "content": PROMPT},
                  {"role": "user", "content": text}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": "contract", "strict": True,
                                         "schema": schema()}},
    )
    content = response.choices[0].message.content
    served = getattr(response, "model", "unknown")
    print(f"  reading {index + 1}/{N_READINGS} — model served: {served}")
    return json.loads(content)


def main():
    if len(sys.argv) < 2:
        sys.exit(f"usage: {sys.argv[0]} <contract.txt|contract.pdf>")
    path = sys.argv[1]
    name = os.path.splitext(os.path.basename(path))[0]
    text = read_text(path)
    print(f"{name}: {len(text)} characters, ~{len(text)//4} tokens")

    readings = [one_reading(text, i) for i in range(N_READINGS)]

    folder = os.path.join(HERE, "readings")
    os.makedirs(folder, exist_ok=True)
    out = os.path.join(folder, name + ".json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(readings, f, ensure_ascii=False, indent=1)
    print("written", out)

    unstable = [f for f in FIELDS
                if len({json.dumps(r[f]["value"]) for r in readings}) > 1]
    print(f"fields stable across the three readings: {len(FIELDS) - len(unstable)}/{len(FIELDS)}")
    if unstable:
        print("unstable:", ", ".join(unstable))


if __name__ == "__main__":
    main()
