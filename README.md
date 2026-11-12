# Verification floor Phi

A claim about model error can only be tested if the archive used to test it is
informative enough. This repository implements the dimensionless floor that says
how informative it has to be,

    Phi = 2.802 * sigma_d / (claim * sqrt(n_eff)),

together with the archive recomputation for Arctic sea-ice thickness thickness
that supplies its hardest case, and the sensitivity grids reported in the paper.

`Phi > 1` means the claim cannot be verified by this archive. `Phi < 1` means it
can be — not that it is right.

## What is here

    code/        the whole chain, one entry point
      phi_core.py           Phi, MDE, effective sample size, sensitivity grids
      archive_recompute.py  sea-ice archive: kappa, n_eff, the two kernels
      run_all.py            runs everything, checks every number, writes figures
      make_figures.py       the seven figures
      test_phi_core.py      ten regression tests
    data/        every table the paper quotes, as CSV, with data/README.md
    figures/     the figures (PDF)
    manuscript.tex, supplement.tex, refs.bib   the submission-side sources
    REPRO_CHECK.txt   environment, run order, expected values

## Run it

    pip install numpy scipy pandas matplotlib pytest
    python code/run_all.py            # arithmetic, number check, figures, both PDFs
    python -m pytest code             # ten tests
    python code/run_all.py --refs     # optional: re-resolve every DOI

`run_all.py` exits non-zero if any headline number moves by more than 0.1 % from
the value printed in the manuscript, so it doubles as a submission gate.

## The archive example

The sea-ice section uses two monthly product fields that are not redistributed
here. Without them, `archive_example.py` falls back to the two CSVs those fields
produced (`data/archive/sigma_by_month.csv`, `data/archive/acf.csv`) and
recomputes the same summary:

    python code/archive_recompute.py

Every measured number in the paper reproduces that way.

## Licence and citation

Code MIT (see LICENSE); derived tables CC BY 4.0. If you use this, please cite
the article and this repository (CITATION.cff).
