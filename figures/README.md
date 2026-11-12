# figures/

Written by `python code/make_figures.py`, which `run_all.py` calls. Each figure
exists twice: a vector PDF that the manuscript includes, and a PNG preview for
quick inspection. File names do not match figure numbers, because the figures
were introduced in a different order from the one they appear in; the mapping
is:

| file | figure | content |
|---|---|---|
| `fig1_power.pdf` | Fig. 1 (manuscript) | power to detect a true difference as a function of the multiple of the floor |
| `fig2_ranking.pdf` | Fig. 2 (manuscript) | the five `Phi` values on a logarithmic axis, sea ice drawn as an interval |
| `fig3_floor.pdf` | Fig. 3 (manuscript) | verification floor against claimed magnitude, with the `Phi = 0.1, 1, 10` diagonals |
| `fig5_kernel.pdf` | Fig. S1 (supplement) | two correlation models of the same difference field, and the five floors they imply |
| `fig4_sensitivity.pdf` | Fig. S2 (supplement) | the five `+/- 50 %` sensitivity panels |
| `fig6_design.pdf` | Fig. S3 (supplement) | `Phi` against `n_eff` for the two ends of the measured `sigma_d`, with the campaign, fourteen-winter and 43-month designs marked |
| `fig7_acf.pdf` | Fig. S4 (supplement) | autocorrelation of the 2019-04 CCI--CS2SMOS difference field along `x` and `y`, with the two bandwidth factors |

## Determinism

The plotted quantities are deterministic: they are read from `data/*.csv`.
The PDF bytes are not. matplotlib writes a creation timestamp into every PDF, so
`figures/*.pdf` hashes change between runs even when the plotted data are
identical; the PNG previews have a timestamp-free pixel payload and are stable
for a fixed matplotlib version. Reproducibility here means "the same numbers
are plotted", not "the same bytes are written". The PDFs are included for
convenience and can be regenerated at any time.
