# Publishing this directory as a public code repository

Computers & Geosciences requires a public code repository to exist **at
submission**; a DOI can be added during review, the repository cannot. This
directory is already laid out for a one-command first push. Nothing here
asserts a remote URL: the URL does not exist until you create it, and every
place that must carry it is listed in §5.

## 0. Pre-flight (manual, about ten minutes)

1. Fill `LICENSE`: replace `[YEAR]` and `[COPYRIGHT HOLDER]`.
2. Fill the author placeholders in `manuscript.tex` (author names, affiliations,
   e-mail, CRediT, competing interest, acknowledgements) and in `CITATION.cff`
   and `.zenodo.json` (§1).
3. The repository name is `free-demo` and the URL is
   `https://github.com/dddsx3/free-demo`; both are already used below and in
   every file listed in §5.
4. `legacy_copernicus/` holds the superseded Copernicus class files and the
   unmodified journal template, kept only to document the change of venue. It
   is listed in `.gitignore`, so `git add -A` skips it; nothing in the build
   reads from it. `response_ready_notes.md` is internal referee preparation
   material and is also ignored.
5. Confirm the tree contains no secret, no token and no oversized file:

       git init -b main
       git add -A
       git status --short
       git ls-files | Measure-Object -Line     # expect 51 files, 1.7 MB

   Expect no `data/archive/` inputs beyond the derived CSVs, no `.tex`
   intermediates and no `legacy_copernicus/`. Then delete the temporary `.git`
   if you ran the two commands above for the check only:
   `Remove-Item -Recurse -Force .git`.

## 1. Repository identity (paste into the hosting page)

The five fields below are what a reviewer sees before opening the archive.
They are not cosmetic: the journal's code-availability check reads the
repository landing page, and an empty description reads as an abandoned
deposit.

| field | value to use |
|---|---|
| name | `free-demo` |
| description | Reference implementation and derived tables for a dimensionless testability criterion for geophysical claims (Phi = MDE80 / claim). |
| topics | `geoscience`, `model-evaluation`, `uncertainty`, `reproducibility`, `sea-ice`, `statistics` |
| licence | the licence chosen in step 1 (MIT or BSD-3-Clause are both accepted by the journal) |
| website | leave empty until the DOI exists; then set it to the DOI URL |

`CITATION.cff` (already in the tree) carries

    cff-version: 1.2.0
    message: "If you use this code, cite the manuscript and the archive DOI."
    title: "Phi criterion: reference implementation"
    authors:
      - family-names: "[SURNAME 1]"
        given-names: "[GIVEN 1]"
      - family-names: "[SURNAME 2]"
        given-names: "[GIVEN 2]"
    license: MIT
    repository-code: "https://github.com/dddsx3/free-demo"
    version: "1.0.0"

and `.zenodo.json` carries the same authors, `"license": "MIT"` and
`"keywords"` copied from the topics above. Both files keep the author
placeholders on purpose; do not invent names or a DOI.

## 2. Create an empty remote

The remote exists: `https://github.com/dddsx3/free-demo` (public, default
branch `main`). GitHub created it with an auto-generated `README.md`; the
first push is therefore a rebase onto that stub commit, not a force push.

## 3. One command: initialise, commit, push

From this directory, in PowerShell:

    git init -b main; git add -A; git commit -m "Phi criterion: code, derived tables and manuscript"; git remote add origin https://github.com/dddsx3/free-demo.git; git fetch origin; git rebase --onto origin/main --root main; git push -u origin main

The rebase keeps the remote stub commit and resolves `README.md` in favour of
this repository's README.

## 4. Verify from a clean clone

    cd $env:TEMP
    git clone https://github.com/dddsx3/free-demo phi-check
    cd phi-check
    python -m pip install -r requirements.txt
    python -m pytest code
    python code/run_all.py --no-tex

Acceptance is all four of:

1. `pytest` reports **9 passed**;
2. `run_all.py --no-tex` exits 0 and prints the number check covering the five
   `Phi` values, the 3.447/10.38 cm floors and the archive rows of Table 1;
3. `figures/` holds **seven** `.pdf` files and seven `.png` previews;
4. `git status --short` is empty after the run, i.e. the committed CSVs and
   figures are byte-identical to what the chain reproduces (the PDFs are
   exempt: matplotlib timestamps them).

With a TeX installation, `python code/run_all.py` additionally builds both
`manuscript.pdf` (25 pages) and `supplement.pdf` (15 pages), with 0 overfull
boxes and no unresolved reference in either log. The manuscript body is 5 361
tokens under the C&G counting rule (5 405 with title and authors, limit 5 500);
`REPRO_CHECK.txt`, section 4, records the rule and the margin. If the limit is
re-checked before submission and has moved, `REPRO_CHECK.txt` must be
recomputed, not assumed.

If `run_all.py` reports a headline number moved by more than 0.1 %, the
committed CSVs and the code disagree — do not push that state; fix it first.

Version drift, measured in an anonymous clone on 2026-11-09 with the
resolved newer stack (numpy 2.5.4, pandas 3.1.1, matplotlib 3.11.2,
scipy 1.18.1): the nine tests still pass and every headline number is
unchanged, but `git status` then reports `data/power_curve.csv` and the seven
figures as modified. Compared numerically the power-curve values agree to
2.4 × 10^-16; the CSV bytes differ only in float text, and the figures differ
because of the matplotlib version. Byte-identity is therefore a property of
the pinned reference versions, not of any interpreter that satisfies the
lower bounds.

## 5. Close the loop in the manuscript

The repository URL appears in five places. All five carry
`https://github.com/dddsx3/free-demo`:

| place | status |
|---|---|
| `manuscript.tex`, Code availability | filled, `\url{...}` |
| `cover_letter.md` | filled, plain URL |
| `CITATION.cff` | filled, `repository-code` |
| `.zenodo.json` | filled, `related_identifiers` |
| `REPO_SETUP.md` (this file), `REPRO_CHECK.txt` | filled, clone command |

Then: rebuild (`REPRO_CHECK.txt`, section 2), recompute the sha256
fingerprints (`REPRO_CHECK.txt`, section 5), and push the amended manuscript.
Recompute the word and page counts in `REPRO_CHECK.txt` and `cover_letter.md`
if the availability paragraph changes length.

## 6. Zenodo DOI (after step 3, before or during review)

1. In Zenodo, link the GitHub account and enable the repository.
2. Create a release on GitHub tagged `v1.0.0`; Zenodo mints the DOI from it.
   Release title: `v1.0.0 — Phi criterion, code and derived tables`. Release
   notes: the one-line `run_all.py` command, the seven figures, the nine tests
   and the fact that the transcript is byte-identical to `REPRO_CHECK.txt`
   section 5.
3. Replace `[DOI: ZENODO-TO-BE-ASSIGNED]` in `manuscript.tex` and the
   corresponding line in `REPRO_CHECK.txt`.
4. Rebuild, recompute the hashes, push, and tag the amended commit `v1.0.1`.

The DOI must resolve to the **code archive**, not to the manuscript. The
journal handles the article DOI; this one is for the software.

## What must not be committed

- `__pycache__/`, `.pytest_cache/`, `*.aux`, `*.bbl`, `*.blg`, `*.log`,
  `*.spl` — already in `.gitignore`.
- Observational inputs for the optional worked example: they are third-party
  products, are not redistributed, and `data/archive/` holds only the derived
  CSVs.
- Any credential or personal token.
