#!/usr/bin/env python
# coding: utf-8
"""
Publication markdown generator for academicpages, driven by a Zotero
(Better BibTeX) .bib export.

Workflow
--------
1.  In Zotero, keep your own publications in one collection. With the
    Better BibTeX plugin, right-click the collection -> "Export Collection"
    -> format "Better BibTeX", check "Keep updated". Point it at
    ``zotero_publications.bib`` in the repo root. The file now refreshes
    automatically whenever you add a paper.
2.  Run this script from the repo root:  ``python markdown_generator/pubsFromBib.py``
3.  Commit the new/changed files in ``_publications/``.

Design choices
--------------
* Citations are rendered in a single consistent **AMA** style.
* Your name (``Benson``) is bolded in every citation.
* ``@incollection`` (book chapters) are handled, not just journal articles.
* Each generated file records ``doi`` and ``zotero_key`` in its front matter.
* DEDUP: before writing, the script scans existing ``_publications/*.md``.
  If a file already references the same ``zotero_key`` or ``doi``, the entry
  is SKIPPED. This (a) prevents duplicate pages like the old mammography
  double-entry, and (b) preserves any short, hand-curated permalinks/slugs
  you have already created. Only genuinely new papers are written. Delete a
  file if you want it regenerated.

Requires: ``pip install bibtexparser``
"""

import os
import re
import sys
import glob
import bibtexparser
from bibtexparser.bparser import BibTexParser

# --- paths (robust to being run from repo root or markdown_generator/) -------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BIB = os.path.join(REPO, "zotero_publications.bib")
PUBDIR = os.path.join(REPO, "_publications")

# Your surname, as it appears in the bib, to bold + standardize.
MY_LASTNAME = "Benson"
MY_INITIALS = "JS"

# Journals whose indexed title is unwieldy -> cleaner display name.
JOURNAL_CLEAN = {
    "Medical Decision Making: An International Journal of the Society for "
    "Medical Decision Making": "Medical Decision Making",
}


# ---------------------------------------------------------------------------
def delatex(s):
    """Strip BibTeX/LaTeX cruft and normalize punctuation/quotes."""
    if not s:
        return ""
    s = s.replace("``", '"').replace("''", '"')
    s = (s.replace("\\&", "&").replace("$\\geq$", "≥")
           .replace("$<$", "<").replace("$>$", ">").replace("\\$", "$"))
    # accent commands (\'a  \"u  \^o  \~n  \`e  \=a  \.a, with optional braces)
    s = re.sub(r"\\[\'\"\^\`~=.]\s*\{?([A-Za-z])\}?", r"\1", s)
    s = re.sub(r"\\textsc\s*", "", s)
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)        # drop remaining \commands
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\s+([:;.,?!])", r"\1", s)       # no space before punctuation
    s = re.sub(r"\s+", " ", s).strip()
    return s


def initials(firsts):
    out = ""
    for tok in re.split(r"[\s.]+", firsts):
        tok = tok.strip("{}")
        if tok:
            out += tok[0].upper()
    return out


def fmt_authors(author_field):
    """Render an AMA author list; bold the site owner; cap at 6 (+ et al.)."""
    persons = [p for p in re.split(r"\s+and\s+", author_field)]
    names = []
    for p in persons:
        p = p.strip()
        if "," in p:
            last, first = p.split(",", 1)
        elif " " in p:
            first, last = p.rsplit(" ", 1)
        else:
            last, first = p, ""
        last, ini = delatex(last), initials(delatex(first))
        if last == MY_LASTNAME:
            names.append((MY_LASTNAME, MY_INITIALS, True))
        elif "broek-altenburg" in last.lower():          # collapse name variants
            names.append(("Van Den Broek-Altenburg", "EM", False))
        else:
            names.append((last, ini, False))

    def render(n):
        s = f"{n[0]} {n[1]}".strip()
        # HTML <strong> (not markdown **) so it renders in the Liquid
        # templates, which output the citation as raw text.
        return f"<strong>{s}</strong>" if n[2] else s

    if len(names) > 6:
        shown = names[:3]
        if not any(n[2] for n in shown):     # always keep the owner visible
            for n in names[3:]:
                if n[2]:
                    shown = names[:2] + [n]
                    break
        return ", ".join(render(n) for n in shown) + ", et al."
    return ", ".join(render(n) for n in names)


def authors_list(author_field):
    """Full 'Last, First' names for the front-matter authors: list (drives
    Highwire/Scholar citation_author meta tags)."""
    out = []
    for p in re.split(r"\s+and\s+", author_field):
        p = p.strip()
        if "," in p:
            last, first = p.split(",", 1)
        elif " " in p:
            first, last = p.rsplit(" ", 1)
        else:
            last, first = p, ""
        last, first = delatex(last), delatex(first)
        if "broek-altenburg" in last.lower():
            last, first = "Van Den Broek-Altenburg", "Eline M."
        if last == MY_LASTNAME:
            last, first = MY_LASTNAME, "Jamie S."
        out.append(f"{last}, {first}".strip().rstrip(","))
    return out


def _join(a, b):
    a = a.rstrip()
    return (a + " " + b) if a.endswith((".", "?", "!")) else (a + ". " + b)


def build_citation(e):
    """Return (citation, venue, doi) in AMA style for a bibtexparser entry."""
    authors = fmt_authors(e["author"])
    title = delatex(e["title"]).rstrip(".")
    venue = delatex(e.get("journal") or e.get("booktitle", ""))
    venue = JOURNAL_CLEAN.get(venue, venue)
    year = e.get("year", "")
    vol = e.get("volume")
    num = e.get("number")
    pages = (e.get("pages", "") or "").replace("--", "-")
    if "-" in pages:
        lo, hi = pages.split("-", 1)
        if lo == hi:
            pages = lo
    doi = e.get("doi")

    if e.get("ENTRYTYPE") == "incollection":
        tail = f"In: {venue}. {e.get('publisher', '')}; {year}:{pages}.".replace("  ", " ")
    elif vol:
        vip = f"{vol}" + (f"({num})" if num else "") + (f":{pages}" if pages else "")
        tail = f"{venue}. {year};{vip}."
    else:
        mon = e.get("month", "").capitalize()
        tail = f"{venue}. Published online {mon} {year}.".replace("  ", " ")

    cite = _join(_join(authors, title), tail)
    if doi:
        cite += f" doi:{doi}"
    return re.sub(r"\s+", " ", cite).strip(), venue, doi


def slugify(title):
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", delatex(title)).lower()
    words = [w for w in s.split() if w][:6]
    return "-".join(words)


def existing_keys_and_dois():
    keys, dois = set(), set()
    for fn in glob.glob(os.path.join(PUBDIR, "*.md")):
        txt = open(fn, encoding="utf-8").read()
        m = re.search(r"(?m)^zotero_key:\s*'?([^'\n]+)", txt)
        if m:
            keys.add(m.group(1).strip())
        for m in re.finditer(r"10\.\d{4,9}/[^\s'\")]+", txt):   # any DOI anywhere
            dois.add(m.group(0).strip().lower())
    return keys, dois


def month_to_num(mraw):
    if not mraw:
        return "01"
    from time import strptime
    try:
        return "%02d" % strptime(mraw[:3], "%b").tm_mon
    except ValueError:
        return mraw.zfill(2)[-2:]


def main():
    if not os.path.exists(BIB):
        sys.exit(f"Bib file not found: {BIB}")
    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    with open(BIB, encoding="utf-8") as f:
        db = bibtexparser.load(f, parser=parser)

    seen_keys, seen_dois = existing_keys_and_dois()
    created = skipped = 0

    for e in db.entries:
        if "author" not in e or "title" not in e or "year" not in e:
            print(f"SKIP (missing fields): {e.get('ID')}")
            continue
        key = e["ID"]
        doi = (e.get("doi") or "").lower()
        if key in seen_keys or (doi and doi in seen_dois):
            skipped += 1
            continue

        cite, venue, doi_raw = build_citation(e)
        date = f"{e['year']}-{month_to_num(e.get('month', ''))}-01"
        permalink_slug = f"{date}-{slugify(e['title'])}"
        title = delatex(e["title"])
        paperurl = f"https://doi.org/{doi_raw}" if doi_raw else ""

        fm = [
            "---",
            f'title: "{title}"',
            "collection: publications",
            f"permalink: /publication/{permalink_slug}",
            "excerpt: ''",
            f"date: {date}",
            f"venue: '{venue}'",
        ]
        if paperurl:
            fm.append(f"paperurl: '{paperurl}'")
            fm.append(f"doi: '{doi_raw}'")
        fm.append(f"zotero_key: '{key}'")
        fm.append("authors:")
        for a in authors_list(e["author"]):
            fm.append(f'  - "{a}"')
        fm.append("citation: '%s'" % cite.replace("'", "''"))
        fm.append("---")
        body = ""
        if paperurl:
            body = f'\n<a href="{paperurl}" target="_blank">Access the paper here.</a>\n'
        md = "\n".join(fm) + "\n" + body

        out = os.path.join(PUBDIR, f"{permalink_slug}.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(md)
        created += 1
        seen_keys.add(key)
        if doi:
            seen_dois.add(doi)
        print(f"CREATED {os.path.basename(out)}")

    print(f"\nDone. {created} created, {skipped} already on site (skipped).")


if __name__ == "__main__":
    main()
