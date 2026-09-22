#!/usr/bin/env python3
"""Fact check: compare a tailored resume against the master resume.

Usage:
    python3 scripts/check_claims.py "<master.md>" "<tailored.md>"

Exit code 0 = passed (warnings may still be listed for review).
Exit code 1 = FAILED: something in the tailored resume is not in the master.

What it enforces (FAIL):
  - every number (percent, dollar amount, count, year) exists in the master
  - every acronym / all-caps term (SOC, CAE, AWS, ...) exists in the master
  - section headings, employer lines, title/date lines, company descriptions,
    education and certification lines are copied exactly from the master
  - every Core Competencies item exists in the master
What it reports for review (WARN):
  - capitalized terms that are not in the master (possible new names or tools)
  - bullets or sentences that were reworded heavily compared to the closest
    master line, shown side by side so the meaning can be checked by a person
Uses only the Python standard library.
"""
import difflib
import re
import sys


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def plain(s):
    """Markdown line -> plain text."""
    s = re.sub(r"^\s*(#{1,6}\s+|-\s+)", "", s)
    s = s.replace("**", "").replace("*", "").replace("_", " ")
    s = s.replace("’", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s).strip()


def norm(s):
    return plain(s).lower()


NUM_RE = re.compile(r"\$?\d[\d,]*(?:\.\d+)?\s?(?:%|[MKB]\b)?\+?")


def numbers(text):
    out = set()
    for m in NUM_RE.finditer(plain(text)):
        tok = m.group(0).replace("$", "").replace(",", "").replace(" ", "").rstrip("+")
        out.add(tok.upper())
    return out


def acronyms(text):
    out = set()
    for line in text.splitlines():
        if line.startswith("#"):
            continue  # headings are all caps by design; checked separately
        for m in re.finditer(r"\b[A-Z][A-Z0-9]*[A-Z][A-Z0-9]*\b", plain(line)):
            out.add(m.group(0))
    return out


def cap_terms(text):
    """Capitalized words that are not at the start of a sentence or bullet."""
    out = set()
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        p = plain(line)
        for m in re.finditer(r"(?<![.:!?]\s)(?<!^)\b[A-Z][a-z]+(?:[- ][A-Z][a-z]+)*", p):
            out.add(m.group(0))
    return out


def lines_of(text, pred):
    return [l.rstrip() for l in text.splitlines() if pred(l)]


def is_title_line(l):
    """**Job Title | 2022 - 2026** (competency lines carry a ':**' label instead)."""
    return l.startswith("**") and "|" in l and ":**" not in l


def is_desc_line(l):
    s = l.strip()
    return s.startswith("*") and not s.startswith("**") and s.endswith("*")


def competency_items(text):
    items = []
    in_comp = False
    for l in text.splitlines():
        if l.startswith("## "):
            in_comp = "COMPETENC" in l.upper()
            continue
        if in_comp and l.startswith("**") and ":**" in l:
            body = l.split(":**", 1)[1]
            items += [norm(x) for x in body.split("|") if x.strip()]
    return items


def section_lines(text, keyword):
    out, on = [], False
    for l in text.splitlines():
        if l.startswith("## "):
            on = keyword in l.upper()
            continue
        if on and l.strip():
            out.append(l.rstrip())
    return out


def sentences(text):
    """Bullets and prose sentences from the body, for the reword report."""
    out = []
    for l in text.splitlines():
        s = l.strip()
        if not s or s.startswith("#") or is_title_line(s) or is_desc_line(s):
            continue
        if s.startswith("**") and ":**" in s and "|" in s:
            continue  # competency lines: reordering is allowed, items are checked separately
        for part in re.split(r"(?<=[.!?])\s+(?=[A-Z*])", s):
            if len(plain(part)) > 25:
                out.append(plain(part))
    return out


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    master, tailored = read(sys.argv[1]), read(sys.argv[2])
    fails, warns = [], []

    # 1. numbers
    m_nums = numbers(master)
    for n in sorted(numbers(tailored) - m_nums):
        fails.append(f"Number not in master: {n}")

    # 2. acronyms / all-caps terms
    m_text = plain(master)
    for a in sorted(acronyms(tailored)):
        if a not in m_text:
            fails.append(f"Acronym or all-caps term not in master: {a}")

    # 3. structure copied exactly
    m_lines = {l.rstrip() for l in master.splitlines()}
    m_heads = lines_of(master, lambda l: l.startswith("## "))
    t_heads = lines_of(tailored, lambda l: l.startswith("## "))
    for h in t_heads:
        if h not in m_heads:
            fails.append(f"Section heading not in master: {h}")
    order = [h for h in m_heads if h in t_heads]
    if order != [h for h in t_heads if h in m_heads]:
        fails.append("Sections are in a different order than the master")
    for pred, label in [
        (lambda l: l.startswith("# ") or l.startswith("### "), "Name or employer line"),
        (is_title_line, "Title/date line"),
        (is_desc_line, "Company description"),
    ]:
        for l in lines_of(tailored, pred):
            if l not in m_lines:
                fails.append(f"{label} changed from master: {l}")
    for key in ("EDUCATION",):
        for l in section_lines(tailored, key):
            if l not in m_lines:
                fails.append(f"Education/recognition line changed from master: {l}")
    m_contact = [l for l in master.splitlines()[:6] if "@" in l]
    t_contact = [l for l in tailored.splitlines()[:6] if "@" in l]
    if m_contact and t_contact and m_contact[0].strip() != t_contact[0].strip():
        fails.append("Contact line changed from master")

    # 4. competencies must be existing items
    m_items = set(competency_items(master))
    for it in competency_items(tailored):
        if it not in m_items:
            fails.append(f"Core Competencies item not in master: {it}")

    # 5. warnings: new capitalized terms
    m_low = m_text.lower()
    for t in sorted(cap_terms(tailored)):
        if t.lower() not in m_low:
            warns.append(f"Capitalized term not in master (check it is not a new claim): {t}")

    # 6. warnings: heavy rewording, shown against the closest master line
    m_sents = sentences(master)
    for s in sentences(tailored):
        if s in m_sents:
            continue
        best = max(m_sents, key=lambda m: difflib.SequenceMatcher(None, s.lower(), m.lower()).ratio())
        r = difflib.SequenceMatcher(None, s.lower(), best.lower()).ratio()
        if r < 0.6:
            warns.append(f"Reworded ({int(r * 100)}% similar). Check the claim is the same.\n"
                         f"      tailored: {s}\n      master:   {best}")

    print("FACT CHECK:", "FAILED" if fails else "PASSED")
    for f in fails:
        print("  FAIL", f)
    for w in warns:
        print("  WARN", w)
    if not fails and not warns:
        print("  Every number, name and structural line matches the master.")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
