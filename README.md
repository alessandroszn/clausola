# Clausola

What you actually signed, and what it costs to get out.

Academic prototype — *Introduction to Fintech*, USI, September 2026 session.
Alessandro Zanichelli · Arnel Hodza · Denis Valentinelli

---

## What it is

You paste in a consumer financial contract — loan, lease, mortgage, instalment card, insurance — and in thirty seconds you see **what it costs you in total**, **what it costs to get out early** and **what happens if you do nothing**, with **the line of the contract** every number comes from next to it.

## How to try it, in ten seconds

Try it in the browser: **https://<user>.github.io/clausola/**

Or open **`clausola.html`** with a double click — which is the way to read a contract of your own, for the reason under *Limits*. No server, nothing to install, no API key.
Six sample contracts are already inside — two offers each of a personal loan (same CHF 12'000),
a car lease (same CHF 28'000 car) and a motor policy — in **English, French,
German, Italian and Spanish**; switch language at the top right (each has its flag), and the
page follows your system's light or dark appearance, with a manual toggle in the header.
Pick a contract and press *Read the contract*.

**What you are looking at when you do that.** The six sample contracts run **without a model**:
their three readings are stored in the file, and the disagreement between those readings is
**set by hand**. It shows what the system does with disagreement; it does not measure how much
of it a model produces. The page says so, in every language, among the limits under each result.
The measurement itself is the one step still open, and `RUNBOOK.md` is how it gets closed.

## How to read a contract of your own

You need a local model:

1. install [LM Studio](https://lmstudio.ai) and load a model (e.g. `gemma3-4B-it`);
2. *Developer → Start Server* (port 1234), **CORS enabled**;
3. open `clausola.html`, choose *“a contract of my own”*, paste the text, press *Read the contract*.

The contract **never leaves the machine**: there is no server of ours, no account, no storage.

## The two rules the project stands on

**1. The LLM never calculates.** It extracts twenty fields into a strict JSON schema, and for every field it reports the literal quotation. Every number — totals, amortisation, penalties — is worked out by deterministic code. *(Deck 06 GenAI: LLMs are models of language, not of computation.)*

**2. Disagreement is shown, not hidden.** The contract is read **three times**. Every item carries its own level of agreement — 3 of 3, 2 of 3, all different — and where the system is not stable it says so. *(Deck 06 GenAI: LLMs are not deterministic — “how to notice: ask the same question twice”.)*

And where the contract points at a figure it never states, the product writes **not computable**. A plausible wrong number is worse than no number.

## Three things it does that a single reading cannot

**It compares — like with like.** Switch to *Compare* at the top of the first panel: the
contracts are grouped by kind, and only offers of the same kind compare — a lease against a
lease, a loan against a loan. The two leasing offers are for the same CHF 28'000 car, and the
comparison shows the point in one screen: the lower monthly instalment is not the cheaper
contract. The best value in each row carries a green dot; the lowest total carries the flag.

**It shows the calendar.** Every contract fixes things in time: a lock-in you cannot leave before,
a notice window, a last day to cancel, an expiry, an automatic renewal. The page draws them on one
line, in months from signature.

**It shows the three readings.** Where the three do not agree, you see all three values next to
each other with the one we kept marked — not a summary of the disagreement, the disagreement itself.

**It hands you the report.** *The CHF 6 report — print or save as PDF* produces the one-page
document that is the unit of sale: the headline figures, every clause quoted verbatim with its
agreement count, the stated limits. Generated in the browser; nothing leaves the page.

**And it can present itself.** The *Presentation* button starts a scripted, keyboard-driven
walk through the whole argument — lease, provenance, timeline, exit curve, the three
readings, comparison — with a caption bar readable from the back of a room. Arrow keys advance, Esc exits.

## The one thing that recurs

Reading a contract happens once. **Remembering the cancellation window comes back every year.** For a contract that renews automatically, the product works out the last day you can still cancel and hands you a calendar file (`.ics`). The date stays on your machine — it leaves as a file you keep, not as a record we hold.

## The files

```
index.html                    the same page under the name GitHub Pages serves
clausola.html                 the finished, standalone page (generated)
template.html                 source: interface, five languages, JavaScript calculations
build.py                      generates clausola.html by injecting the data
contracts/{en,fr,de,it,es}/   the same six sample contracts in five languages
extraction/fields.json        values + the LOCATION of each clause (language-independent)
extraction/variations.json    the differences between the three readings (demo mode)
extraction/truth.json         the English reading marked by hand, with quotations
extraction/legibility.py      what each contract states, and what it only implies
extraction/calculations.py    the deterministic calculations — reference for the JS version
extraction/extractor.py       litellm + LM Studio: three readings, strict schema
extraction/evaluate.py        measures accuracy and, above all, UNFLAGGED errors
extraction/costs.py           marginal cost per document, with stated assumptions
extraction/infrastructure.py  at what volume our own GPU stops being the expensive option
requirements.txt              the two packages the extraction step needs
RUNBOOK.md                    how to run the measurement that is still open, step by step
```

The quotations shown in the interface are **not stored**: `build.py` locates each
clause in each language's contract at build time, so what is highlighted is always
an exact substring of the document on screen — in all five languages.

After changing `template.html`, `contracts/` or `extraction/*.json`:

```bash
python3 build.py                    # regenerate clausola.html
python3 extraction/calculations.py  # check the numbers
python3 extraction/costs.py         # marginal cost per document
```

## Measuring the extraction — the step that is missing

On a machine with LM Studio running:

```bash
pip install -r requirements.txt
python3 extraction/extractor.py contracts/en/01_personal_loan.txt
python3 extraction/evaluate.py
```

`evaluate.py` prints five numbers. Two of them decide anything: how many fields are right, and — **the one that matters** — how many of the wrong ones passed without being flagged. That second figure is the real risk of the project.

## Limits, stated

- **The disagreement shown on the six sample contracts is ours, not a model's.** It comes from `extraction/variations.json`, which is hand-set and says so in its own first line. No model has been run behind the demonstration you open by double-clicking.
- **We wrote the six sample contracts ourselves.** They are not real contracts of existing providers. On real contracts the extraction is **not yet measured**.
- An unexpected type of contract breaks the pipeline: that is the stated downside of deterministic orchestration.
- **This is not legal or financial advice.** The product reorders what the contract says and works out its arithmetic consequences. It does not say whether a clause is valid, whether the price is fair, or whether a better offer exists.
- Publishing `clausola.html` on GitHub Pages works for the sample contracts; reading a contract of your own requires LM Studio **on the machine of whoever visits the page**.

## What is deliberately not in here

No API key. No personal data. No server. No account.
And in the vocabulary: it is not an *agent*, it does not use *RAG*, there is no *sandbox*.
