"""Regression tests for the Phi criterion (P4 / GMD submission).

Run from the paper root:

    python -m pytest code/test_phi_core.py -q

Every test is offline and writes only inside data/. The first test re-runs
phi_core.py, so a change in the arithmetic is caught here before it reaches
the manuscript.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

CODE = Path(__file__).resolve().parent
ROOT = CODE.parent
sys.path.insert(0, str(CODE))

import archive_example as ax  # noqa: E402

# Values printed in the manuscript (Tables 3 and 4, Fig. 2).
EXPECTED_PHI = {
    "SIT": 3.7406,
    "SM": 0.23798,
    "SSS": 0.019490,
    "PR": 0.043409,
    "AGB": 2.70885,
}


def test_headline_phi_values_match_manuscript():
    """phi_core.py must reproduce the five published Phi values."""
    proc = subprocess.run([sys.executable, str(CODE / "phi_core.py")],
                          cwd=str(ROOT), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr

    master = pd.read_csv(ROOT / "data" / "phi_master.csv").set_index("id")
    for key, want in EXPECTED_PHI.items():
        got = float(master.loc[key, "phi"])
        assert abs(got - want) < 1e-3 * max(1.0, want), f"{key}: {got} vs {want}"


def test_mde_is_phi_times_claim():
    """MDE80 = Phi * claim is an identity, not an approximation."""
    master = pd.read_csv(ROOT / "data" / "phi_master.csv")
    assert np.allclose(master["mde80"], master["phi"] * master["claim"], rtol=1e-12)


def test_transect_closure_gives_325_2():
    """297 flight days + 28.2 IceBird, one segment per sortie at L = 326 km."""
    l_sortie, l_corr = 450.0, 326.0
    n_seg = max(1.0, l_sortie / (2.0 * l_corr))
    assert n_seg == 1.0
    assert abs((297 + 28.2) * n_seg - 325.2) < 1e-9


def test_kish_closure_gives_138_6():
    """Soil moisture: n = 2842, m = 40, rho = 0.5."""
    n = 2842 / (1 + (40 - 1) * 0.5)
    assert abs(n - 138.6341463414634) < 1e-9


def test_area_time_closure_gives_20668():
    """Salinity: A/(2 pi L^2) * (T/tau)."""
    n = (3.6e8 / (2 * np.pi * 333.0 ** 2)) * (120.0 / 3.0)
    assert abs(n - 20667.795548) < 1e-4


def test_integral_scale_sums_positive_lags_only():
    """kappa = 1 + 2 * sum of positive lags; stop at the first non-positive one."""
    assert abs(ax.integral_scale([1.0, 0.5, 0.2])[0] - 2.4) < 1e-12
    assert abs(ax.integral_scale([1.0, 0.5, 0.0, 0.4])[0] - 2.0) < 1e-12
    assert abs(ax.integral_scale([1.0, -0.5])[0] - 1.0) < 1e-12


def test_phi_decreases_with_effective_sample_size():
    """More independent units can only lower the floor."""
    phi = [ax.phi_rows(0.027, [("d", n, 0.389)])[0]["phi"] for n in (100, 1000, 10000)]
    assert phi[0] > phi[1] > phi[2]


def test_archive_example_rejects_missing_real_inputs(tmp_path, monkeypatch):
    """With a --p1 directory that lacks the npz files it must fail loudly."""
    monkeypatch.delenv("P1_OUT", raising=False)
    missing = tmp_path / "empty"
    missing.mkdir()
    monkeypatch.setattr(sys, "argv",
                        ["archive_example.py", "--p1", str(missing),
                         "--out", str(tmp_path / "out")])
    assert ax.main() == 2


def test_archive_example_runs_from_committed_csv(tmp_path, monkeypatch):
    """With no --p1 the worked example recomputes from the shipped CSVs."""
    monkeypatch.delenv("P1_OUT", raising=False)
    monkeypatch.setattr(sys, "argv",
                        ["archive_example.py", "--out", str(tmp_path / "out")])
    assert ax.main() == 0
    import json
    res = json.load(open(tmp_path / "out" / "archive_example.json"))
    # eleven winters -> n_eff ~ 3 534, shared Phi ~ 0.68
    assert abs(res["n_eff_11winters"] - 3534.3) < 1.0
    shared = [t for t in res["phi_table"]
              if t["design"].startswith("11 winters, one month")
              and t["sigma_d"] < 0.5][0]
    assert abs(shared["phi"] - 0.679) < 0.01


def test_archive_example_runs_on_a_synthetic_pair(tmp_path, monkeypatch):
    """A tiny synthetic A/B pair with a known white-noise difference gives kappa ~ 1."""
    import numpy as np

    n_month, ny, nx = 1, 60, 60
    rng = np.random.default_rng(0)
    a = np.ones((n_month, ny, nx), dtype="float32")
    b = a.copy()
    b[0, :, :] += rng.normal(0, 0.3, (ny, nx)).astype("float32")   # white noise only

    p1 = tmp_path / "p1"
    p1.mkdir()
    np.savez(p1 / "p1_cci_monthly.npz", stack=a,
             months=np.array(["2019-04"]), lat=np.zeros((ny, nx)))
    np.savez(p1 / "p1_monthly_cells.npz",
             cellsum=b.astype("float64"), cellnv=np.ones_like(a, dtype="float64"),
             months=np.array(["2019-04"]))

    monkeypatch.setattr(sys, "argv",
                        ["archive_example.py", "--p1", str(p1), "--out", str(tmp_path / "out"),
                         "--acf-months", "2019-04"])
    assert ax.main() == 0
    import json
    res = json.load(open(tmp_path / "out" / "archive_example.json"))
    acf = res["acf"][0]
    # White noise -> no correlation at lag > 0 -> bandwidth factor near 1.
    assert 0.8 < acf["kappa_x"] < 1.4
    assert 0.8 < acf["kappa_y"] < 1.4
    assert abs(res["sigma_d_month_median"] - 0.3) < 0.06
