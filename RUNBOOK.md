# Measuring the extraction — the one thing left

> **This file is part of the submission on purpose.** The project has one open step, and rather
> than leave it to be discovered we have scoped it, given it an owner and written the commands.
> Everything around it has been run end to end with the model call replaced by a stub, so the
> pipeline is known to work; the measuring tool was written before any measurement existed.
> What is missing is a machine with a model on it, and no script can supply that.

**Owner: Alessandro. About an afternoon, most of it waiting.**

What it changes: the demonstration stops being staged and becomes measured. The risk slide of the deck stops saying *"no model has been run behind this demonstration"* and prints a number instead, and the agreement badges on the page stop being ours and start being the model's. Nothing has to be edited by hand in between — the code already switches by itself when the files appear.

---

## Before you start

Everything below has been run end to end with the model call replaced by a stub, so the pipeline is known to work: `extractor.py` reads six contracts without crashing, `evaluate.py` scores them and writes `accuracy.json`, `build.py` picks the real readings over the hand-set ones, and the deck prints the measurement. The only untested component is the model.

```
pip install -r ../requirements.txt      # or: pip install litellm pymupdf
```

In **LM Studio**: load a model, then *Developer → Start Server*, port **1234**, and turn **CORS on** (the page needs it, the scripts do not). An instruction-tuned open-weights model around 4B is what the project is written against; anything that can return strict JSON will do.

Check the server answers before running anything else:

```
curl http://localhost:1234/v1/models
```

---

## 1. Three readings of each of the six contracts

```
cd extraction
for f in ../contracts/en/*.txt; do python3 extractor.py "$f"; done
```

Eighteen calls in total. Each one prints the model actually served and, at the end of each contract, how many of the twenty fields were stable across the three readings. Output lands in `extraction/readings/<contract>.json`.

**If a call fails on `response_format`,** the model does not support strict JSON schema. Two ways out, in order: load a model that does, or delete the `response_format` argument in `one_reading()` and add *"Answer with JSON only."* to the end of `PROMPT`. The second is worse and you should say so if asked.

**Run it on the English contracts only.** The quotation shown on screen is never taken from the model: `build.py` re-extracts it from the contract in whatever language is being built, using the article number the model reported. So one English pass gives you all five languages.

## 2. Score it against the ground truth

```
python3 evaluate.py
```

Prints five numbers and writes `extraction/accuracy.json`:

- fields compared — 120, being 20 × 6 contracts
- extracted correctly
- **of which null where the contract states nothing** — eighteen of the hundred and twenty fields are figures no contract mentions: a down payment nobody made, a fee that does not exist, an insurance nobody imposes. The ground truth records them as 0 or false because that is what the arithmetic needs; the prompt tells the model to answer null. Both are right. `evaluate.py` accepts both and prints the count, instead of charging the model fifteen points of invented error — and, since three readings would agree on null, putting all fifteen into the SILENT column
- **wrong but flagged** — the three readings disagreed, so the interface already tells the user to check that line
- **wrong and NOT flagged** — the three readings agreed on the same wrong value. This is the dangerous one, it is the number the whole project turns on (lesson L7 of the project diary), and it is the one to put in front of the room.

## 3. Rebuild both artefacts

```
cd .. && python3 build.py
cd deck && node shots.js && python3 crop.py && node generate.js
```

`build.py` prints which source it used. You want to see:

```
readings from the model (extraction/readings/): 6 of 6 contracts
```

and **not** the `HAND-SET` line. `node shots.js` re-takes the four screenshots from the rebuilt page so the deck shows the real badges rather than the old ones; `generate.js` finds `accuracy.json` and rewrites slide 22 by itself.

## 4. Then retire the staging

```
git rm extraction/variations.json      # only once step 3 prints "6 of 6"
```

`build.py` falls back to that file only when `readings/` is missing, so until the measurement exists it is what makes the demonstration work, and it is declared — in its own first line, in the README and in the page itself. Once real readings exist it becomes dead weight, and a file called *variations* whose own note says *"these are not measurements"* has no reason to stay in a repository that no longer needs it.

---

## Then change four sentences

They are the only places that still say the measurement has not been made.

| Where | What it says now |
|---|---|
| Deck, the risk slide | changes itself from `accuracy.json` — check it, do not retype it |
| Deck, the three-readings slide | *"The particular disagreements in this demonstration are set by hand"* — delete that sentence |
| `README.md`, *Limits, stated* | the first two bullets: the disagreement stops being ours, the measurement stops being absent |
| The page: `lim4` in `template.html` | the sentence in five languages that says the disagreement is hand-set — delete it, then rebuild |
| Project diary, open points | rewrite as measured, and give the number |
| Pitch Q&A | the prepared answer (*"read the note in variations.json"*) becomes a much better one: quote the number |

---

## What it is still not

A measurement on **our own** contracts, which we wrote, with ground truth **we** marked. It tells you whether the pipeline reads a document it was designed around. It does not tell you what happens on a real contract from a real lender, and the risk slide must go on saying so. The corpus problem is lesson L12 of the project diary, and it does not go away.

But there is a difference between *"we have not measured it"* and *"we measured it here, and here is where the measurement stops"*. The second is a result. The first is a confession.
