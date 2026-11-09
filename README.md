# phi-criterion

Code and derived tables for the manuscript

> A dimensionless verification floor for model assessment: which accuracy claims
> can an observational archive actually resolve?

The paper defines one number,

    Phi = 2.802 * sigma_d / (claim * sqrt(n_eff)) = MDE80 / claim,

where `sigma_d` is the standard deviation of the product–truth difference,
`n_eff` the effective number of independent truth samples and `claim` the
magnitude the assessment asserts. `Phi > 1` means the claim lies below what the
archive can resolve at 80 % power. This repository reproduces every table,
figure and headline number in the manuscript from fixed inputs; it downloads
no observational data.

## Install

    git clone https://github.com/dddsx3/free-demo
    cd free-demo
    python -m pip install -r requirements.txt

Python 3.10 or newer. The reference run used Python 3.14.2 with numpy 2.4.1,
pandas 3.0.0, matplotlib 3.10.8 and scipy 1.17.0; `requirements.txt` states
lower bounds so that the install also works on older interpreters.

## Reproduce everything with one command

From the repository root:

    python code/run_all.py

This runs the arithmetic, checks that no headline number has moved by more than
0.1 % from the value printed in the manuscript, writes the seven derived tables
to `data/`, writes the seven figures to `figures/`, and — if `pdflatex` and
`bibtex` are on `PATH` — builds `manuscript.pdf`. The process exits non-zero if
any stage fails.

Options:

| command | effect |
|---|---|
| `python code/run_all.py` | full chain, including the PDF |
| `python code/run_all.py --no-tex` | numbers and figures only |
| `python code/run_all.py --refs` | full chain plus a DOI re-resolution audit (needs network) |
| `python code/run_all.py --refs-only` | reference audit only |
| `python code/run_all.py --archive --p1 DIR` | also runs the optional worked example on a real archive |

## Tests

    python -m pytest code

Nine tests cover the five reported `Phi` values, the three closure identities
(`n_eff` = 325.2, 138.6, 20 668), the integral-scale rule, the monotonicity of
`Phi` in `n_eff`, and the two failure modes of the worked example.

## Optional: worked example on a real archive

`code/archive_example.py` takes the one step that the five tabulated domains
leave open — it estimates `sigma_d` and the correlation bandwidth from two
coincident monthly thickness fields instead of assuming them:

    python code/archive_example.py --p1 DIR_WITH_MONTHLY_FIELDS

`DIR_WITH_MONTHLY_FIELDS` must contain `p1_cci_monthly.npz` and
`p1_monthly_cells.npz`. Those files are derived from the ESA CCI and CS2SMOS
distributions and are **not** redistributed here, so this stage is optional and
skipped by default. It writes `data/archive/` (per-month `sigma_d`, the
autocorrelation, `n_eff` and the `Phi` rows). The file header of the script
states the expected values for the reference archive.

## Layout

    code/
      phi_core.py         constants, three closures, Phi table, sensitivity
      make_figures.py     the seven figures
      archive_example.py  optional worked example (not a library)
      run_all.py          one-command chain
      test_phi_core.py    nine regression tests
      verify_refs.py      DOI/title audit of refs.bib (network)
    data/                 derived tables written by the chain, see data/README.md
    figures/              figure PDFs and PNG previews, see figures/README.md
    manuscript.tex        manuscript source (elsarticle, author-year)
    refs.bib              bibliography, 60 entries, all cited
    REPRO_CHECK.txt       environment, commands, expected output, fingerprints
    REPO_SETUP.md         how to publish this directory as a public repository
    legacy_copernicus/    superseded Copernicus class package and template

`legacy_copernicus/` records that an earlier revision was prepared for
Geoscientific Model Development: it holds `copernicus.cls`, `.bst`, `.cfg` and
the unmodified journal template. Nothing in the build uses it, it is listed in
`.gitignore`, and it is **not** part of the repository; it exists on disk only
so that the change of venue stays auditable.

## What is not in this repository

- No observational granule: the five domains use literature values that are
  fixed constants in `code/phi_core.py`, each with a citable source.
- No credentials, no tokens, no personal data.
- `manuscript.pdf` is a build artefact; `REPRO_CHECK.txt` records its
  fingerprint, so a rebuilt PDF that differs in bytes is expected.

## License

MIT, see `LICENSE`. Replace the copyright holder placeholder before publishing.

## Citation

The archived release is to be deposited on Zenodo; the DOI placeholder in
`manuscript.tex` and in `REPRO_CHECK.txt` is filled only after the first public
push. Until then, cite the manuscript.
