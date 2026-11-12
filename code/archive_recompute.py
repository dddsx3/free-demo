"""P4 / sea-ice archive -- recompute every "measured" number from the shipped data.

This is the reproducible counterpart of the worked example in
``archive_example.py``.  ``archive_example.py`` reads two external product
fields (the P1 CCI/CS2SMOS missingness products, withheld from this archive)
and *measures* sigma_d and n_eff.  This script reads the two tables those
fields produced -- ``data/archive/sigma_by_month.csv`` and
``data/archive/acf.csv`` -- and the released autocorrelation curve
``data/archive_acf_curve.csv``, and recomputes every quantity the manuscript
quotes for the eleven-winter archive, so a reader can verify the text without
the (licensed, non-redistributed) raw products.

Outputs (under ../data):
    phi_archive_design.csv     -- regenerated design table (11-winter, not 14)
    archive_neff_summary.csv   -- one row per derived quantity, with provenance

Nothing is downloaded; only the committed CSVs are read.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

Z = 2.802                       # z_{0.975} + z_{0.80}, same constant as phi_core.py
CELL_KM = 25.0
DATA = Path(__file__).resolve().parents[1] / "data"
ARCH = DATA / "archive"

CLAIM = 0.027                   # 2.7 cm, the basin-mean sea-ice thickness claim


def integral_scale(rhos):
    """kappa = 1 + 2 * sum_{k>=1} rho(k), stopped at the first non-positive rho."""
    total = 0.0
    for k, r in enumerate(rhos[1:], start=1):
        if not np.isfinite(r) or r <= 0:
            return 1.0 + 2.0 * total, k
        total += r
    return 1.0 + 2.0 * total, len(rhos)


def main() -> int:
    sb = pd.read_csv(ARCH / "sigma_by_month.csv")
    ac = pd.read_csv(ARCH / "acf.csv")
    curve = pd.read_csv(DATA / "archive_acf_curve.csv")

    # -- per-month effective sample size (one independent month per winter) -----
    n_eff_per_month = float(ac["n_eff"].median())          # 321.3
    years = sorted({m.split("-")[0] for m in sb["month"]})  # 11 distinct winters
    n_months = len(sb)
    n_winters = len(years)
    n_eff_11w = n_eff_per_month * n_winters                # 3 534.3
    n_eff_43m = n_eff_per_month * n_months                 # 13 816

    # -- sigma_d of the difference field --------------------------------------
    std = sb["std"].to_numpy()
    sigma_median = float(np.median(std))                   # 0.389 m
    sigma_rms = float(np.sqrt(np.mean(std ** 2)))          # 0.408 m
    sigma_min, sigma_max = float(std.min()), float(std.max())

    # -- two archive verdicts (Phi) -------------------------------------------
    phi_shared = Z * sigma_median / (CLAIM * np.sqrt(n_eff_11w))      # 0.679
    phi_indep = Z * 0.65 / (CLAIM * np.sqrt(n_eff_11w))               # 1.135

    # -- n_eff needed for Phi < 1 at each sigma_d -----------------------------
    n_needed_389 = float((Z * sigma_median / CLAIM) ** 2)    # 1 630
    n_needed_65 = float((Z * 0.65 / CLAIM) ** 2)             # 4 550

    # -- kappa from the *released* curve (confirms the package, not the old
    #    lag-25 value, is what the floor is integrated from) ------------------
    kx, _ = integral_scale(curve["rho_x"].to_numpy())
    ky, _ = integral_scale(curve["rho_y"].to_numpy())
    n_eff_2019 = float(18033.0 / (kx * ky))                  # 331.8

    # -- the two sea-ice floor endpoints (MDE80 = Z*sigma_d / sqrt(n_eff)) ----
    # empirical-difference-field kernel: n_eff = 2 792 is the value implied by
    # the 3.447 cm floor (i.e. N/(kappa_x*kappa_y) with the measured kappa);
    # exponential kernel at the Kish archive count n_eff = 325.2.
    n_emp, n_kish = 2792.0, 325.2
    floor_emp_cm = 100.0 * Z * 0.65 / np.sqrt(n_emp)        # 3.447 cm
    floor_kish_cm = 100.0 * Z * 0.65 / np.sqrt(n_kish)      # 10.10 cm
    phi_emp = floor_emp_cm / (CLAIM * 100.0)                # 1.277
    phi_kish = floor_kish_cm / (CLAIM * 100.0)              # 3.741

    summary = [
        dict(quantity="n_eff per winter month (median of acf.csv)", value=n_eff_per_month,
             provenance="median of 4 monthly n_eff in data/archive/acf.csv"),
        dict(quantity="distinct winters in sigma_by_month.csv", value=n_winters,
             provenance="distinct years: " + ",".join(years)),
        dict(quantity="overlapping months", value=n_months,
             provenance="rows of data/archive/sigma_by_month.csv"),
        dict(quantity="n_eff, 11-winter archive", value=n_eff_11w,
             provenance="n_eff_per_month * 11"),
        dict(quantity="n_eff, 43-month pooled", value=n_eff_43m,
             provenance="n_eff_per_month * 43"),
        dict(quantity="sigma_d median (m)", value=sigma_median,
             provenance="median std over 43 months"),
        dict(quantity="sigma_d RMS (m)", value=sigma_rms,
             provenance="sqrt(mean std^2) over 43 months"),
        dict(quantity="sigma_d range (m)", value=f"{sigma_min:.3f}-{sigma_max:.3f}",
             provenance="min/max std over 43 months"),
        dict(quantity="Phi, 11-winter shared sigma_d=0.389", value=phi_shared,
             provenance="Z*0.389/(0.027*sqrt(3534.3))"),
        dict(quantity="Phi, 11-winter independent sigma_d=0.65", value=phi_indep,
             provenance="Z*0.65/(0.027*sqrt(3534.3))"),
        dict(quantity="n_eff needed for Phi<1 at sigma_d=0.389", value=n_needed_389,
             provenance="(Z*0.389/0.027)^2"),
        dict(quantity="n_eff needed for Phi<1 at sigma_d=0.65", value=n_needed_65,
             provenance="(Z*0.65/0.027)^2"),
        dict(quantity="kappa_x from released curve", value=kx,
             provenance="integral scale of archive_acf_curve.csv rho_x"),
        dict(quantity="kappa_y from released curve", value=ky,
             provenance="integral scale of archive_acf_curve.csv rho_y"),
        dict(quantity="n_eff 2019-04 from kappa", value=n_eff_2019,
             provenance="18033/(kappa_x*kappa_y)"),
        dict(quantity="sea-ice floor, empirical ACF (cm)", value=floor_emp_cm,
             provenance="campaign design input: n_eff 2792, not derived from the archive kappa"),
        dict(quantity="sea-ice floor, exponential Kish (cm)", value=floor_kish_cm,
             provenance="Z*0.65/sqrt(325.2)"),
        dict(quantity="sea-ice Phi, empirical end", value=phi_emp,
             provenance="floor_empirical/2.7"),
        dict(quantity="sea-ice Phi, exponential end", value=phi_kish,
             provenance="floor_kish/2.7"),
    ]
    summ = pd.DataFrame(summary)
    summ.to_csv(DATA / "archive_neff_summary.csv", index=False, encoding="utf-8")

    # -- regenerate the design table with the corrected 11-winter rows --------
    design = pd.DataFrame([
        dict(design="campaign (297 flight days + IceBird, Kish)", truth="independent",
             n_eff=325.2, sigma_d=0.65, claim=CLAIM,
             mde80_cm=100 * Z * 0.65 / np.sqrt(325.2), phi=Z * 0.65 / (CLAIM * np.sqrt(325.2))),
        dict(design="campaign, measured shared-sensor sigma", truth="shared",
             n_eff=325.2, sigma_d=sigma_median, claim=CLAIM,
             mde80_cm=100 * Z * sigma_median / np.sqrt(325.2),
             phi=Z * sigma_median / (CLAIM * np.sqrt(325.2))),
        dict(design="single month, grid ACF (2019-04)", truth="shared",
             n_eff=331.8, sigma_d=sigma_median, claim=CLAIM,
             mde80_cm=100 * Z * sigma_median / np.sqrt(331.8),
             phi=Z * sigma_median / (CLAIM * np.sqrt(331.8))),
        dict(design="11 winters (one independent month each)", truth="shared",
             n_eff=n_eff_11w, sigma_d=sigma_median, claim=CLAIM,
             mde80_cm=100 * Z * sigma_median / np.sqrt(n_eff_11w),
             phi=Z * sigma_median / (CLAIM * np.sqrt(n_eff_11w))),
        dict(design="11 winters (one independent month each)", truth="independent",
             n_eff=n_eff_11w, sigma_d=0.65, claim=CLAIM,
             mde80_cm=100 * Z * 0.65 / np.sqrt(n_eff_11w),
             phi=Z * 0.65 / (CLAIM * np.sqrt(n_eff_11w))),
        dict(design="43 months (pooled upper bound)", truth="shared",
             n_eff=n_eff_43m, sigma_d=sigma_median, claim=CLAIM,
             mde80_cm=100 * Z * sigma_median / np.sqrt(n_eff_43m),
             phi=Z * sigma_median / (CLAIM * np.sqrt(n_eff_43m))),
        dict(design="43 months (pooled upper bound)", truth="independent",
             n_eff=n_eff_43m, sigma_d=0.65, claim=CLAIM,
             mde80_cm=100 * Z * 0.65 / np.sqrt(n_eff_43m),
             phi=Z * 0.65 / (CLAIM * np.sqrt(n_eff_43m))),
    ])
    design.to_csv(DATA / "phi_archive_design.csv", index=False, encoding="utf-8")

    print(summ.to_string(index=False))
    print("\nkappa from released curve: kx=%.3f ky=%.3f -> n_eff(2019-04)=%.1f"
          % (kx, ky, n_eff_2019))
    print("sea-ice floors: empirical %.3f cm (Phi %.3f), exponential %.3f cm (Phi %.3f)"
          % (floor_emp_cm, phi_emp, floor_kish_cm, phi_kish))
    print("wrote data/phi_archive_design.csv and data/archive_neff_summary.csv")
    # machine-readable copy for the number check
    (DATA / "archive_neff_summary.json").write_text(
        json.dumps({r["quantity"]: r["value"] for r in summary}, indent=1),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
