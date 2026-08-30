#!/usr/bin/env python3
"""
Builds clausola.html — one standalone page, five languages.

Inputs
    template.html                 interface, i18n strings and calculations
    contracts/<lang>/*.txt        the same three contracts in en, fr, de, it, es
    extraction/fields.json        values + the LOCATION of each clause (language-independent)
    extraction/variations.json    the differences of readings 2 and 3

The quotation shown next to every extracted value is **not stored**: it is pulled
out of the contract of the language you are reading, at build time, by locating
the article number. That is why clicking an item can always highlight the exact
sentence — in any of the five languages — instead of a translated paraphrase.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LANGS = ["en", "fr", "de", "it", "es"]

TITLES = {
    "01_personal_loan": {
        "en": "Personal loan · offer A — CHF 12'000 over 36 months",
        "fr": "Prêt personnel · offre A — CHF 12'000 sur 36 mois",
        "de": "Privatkredit · Angebot A — CHF 12'000 über 36 Monate",
        "it": "Prestito personale · offerta A — CHF 12'000 in 36 mesi",
        "es": "Préstamo personal · oferta A — CHF 12'000 a 36 meses"},
    "01b_personal_loan": {
        "en": "Personal loan · offer B — CHF 12'000 over 48 months",
        "fr": "Prêt personnel · offre B — CHF 12'000 sur 48 mois",
        "de": "Privatkredit · Angebot B — CHF 12'000 über 48 Monate",
        "it": "Prestito personale · offerta B — CHF 12'000 in 48 mesi",
        "es": "Préstamo personal · oferta B — CHF 12'000 a 48 meses"},
    "02_car_lease": {
        "en": "Car lease · offer A — CHF 349 a month for 48 months",
        "fr": "Leasing auto · offre A — CHF 349 par mois pendant 48 mois",
        "de": "Autoleasing · Angebot A — CHF 349 pro Monat über 48 Monate",
        "it": "Leasing auto · offerta A — CHF 349 al mese per 48 mesi",
        "es": "Leasing de coche · oferta A — CHF 349 al mes durante 48 meses"},
    "02b_car_lease": {
        "en": "Car lease · offer B — CHF 319 a month for 48 months",
        "fr": "Leasing auto · offre B — CHF 319 par mois pendant 48 mois",
        "de": "Autoleasing · Angebot B — CHF 319 pro Monat über 48 Monate",
        "it": "Leasing auto · offerta B — CHF 319 al mese per 48 mesi",
        "es": "Leasing de coche · oferta B — CHF 319 al mes durante 48 meses"},
    "03_motor_policy": {
        "en": "Motor policy · offer A — CHF 68 a month, renews by itself",
        "fr": "Police auto · offre A — CHF 68 par mois, reconduction tacite",
        "de": "Autoversicherung · Angebot A — CHF 68 pro Monat, verlängert sich automatisch",
        "it": "Polizza auto · offerta A — CHF 68 al mese, rinnovo tacito",
        "es": "Póliza de coche · oferta A — CHF 68 al mes, prórroga tácita"},
    "03b_motor_policy": {
        "en": "Motor policy · offer B — CHF 63 a month, five-year discount tie-in",
        "fr": "Police auto · offre B — CHF 63 par mois, engagement de cinq ans",
        "de": "Autoversicherung · Angebot B — CHF 63 pro Monat, fünf Jahre Rabattbindung",
        "it": "Polizza auto · offerta B — CHF 63 al mese, vincolo sconto di cinque anni",
        "es": "Póliza de coche · oferta B — CHF 63 al mes, permanencia de cinco años"},
}
MAXQ = 240


def marker(where):
    """'Art. 5.2' -> '5.2';  'A.3' -> 'A.3';  'B.4.2' -> 'B.4.2'."""
    if not where:
        return None
    m = re.search(r"\b([A-Z]\.)?\d+(\.\d+)*\b", where)
    return m.group(0) if m else None


def extract_quote(text, where):
    """Pull the literal sentence out of THIS language's contract."""
    if not where:
        return None
    if where.lower() in ("heading", "intestazione"):
        return text.strip().splitlines()[0].strip()
    tok = marker(where)
    if not tok:
        return None
    lines = text.splitlines()
    pat = re.compile(r"^\s*" + re.escape(tok) + r"[\s)]")
    for i, line in enumerate(lines):
        if pat.match(line):
            chunk = [line.strip()]
            for nxt in lines[i + 1:]:
                if not nxt.strip():
                    break
                if re.match(r"^\s*([A-Z]\.)?\d+(\.\d+)*[\s)]", nxt) or re.match(r"^\S", nxt):
                    break
                chunk.append(nxt.strip())
            q = re.sub(r"\s+", " ", " ".join(chunk)).strip()
            return q[:MAXQ].rstrip() + "…" if len(q) > MAXQ else q
    return None


def reading_with_variants(base, variants):
    out = json.loads(json.dumps(base))
    for field, value in variants.items():
        if field not in out:
            out[field] = {"value": value, "quote": None, "where": None}
            continue
        out[field] = dict(out[field])
        out[field]["value"] = value
        if value is None:
            out[field]["quote"] = None
            out[field]["where"] = None
    return out


READINGS = os.path.join(HERE, "extraction", "readings")


def real_readings(key, text):
    """Three readings actually produced by extractor.py, if they exist.

    The model reports a value and a location. The quotation is not taken from
    the model: it is pulled out of the contract in the language being built,
    from that location, exactly as it is for the hand-set demo. So a real
    reading is multilingual for free, and a quotation is always a substring of
    the document on screen.

    If this directory is empty the build falls back to extraction/variations.json,
    which is hand-set and says so, and the build prints which one it used.
    """
    path = os.path.join(READINGS, key + ".json")
    if not os.path.exists(path):
        return None
    runs = json.load(open(path, encoding="utf-8"))
    out = []
    for run in runs:
        m = {}
        for f, d in run.items():
            if not isinstance(d, dict):
                continue
            value, where = d.get("value"), d.get("where")
            m[f] = {"value": value,
                    "quote": extract_quote(text, where) if value is not None else None,
                    "where": where}
        out.append(m)
    return out


def main():
    fields = json.load(open(os.path.join(HERE, "extraction/fields.json"), encoding="utf-8"))
    variations = json.load(open(os.path.join(HERE, "extraction/variations.json"), encoding="utf-8"))

    data, missing, used_real = {}, [], set()
    for lang in LANGS:
        data[lang] = {}
        for key, titles in TITLES.items():
            path = os.path.join(HERE, "contracts", lang, key + ".txt")
            text = open(path, encoding="utf-8").read()
            base = {}
            for f, d in fields[key].items():
                if f.startswith("_"):
                    # contract metadata, not one of the twenty extracted fields:
                    # carried through so the arithmetic can honour a condition the
                    # schema does not hold (personal loan, Art. 5.3)
                    if not isinstance(d, dict):
                        base[f] = {"value": d, "quote": None, "where": None}
                    continue
                q = extract_quote(text, d["where"]) if d["value"] is not None else None
                if d["value"] is not None and d["where"] and not q:
                    missing.append(f"{lang}/{key}: {f} ({d['where']})")
                base[f] = {"value": d["value"], "quote": q, "where": d["where"]}
            real = real_readings(key, text)
            if real is not None:
                readings = real
                used_real.add(key)
            else:
                var = variations.get(key, {})
                readings = [base,
                            reading_with_variants(base, var.get("run2", {})),
                            reading_with_variants(base, var.get("run3", {}))]
            data[lang][key] = {"title": titles[lang], "text": text, "readings": readings}

    template = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    if "/*__DATA__*/{}" not in template:
        raise SystemExit("placeholder __DATA__ not found in template.html")
    final = template.replace("/*__DATA__*/{}", json.dumps(data, ensure_ascii=False, indent=1))

    out = os.path.join(HERE, "clausola.html")
    open(out, "w", encoding="utf-8").write(final)
    print(f"written {out} — {len(final)} bytes, {len(LANGS)} languages")
    staged = [k for k in TITLES if k not in used_real]
    if used_real:
        print(f"readings from the model (extraction/readings/): {len(used_real)} of {len(TITLES)} contracts")
    if staged:
        print(f"readings HAND-SET (extraction/variations.json): {len(staged)} of {len(TITLES)} contracts")
        print("    -> the disagreement shown for these is illustrative, not measured.")
        print("    -> run extraction/extractor.py on each of them to replace it.")
    if missing:
        print(f"\n{len(missing)} clause(s) could not be located in the contract text:")
        for m in missing:
            print("   ", m)
    else:
        print("every clause located in every language")

    # The claim on the slide is stronger than "located": every quotation must be
    # the clause itself, character for character, once line wrapping is set aside.
    checked = inexact = 0
    for lang in LANGS:
        for key, doc in data[lang].items():
            norm = re.sub(r"\s+", " ", doc["text"])
            for f, d in doc["readings"][0].items():
                q = d.get("quote")
                if not q:
                    continue
                checked += 1
                if q.rstrip("…") not in norm:
                    inexact += 1
                    print(f"    INEXACT {lang}/{key}: {f}")
    print(f"exact quotations: {checked - inexact}/{checked}"
          + ("" if inexact else "  — every quotation is a verbatim clause of the document"))


if __name__ == "__main__":
    main()
