"""Worked example: measure sigma_d and n_eff from a real product pair.

This is the "example implementation" of Sect. 5 extended to the one step the
paper deliberately leaves to the assessor: estimating the correlation function
of the difference field. It is a worked example, not a library. It reads two
monthly thickness fields, forms the cell-level difference d = A - B on cells
where both are valid, and reports

    sigma_d   the standard deviation of d, per month and pooled;
    rho(k)    the empirical autocorrelation of d along each grid axis;
    kappa     1 + 2 * sum_k rho(k), summed to the first non-positive lag;
    n_eff     n_valid / (kappa_x * kappa_y);
    Phi       z * sigma_d / (claim * sqrt(n_eff)), z = 2.802.

Inputs are the P1 missingness products, which are NOT part of the paper
archive because they are derived from the ESA CCI and CS2SMOS distributions.
Pass their directory explicitly:

    python code/archive_example.py --p1 /path/to/p1_missingness/out

or set the environment variable P1_OUT. Outputs go to data/archive/ unless
--out is given. Nothing is downloaded.

Expected values on the 2011-2024 winter archive used in the paper:
    sigma_d (month median) 0.389 m;  n_eff (2019-04) 331.8;  kappa_x 7.69;
    kappa_y 7.07.  A different product pair will give different numbers; the
    arithmetic below is what carries over.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

Z = 2.802                      # z_{0.975} + z_{0.80}, same constant as phi_core.py
CELL_KM = 25.0
DATA = Path(__file__).resolve().parents[1] / "data" / "archive"


def norm_month(m) -> str:
    """'201904' | '2019-4' | '2019-04' -> '2019-04'."""
    m = str(m).strip()
    if "-" in m:
        y, mm = m.split("-")[:2]
    else:
        y, mm = m[:4], m[4:6]
    return "%s-%02d" % (y, int(mm))


def load_fields(p1_dir: Path) -> dict:
    """Read the two monthly fields and put them on a common month label."""
    zc = np.load(p1_dir / "p1_cci_monthly.npz", allow_pickle=True)
    cci = zc["stack"].astype("float32")
    cci_months = [norm_month(m) for m in zc["months"]]

    zs = np.load(p1_dir / "p1_monthly_cells.npz", allow_pickle=True)
    cell_sum = zs["cellsum"].astype("float64")
    n_valid = zs["cellnv"].astype("float64")
    cs_months = [norm_month(m) for m in zs["months"]]
    with np.errstate(invalid="ignore", divide="ignore"):
        cs_mean = np.where(n_valid > 0, cell_sum / n_valid, np.nan).astype("float32")

    return dict(a=cci, a_months=cci_months, b=cs_mean, b_months=cs_months)


def difference(d: dict, month: str, valid_min: float = 0.05):
    """d = A - B on cells where both are finite and above a positive floor."""
    i = d["a_months"].index(month)
    j = d["b_months"].index(month)
    a, b = d["a"][i], d["b"][j]
    ok = np.isfinite(a) & np.isfinite(b) & (a > valid_min) & (b > valid_min)
    return np.where(ok, a - b, np.nan), ok


def monthly_sigma(d: dict) -> pd.DataFrame:
    rows = []
    for month in d["a_months"]:
        if month not in d["b_months"]:
            continue
        diff, ok = difference(d, month)
        n = int(ok.sum())
        if n < 100:
            rows.append(dict(month=month, n=n, note="too few common cells"))
            continue
        v = diff[ok]
        rows.append(dict(month=month, n=n, mean=float(np.mean(v)),
                         std=float(np.std(v, ddof=1)),
                         median=float(np.median(v)),
                         p10=float(np.percentile(v, 10)),
                         p90=float(np.percentile(v, 90))))
    return pd.DataFrame(rows)


def acf_1d(field: np.ndarray, mask: np.ndarray, axis: int, max_lag: int = 30) -> list:
    """Empirical autocorrelation along one axis, using only pairs valid on both ends."""
    rhos = []
    for lag in range(0, max_lag + 1):
        if axis == 1:
            a, ma = field[:, :-lag or None], mask[:, :-lag or None]
            b, mb = field[:, lag:], mask[:, lag:]
        else:
            a, ma = field[:-lag or None, :], mask[:-lag or None, :]
            b, mb = field[lag:, :], mask[lag:, :]
        ok = ma & mb
        if ok.sum() < 200:
            break
        av = a[ok] - a[ok].mean()
        bv = b[ok] - b[ok].mean()
        den = np.sqrt(np.sum(av * av) * np.sum(bv * bv))
        rhos.append(float(np.sum(av * bv) / den) if den > 0 else np.nan)
    return rhos


def integral_scale(rhos: list) -> tuple:
    """kappa = 1 + 2 * sum_{k>=1} rho(k), stopped at the first non-positive rho."""
    total = 0.0
    for k, r in enumerate(rhos[1:], start=1):
        if not np.isfinite(r) or r <= 0:
            return 1.0 + 2.0 * total, k
        total += r
    return 1.0 + 2.0 * total, len(rhos)


def acf_report(d: dict, months: list) -> pd.DataFrame:
    rows = []
    for month in months:
        if month not in d["b_months"]:
            continue
        diff, ok = difference(d, month)
        field = np.where(ok, diff, 0.0)          # zeros so that pairing stays valid
        kx, lag_x = integral_scale(acf_1d(field, ok, axis=1))
        ky, lag_y = integral_scale(acf_1d(field, ok, axis=0))
        n = int(ok.sum())
        rows.append(dict(month=month, n=n, kappa_x=kx, kappa_y=ky,
                         lag0_x=lag_x, lag0_y=lag_y,
                         bandwidth_x_km=kx * CELL_KM, bandwidth_y_km=ky * CELL_KM,
                         n_eff=n / (kx * ky),
                         sigma_d=float(np.std(diff[ok], ddof=1))))
    return pd.DataFrame(rows)


def phi_rows(claim: float, designs: list) -> list:
    """Phi and the 80 % floor for a list of (label, n_eff, sigma_d) designs."""
    out = []
    for label, n_eff, sigma_d in designs:
        out.append(dict(design=label, n_eff=float(n_eff), sigma_d=float(sigma_d), claim=claim,
                        mde80=float(Z * sigma_d / np.sqrt(n_eff)),
                        phi=float(Z * sigma_d / (claim * np.sqrt(n_eff)))))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--p1", default=os.environ.get("P1_OUT"),
                    help="directory holding p1_cci_monthly.npz and p1_monthly_cells.npz")
    ap.add_argument("--out", default=str(DATA), help="output directory")
    ap.add_argument("--claim", type=float, default=0.027,
                    help="claimed magnitude in metres (paper: 2.7 cm)")
    ap.add_argument("--acf-months", default="2018-04,2019-04,2020-11,2021-04",
                    help="comma-separated months for the autocorrelation estimate")
    args = ap.parse_args()

    if not args.p1:
        print("error: pass --p1 or set P1_OUT; the P1 products are not in the "
              "paper archive because they derive from the CCI and CS2SMOS "
              "distributions.", file=sys.stderr)
        return 2
    p1_dir = Path(args.p1)
    for name in ("p1_cci_monthly.npz", "p1_monthly_cells.npz"):
        if not (p1_dir / name).exists():
            print(f"error: {p1_dir / name} not found", file=sys.stderr)
            return 2

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    d = load_fields(p1_dir)
    print("[1] month-by-month difference")
    ms = monthly_sigma(d)
    ms.to_csv(out_dir / "sigma_by_month.csv", index=False)
    good = ms[ms["n"] >= 1000]
    sigma_median = float(np.median(good["std"]))
    sigma_rms = float(np.sqrt(np.mean(good["std"] ** 2)))
    print(ms.to_string(index=False))

    print("\n[2] autocorrelation of the difference field")
    ac = acf_report(d, [m.strip() for m in args.acf_months.split(",")])
    ac.to_csv(out_dir / "acf.csv", index=False)
    print(ac.to_string(index=False))

    n_eff_one = float(ac.loc[ac.month == "2019-04", "n_eff"].iloc[0]) if (ac.month == "2019-04").any() else float(ac["n_eff"].iloc[0])
    n_eff_14w = float(np.median(ac["n_eff"]) * 14)     # one independent month per winter
    n_eff_43 = float(np.median(ac["n_eff"]) * len(good))

    print("\n[3] Phi under six designs")
    table = phi_rows(args.claim, [
        ("campaign, Kish design (325.2)", 325.2, sigma_median),
        ("one month, cell-level ACF", n_eff_one, sigma_median),
        ("14 winters, one month each (conservative)", n_eff_14w, sigma_median),
        ("43 months concatenated (optimistic bound)", n_eff_43, sigma_median),
        ("14 winters, independent sigma_d = 0.65", n_eff_14w, 0.65),
        ("43 months, independent sigma_d = 0.65", n_eff_43, 0.65),
    ])
    for row in table:
        print(row)

    result = dict(
        months_with_common_cells=int(len(good)),
        sigma_d_month_median=sigma_median,
        sigma_d_pooled_rms=sigma_rms,
        sigma_d_month_min=float(good["std"].min()),
        sigma_d_month_max=float(good["std"].max()),
        n_common_median=float(np.median(good["n"])),
        n_eff_one_month=n_eff_one,
        n_eff_14winters=n_eff_14w,
        n_eff_43months=n_eff_43,
        acf=ac.to_dict(orient="records"),
        phi_table=table,
        n_eff_needed_for_phi_below_one=float((Z * sigma_median / args.claim) ** 2),
        note=("sigma_d is the cell-level standard deviation of A - B; n_eff follows from "
              "the empirical autocorrelation of the same difference field. The two "
              "thickness products share a radar, so sigma_d here is an optimistic "
              "end, not an independent reference."),
    )
    with open(out_dir / "archive_example.json", "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    print("\nPhi needs n_eff > %.0f for Phi < 1 at this sigma_d and claim."
          % result["n_eff_needed_for_phi_below_one"])
    print("wrote", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
