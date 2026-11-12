# data/

Everything in this directory is written by `python code/run_all.py` (or by
`python code/archive_example.py` for the `archive/` subdirectory), with three
exceptions that are committed with the repository because they summarise a
third-party archive that is not redistributed: `phi_archive_design.csv`,
`archive_neff_months.csv` and `archive_acf_curve.csv`. All tables are UTF-8 CSV
with a header row. Units are given in the manuscript, not in the column names.

| file | contents | where it appears in the paper |
|---|---|---|
| `phi_master.csv` | one row per domain: raw count, `n_eff`, closure rule, `sigma_d` and source note, claim and source note, `MDE80`, `Phi`, verdict | Table 1 (master) |
| `phi_archive_design.csv` | the same domain under three designs (campaign, 14 winters, 43 months) at both ends of `sigma_d` | the two archive rows of Table 1 and Fig. S3 |
| `archive_neff_months.csv` | per-month valid cells, both bandwidth factors, `n_eff` and `sigma_d` for the four months quoted | Table S4 |
| `archive_acf_curve.csv` | the 2019-04 CCI--CS2SMOS difference-field autocorrelation along `x` and `y`, 31 lags | Fig. S4 |
| `phi_kernel_bounds.csv` | `Phi` for each (kernel, design) combination of the sea-ice family | Table S2 and the sea-ice interval |
| `phi_variants.csv` | the alternative designs kept out of the main ranking | Table S2 and Table S3 |
| `phi_sensitivity.csv` | the 25-cell `+/- 50 %` box, 25 rows per domain | Table S3 and Fig. S2 |
| `phi_sensitivity_kernel.csv` | the same box applied to the empirical-kernel sea-ice bound and the 18-site soil-moisture variant | lower rows of Table S3 |
| `phi_robustness.csv` | nominal, axis-wise and joint ranges plus the verdict per domain | the four diagnostics of Sect. S6 |
| `power_curve.csv` | power as a function of the non-centrality `k` for a grid of `Phi` | Fig. 1 |
| `ref_check.csv` | per-entry outcome of the DOI/title audit: key, DOI, year, title, journal, similarity score, status | REPRO_CHECK.txt, section 4 |
| `ref_rejected.csv` | candidates that failed the audit and were **not** used, with the reason | audit trail only |

## archive/

Written only when the optional worked example is run
(`python code/archive_example.py --p1 DIR`), because it needs two monthly
product fields that are not redistributable:

| file | contents |
|---|---|
| `sigma_by_month.csv` | per-month `sigma_d`, mean difference and common-cell count for the CCI minus CS2SMOS thickness difference |
| `acf.csv` | along-track and across-track autocorrelation, the two bandwidth factors and `n_eff` for four months |
| `archive_example.json` | the same quantities plus the `Phi` rows, machine-readable |

The input fields live outside this repository. No observational granule and no
third-party product are redistributed here.

## Regenerating

`python code/run_all.py --no-tex` rewrites every file above except `archive/`
and the three committed `archive_*`/`phi_archive_design.csv` tables in a few
seconds. The hashes in `REPRO_CHECK.txt`, section 5, identify the expected
content; if a CSV changes, the chain exits non-zero when a headline number moves
by more than 0.1 %.
