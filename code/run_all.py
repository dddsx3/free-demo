"""P4 / Phi criterion -- one-command reproduction of every number and figure.

Stages (in order):
    1. phi_core.py    arithmetic -> data/*.csv               (no network)
    2. make_figures.py figures  -> figures/fig1..fig7        (no network)
    3. pdflatex chain  manuscript.tex + supplement.tex -> both PDFs (local TeX only)
    4. verify_refs.py  every DOI vs Crossref / DataCite      (optional: --refs)

Usage:
    python code/run_all.py                 # stages 1-3 (offline, reproducible)
    python code/run_all.py --refs          # also re-resolve the whole reference list
    python code/run_all.py --no-tex        # numbers and figures only
    python code/run_all.py --refs-only     # reference audit only

Exit status is non-zero if any stage fails or if a headline number moves away
from the value quoted in the manuscript.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "code"
DATA = ROOT / "data"
FIG = ROOT / "figures"

# Headline numbers in the manuscript (Tables 3 and 4, Figs. 2 and 5).
EXPECTED = {
    "SIT": 3.7406,
    "SM": 0.23798,
    "SSS": 0.019490,
    "PR": 0.043409,
    "AGB": 2.70885,
}
EXPECTED_INTERVAL = (1.2767, 3.7406)
EXPECTED_FLOORS_CM = (3.447, 10.098)   # the archive sub-family used for the interval
EXPECTED_FLOOR_ALT = 10.38             # the 27-per-campaign variant quoted in the text
TOL = 1e-3


def run(script: str, timeout: int = 900, extra: list | None = None) -> None:
    """Run a sibling script with the current interpreter and stream its output."""
    print(f"\n== {script} ==", flush=True)
    proc = subprocess.run(
        [sys.executable, str(CODE / script)] + list(extra or []),
        cwd=str(ROOT),
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise SystemExit(f"FAILED: {script} exited with {proc.returncode}")


def check_numbers() -> None:
    """Re-read the derived tables and assert the values printed in the paper."""
    import pandas as pd

    master = pd.read_csv(DATA / "phi_master.csv").set_index("id")
    bad = []
    for key, want in EXPECTED.items():
        got = float(master.loc[key, "phi"])
        if abs(got - want) > TOL * max(1.0, want):
            bad.append(f"{key}: table={got:.6f} expected={want:.4f}")

    bounds = pd.read_csv(DATA / "phi_kernel_bounds.csv")
    full = sorted(bounds["floor_cm"].tolist())
    if abs(full[0] - 3.406) > 1e-6 or abs(full[-1] - EXPECTED_FLOOR_ALT) > 1e-6:
        bad.append(f"kernel floor family: {full}, expected 3.406 ... {EXPECTED_FLOOR_ALT}")

    # The reported interval is the archive sub-family (Table 2, rows 1, 4 and 5).
    lo = bounds[(bounds["kernel"] == "empirical difference-field ACF")
                & (bounds["design"] == "archive, 8 per campaign")]
    hi = bounds[(bounds["kernel"] == "exponential, L=326 km")
                & (bounds["design"] == "archive, Kish equal weight")]
    if abs(float(lo["floor_cm"].iloc[0]) - EXPECTED_FLOORS_CM[0]) > 1e-6:
        bad.append(f"ACF floor: {float(lo['floor_cm'].iloc[0])}")
    if abs(float(hi["floor_cm"].iloc[0]) - EXPECTED_FLOORS_CM[1]) > 1e-6:
        bad.append(f"exponential floor: {float(hi['floor_cm'].iloc[0])}")
    if abs(float(lo["phi"].iloc[0]) - EXPECTED_INTERVAL[0]) > 0.01:
        bad.append(f"sea-ice low Phi: {float(lo['phi'].iloc[0]):.4f}")
    if abs(float(hi["phi"].iloc[0]) - EXPECTED_INTERVAL[1]) > 0.01:
        bad.append(f"sea-ice high Phi: {float(hi['phi'].iloc[0]):.4f}")

    # Archive rows of Table 1 / Sect. 5: measured sigma_d and n_eff, and the
    # two eleven-winter verdicts that straddle Phi = 1 (the record holds 11
    # winters, not the 14 assumed by an earlier version).
    archive = pd.read_csv(DATA / "phi_archive_design.csv")
    want = {"single month, grid ACF (2019-04)": (331.8, 2.217),
            "11 winters (one independent month each)": (3534.3, 0.679),
            "43 months (pooled upper bound)": (13815.9, 0.344)}
    for name, (n_want, phi_want) in want.items():
        row = archive[archive["design"] == name]
        if row.empty:
            bad.append(f"archive row missing: {name}")
            continue
        if abs(float(row["n_eff"].iloc[0]) - n_want) > 0.05:
            bad.append(f"{name}: n_eff={float(row['n_eff'].iloc[0]):.1f}")
        if abs(float(row["phi"].iloc[0]) - phi_want) > 5e-3:
            bad.append(f"{name}: Phi={float(row['phi'].iloc[0]):.4f}")
    indep = archive[(archive["design"] == "11 winters (one independent month each)")
                    & (archive["truth"] == "independent")]
    if indep.empty or abs(float(indep["phi"].iloc[0]) - 1.135) > 5e-3:
        bad.append("11-winter independent Phi is not 1.135")

    if bad:
        print("\nNumber check FAILED:")
        for line in bad:
            print("  " + line)
        raise SystemExit(1)
    print("\nNumber check OK: five Phi values, the 3.447/10.38 cm floors, the "
          "1.28-3.74 sea-ice interval and the archive rows of Table 1 all match "
          "the manuscript.")


def check_manuscript() -> None:
    """Read the manuscript (and supplement) and flag text/number drift.

    The regression tests below catch a number moving in *code* but were blind to
    the same number drifting in the *prose*.  This guard reads the TeX sources
    and (a) asserts that the corrected values are present and (b) asserts that
    the stale values they replaced are absent, so a future edit cannot silently
    re-introduce the earlier slips.
    """
    import re
    tex = (ROOT / "manuscript.tex").read_text(encoding="utf-8", errors="ignore")
    sup = (ROOT / "supplement.tex").read_text(encoding="utf-8", errors="ignore")
    both = tex + "\n" + sup
    problems = []

    # (stale pattern, where it is still allowed because it is part of the
    # correction note, corrected pattern that must be present)
    required = [
        (r"3(\\?,?)?534", "11-winter n_eff 3,534 must appear in the manuscript"),
        (r"4(\\?,?)?550", "n_eff needed 4,550 must appear in the manuscript"),
        (r"hundredfold", "Phi=10 needs a hundredfold (not tenfold) increase"),
        (r"1, 5 and 20", "Fig. 1 caption isolines must read 1, 5 and 20"),
        (r"0\.408", "RMS sigma_d must be 0.408 m"),
    ]
    for pat, msg in required:
        if not re.search(pat, both):
            problems.append("missing: " + msg)

    # Stale tokens that must NOT appear as live claims any more.  The 0.269 /
    # 0.080 values and the "fourteen-winter design does not exist" sentence are
    # allowed because they are part of the correction note; a live claim of the
    # old 14-winter archive (n_eff 4,498; Phi 0.60 / 1.006) is forbidden.
    forbidden_exact = [
        ("14 winters (one independent", "archive_design label is now 11 winters"),
        ("4\\,498", "stale 14-winter n_eff 4,498 must be gone"),
        ("4,498", "stale 14-winter n_eff 4,498 must be gone"),
        ("1.006", "stale 14-winter independent Phi 1.006 must be gone"),
        (r"0\.60\b", "stale 14-winter shared Phi 0.60 must be gone"),
    ]
    for tok, msg in forbidden_exact:
        if tok in both:
            problems.append("forbidden live token: " + msg)

    # The Fig. 1 caption / ACF slips: forbid the old literal combinations as
    # live statements (they may appear quoted inside the correction note).
    if re.search(r"isolines of .*?20, 200 and 600", tex):
        problems.append("Fig. 1 caption still says 20, 200 and 600")
    if re.search(r"root-mean-square 0\.461", both):
        problems.append("RMS sigma_d still printed as 0.461 m")
    if re.search(r"tenfold increase in independent", tex):
        problems.append("still says tenfold increase in independent information")
    if re.search(r"\b4,549\b", both):
        problems.append("stale 4,549 (should be 4,550) still present")

    if problems:
        print("\nManuscript literal check FAILED:")
        for p in problems:
            print("  " + p)
        raise SystemExit(1)
    print("Manuscript literal check OK: corrected values present, stale ones gone.")


def compile_tex() -> None:
    """pdflatex -> bibtex -> pdflatex x2 for both documents, then report."""
    latex = shutil.which("pdflatex")
    if latex is None:
        print("pdflatex not found on PATH; skipping the PDF stage.", flush=True)
        return
    print("\n== pdflatex chain ==", flush=True)
    for doc in ("manuscript", "supplement"):
        print(f"-- {doc}.tex", flush=True)
        steps = [
            ["pdflatex", "-interaction=nonstopmode", f"{doc}.tex"],
            ["bibtex", doc],
            ["pdflatex", "-interaction=nonstopmode", f"{doc}.tex"],
            ["pdflatex", "-interaction=nonstopmode", f"{doc}.tex"],
        ]
        for step in steps:
            exe = shutil.which(step[0])
            if exe is None:
                print(f"{step[0]} not found; skipping the remaining TeX steps.")
                return
            subprocess.run([exe] + step[1:], cwd=str(ROOT), stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=900)

        log = (ROOT / f"{doc}.log").read_text(encoding="utf-8", errors="ignore")
        overfull = log.count("Overfull \\hbox")
        undefined = log.count("LaTeX Warning: There were undefined references")
        if "Output written" not in log:
            raise SystemExit(f"FAILED: no PDF was written for {doc}")
        line = [l for l in log.splitlines() if "Output written" in l][-1]
        print("  " + line.strip())
        print(f"  overfull hboxes: {overfull}   undefined-reference warnings: {undefined}")
        if undefined:
            raise SystemExit(f"FAILED: unresolved references in {doc}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def fingerprint() -> None:
    """Print hashes of the artefacts so a reader can confirm byte-identity."""
    print("\n== fingerprints (sha256) ==")
    for pattern, folder in (("*.csv", DATA), ("*.pdf", FIG)):
        for p in sorted(folder.glob(pattern)):
            print(f"{sha256(p)[:16]}  {p.relative_to(ROOT)}")
    for name in ("manuscript.pdf", "supplement.pdf"):
        p = ROOT / name
        if p.exists():
            print(f"{sha256(p)[:16]}  {name}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Reproduce the P4/Phi paper end to end.")
    ap.add_argument("--refs", action="store_true",
                    help="also re-resolve every DOI against Crossref/DataCite (network)")
    ap.add_argument("--refs-only", action="store_true", help="reference audit only")
    ap.add_argument("--no-tex", action="store_true", help="skip the LaTeX stage")
    ap.add_argument("--archive", action="store_true",
                    help="also run the worked example on a real product pair "
                         "(needs --p1 or P1_OUT; the P1 products are not in this archive)")
    ap.add_argument("--p1", default=None,
                    help="directory of the P1 products for --archive")
    args = ap.parse_args()

    if args.refs_only:
        run("verify_refs.py")
        return

    run("phi_core.py")
    check_numbers()
    run("archive_recompute.py")
    check_manuscript()
    run("make_figures.py")

    if args.archive:
        extra = ["--p1", args.p1] if args.p1 else []
        run("archive_example.py", timeout=1800, extra=extra)

    if args.refs:
        run("verify_refs.py")

    if not args.no_tex:
        compile_tex()

    fingerprint()
    print("\nAll stages completed.")


if __name__ == "__main__":
    main()
