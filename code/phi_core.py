"""P4 / Phi criterion -- core arithmetic.

Definition (fixed form, not to be altered):
    Phi = 2.802 * sigma_d / (claim * sqrt(n_eff))          (P1)
    MDE80 = 2.802 * sigma_d / sqrt(n_eff)                  (P2)
    n_eff = n^2 / sum_ij rho_ij                            (Kish design effect)
2.802 = z_{0.975} + z_{0.80} = 1.959964 + 0.841621  (two-sided alpha = 0.05, power = 0.80)

Outputs (all under ../data):
    phi_master.csv          -- one row per domain, base case
    phi_kernel_bounds.csv   -- sea-ice kernel x design family (this is where 3.447 / 10.38 cm live)
    phi_sensitivity.csv     -- sigma_d x claim, each perturbed by -50%..+50%
    phi_robustness.csv      -- one-at-a-time and joint-box summaries
    power_curve.csv         -- P(detect) versus true effect (in units of claim) for a grid of Phi
This script performs arithmetic only; it downloads nothing.
"""
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"
DATA.mkdir(parents=True, exist_ok=True)

Z = 1.959964 + 0.841621          # 2.801585
Z_REPORTED = 2.802               # value used in the manuscript formula


def phi(sigma_d, claim, n_eff, z=Z_REPORTED):
    return z * sigma_d / (claim * np.sqrt(n_eff))


def mde(sigma_d, n_eff, z=Z_REPORTED):
    return z * sigma_d / np.sqrt(n_eff)


# ----------------------------------------------------------------------------
# Master table: five domains + two internal variants (kept because they are
# part of the provenance trail and are used in the sensitivity discussion).
# ----------------------------------------------------------------------------
DOMAINS = [
    dict(domain="Sea-ice thickness", id="SIT",
         quantity="Monthly mean thickness over ice-covered area (m)",
         n_raw="40,084 ATM L1B granules (2009-2019); 338 flight days",
         n_eff=325.2,
         rule="sortie capacity: 1 independent segment per flight day at L=326 km; 297 flight days + IceBird 28.2",
         sigma_d=0.65, sigma_note="measured CCI-IceBird/ATM difference, 0.50-0.80 m",
         claim=0.027, claim_note="2% of 1.36 m mean (mask-induced bias)",
         status="assessable"),
    dict(domain="Soil moisture", id="SM",
         quantity="Volumetric water content 0-5 cm, 9 km, m3/m3",
         n_raw="2,842 stations in 71 networks (ISMN, July 2021)",
         n_eff=2842 / (1 + (40 - 1) * 0.5),
         rule="cluster design effect: m=40 stations per network, intra-cluster rho=0.5",
         sigma_d=0.040, sigma_note="SMAP ubRMSE target/observed, 0.040 m3/m3",
         claim=0.040, claim_note="mission accuracy (ubRMSE)",
         status="assessable"),
    dict(domain="Sea surface salinity", id="SSS",
         quantity="Monthly 25 km sea surface salinity (PSU)",
         n_raw="~1.56e6 Argo profiles (10 yr); 13,000 profiles/month",
         n_eff=(3.6e8 / (2 * np.pi * 333.0 ** 2)) * (120.0 / 3.0),
         rule="area x time: A/(2*pi*L^2) * (T/tau), L=333 km, tau=3 months",
         sigma_d=0.20, sigma_note="SMAP-buoy SD: 0.22 weekly, 0.17 monthly",
         claim=0.20, claim_note="mission accuracy (0.2 PSU)",
         status="assessable"),
    dict(domain="Precipitation", id="PR",
         quantity="Daily accumulation, area mean (mm/day)",
         n_raw="50,000 gauges (China AWS); GPCC 78,000 total / 51,000 monthly",
         n_eff=(9.6e6 / (2 * np.pi * 100.0 ** 2)) * (1095.0 / 3.0),
         rule="area x time: A/(2*pi*L^2) * (T/tau), L=100 km, tau=3 days",
         sigma_d=3.0, sigma_note="daily IMERG-gauge difference SD, order 3 mm/day",
         claim=0.82, claim_note="20% of 4.1 mm/day mean",
         status="assessable"),
    dict(domain="Forest biomass", id="AGB",
         quantity="Aboveground biomass density, regional (Mg/ha)",
         n_raw="39 plots in one region; GEDI L4A 74,860 granules",
         n_eff=39 / (1 + (39 - 1) * 0.4),
         rule="cluster design effect: m=39 plots, intra-region rho=0.4",
         sigma_d=45.0, sigma_note="literature RMSE 39-94 Mg/ha (median 45)",
         claim=30.0, claim_note="20% of 150 Mg/ha mean",
         status="assessable"),
]

master = []
for d in DOMAINS:
    ph = phi(d["sigma_d"], d["claim"], d["n_eff"])
    master.append(dict(
        domain=d["domain"], id=d["id"], quantity=d["quantity"],
        n_raw=d["n_raw"], n_eff=d["n_eff"], rule=d["rule"],
        sigma_d=d["sigma_d"], sigma_note=d["sigma_note"],
        claim=d["claim"], claim_note=d["claim_note"],
        mde80=mde(d["sigma_d"], d["n_eff"]),
        phi=ph, log10_phi=np.log10(ph),
        verdict=("not verifiable (Phi > 1)" if ph > 1 else "verifiable (Phi < 1)"),
        status=d["status"]))
master = pd.DataFrame(master)
master.to_csv(DATA / "phi_master.csv", index=False, encoding="utf-8")

# ----------------------------------------------------------------------------
# Internal variants that belong to the same provenance trail
# ----------------------------------------------------------------------------
variants = pd.DataFrame([
    dict(id="SIT_ACF", label="SIT, empirical difference-field ACF, archive m=8",
         sigma_d=0.65, claim=0.027, n_eff=np.nan, floor_m=0.03447),
    dict(id="SIT_EXP", label="SIT, exponential kernel L=326 km, archive m=8",
         sigma_d=0.65, claim=0.027, n_eff=np.nan, floor_m=0.1038),
    dict(id="SIT_KISH", label="SIT, exponential kernel, Kish archive (n_eff=325.2)",
         sigma_d=0.65, claim=0.027, n_eff=325.2, floor_m=np.nan),
    dict(id="SM_CVS", label="Soil moisture, 18 core validation sites (strict)",
         sigma_d=0.040, claim=0.040, n_eff=18.0, floor_m=np.nan),
    dict(id="SSS_M", label="Sea surface salinity, single-month (conservative)",
         sigma_d=0.20, claim=0.20, n_eff=(3.6e8 / (2 * np.pi * 333.0 ** 2)) * (1.0 / 1.0),
         floor_m=np.nan),
])
variants["floor"] = np.where(variants.floor_m.notna(), variants.floor_m,
                             Z_REPORTED * variants.sigma_d / np.sqrt(variants.n_eff))
variants["phi"] = variants.floor / variants.claim
variants.to_csv(DATA / "phi_variants.csv", index=False, encoding="utf-8")

# ----------------------------------------------------------------------------
# Kernel x design family for sea ice.  Values on the "archive, 8 sorties/campaign"
# row are the published n9 numbers (3.447 cm and 10.38 cm); the other rows are
# the Kish archive bound and the fully optimised bound.
# ----------------------------------------------------------------------------
kernel_bounds = pd.DataFrame([
    dict(kernel="empirical difference-field ACF", design="archive, 8 per campaign",
         floor_cm=3.447, source="n9 campaign design, sect. 5"),
    dict(kernel="empirical difference-field ACF", design="optimised allocation",
         floor_cm=3.406, source="n9 campaign design, sect. 0"),
    dict(kernel="exponential, L=326 km", design="optimised allocation",
         floor_cm=8.40, source="n9 campaign design, sect. 0"),
    dict(kernel="exponential, L=326 km", design="archive, Kish equal weight",
         floor_cm=10.098, source="n8 capacity table (n_eff=325.2)"),
    dict(kernel="exponential, L=326 km", design="archive, 27 per campaign",
         floor_cm=10.38, source="n9 campaign design, sect. 5"),
])
kernel_bounds["claim_cm"] = 2.7
kernel_bounds["phi"] = kernel_bounds.floor_cm / kernel_bounds.claim_cm
kernel_bounds.to_csv(DATA / "phi_kernel_bounds.csv", index=False, encoding="utf-8")

# ----------------------------------------------------------------------------
# Sensitivity: sigma_d and claim each perturbed by -50%..+50%
# ----------------------------------------------------------------------------
FACTORS = [0.5, 0.75, 1.0, 1.25, 1.5]
rows = []
for _, r in master.iterrows():
    for fs in FACTORS:
        for fc in FACTORS:
            rows.append(dict(id=r.id, domain=r.domain,
                             sigma_factor=fs, claim_factor=fc,
                             sigma_d=r.sigma_d * fs, claim=r.claim * fc,
                             phi=r.phi * fs / fc,
                             log10_phi=np.log10(r.phi * fs / fc)))
sens = pd.DataFrame(rows)
sens.to_csv(DATA / "phi_sensitivity.csv", index=False, encoding="utf-8")

rob = []
for _, r in master.iterrows():
    axis_lo = r.phi * 0.5 / 1.0     # sigma_d -50%, claim unchanged
    axis_hi = r.phi * 1.5 / 1.0     # sigma_d +50%, claim unchanged
    axis_lo_c = r.phi * 1.0 / 1.5   # claim +50%, sigma_d unchanged
    axis_hi_c = r.phi * 1.0 / 0.5   # claim -50%
    joint_lo = r.phi * 0.5 / 1.5
    joint_hi = r.phi * 1.5 / 0.5
    lo = min(axis_lo, axis_lo_c, joint_lo)
    hi = max(axis_hi, axis_hi_c, joint_hi)
    if lo > 1:
        verd = "robustly not verifiable"
    elif hi < 1:
        verd = "robustly verifiable"
    else:
        verd = "verdict can flip inside the +-50% box"
    rob.append(dict(id=r.id, domain=r.domain, phi_base=r.phi,
                    phi_axis_min=min(axis_lo, axis_lo_c),
                    phi_axis_max=max(axis_hi, axis_hi_c),
                    phi_joint_min=joint_lo, phi_joint_max=joint_hi,
                    verdict=verd))
rob = pd.DataFrame(rob)
rob.to_csv(DATA / "phi_robustness.csv", index=False, encoding="utf-8")

# same box applied to the two sea-ice kernel bounds
rows = []
for tag, base in (("SIT_ACF_bound", 3.447 / 2.7), ("SIT_EXP_bound", 10.098 / 2.7)):
    rows.append(dict(id=tag, phi_base=base,
                     joint_min=base * 0.5 / 1.5, joint_max=base * 1.5 / 0.5,
                     axis_min=min(base * 0.5, base / 1.5),
                     axis_max=max(base * 1.5, base / 0.5)))
pd.DataFrame(rows).to_csv(DATA / "phi_sensitivity_kernel.csv", index=False, encoding="utf-8")

# ----------------------------------------------------------------------------
# n_eff sensitivity: S2.2 names n_eff the largest source of uncertainty, so the
# grid must perturb it, not only sigma_d and the claim.  Scale each domain's
# n_eff by 0.5 / 0.75 / 1.0 / 1.25 / 1.5 and recompute Phi (sigma_d, claim held
# at their base values).  Phi is proportional to n_eff**-0.5, so the factor is
# 1/sqrt(scale).
# ----------------------------------------------------------------------------
NEF_FACTORS = [0.5, 0.75, 1.0, 1.25, 1.5]
neff_rows = []
for _, r in master.iterrows():
    for f in NEF_FACTORS:
        ne = r.n_eff * f
        ph = Z_REPORTED * r.sigma_d / (r.claim * np.sqrt(ne))
        neff_rows.append(dict(id=r.id, domain=r.domain, n_eff_factor=f,
                              n_eff=ne, phi=ph, log10_phi=np.log10(ph)))
neff_sens = pd.DataFrame(neff_rows)
neff_sens.to_csv(DATA / "phi_sensitivity_neff.csv", index=False, encoding="utf-8")
print("n_eff sensitivity written: factors", NEF_FACTORS)

# ----------------------------------------------------------------------------
# Power curve: P(detect) as a function of true effect measured in units of claim.
# Under the normal approximation the non-centrality is delta/(sigma_d/sqrt(n_eff))
# = 2.802 * k / Phi, with k = delta/claim.
# ----------------------------------------------------------------------------
from scipy.stats import norm
Phi_norm = norm.cdf
k = np.linspace(0, 8, 321)
curves = []
for ph in [0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0]:
    ncp = Z_REPORTED * k / ph
    pw = Phi_norm(ncp - 1.959964) + Phi_norm(-ncp - 1.959964)
    for kk, pp in zip(k, pw):
        curves.append(dict(phi=ph, k=kk, power=pp))
pd.DataFrame(curves).to_csv(DATA / "power_curve.csv", index=False, encoding="utf-8")

# sanity checks printed for the build log
print(master[["id", "n_eff", "sigma_d", "claim", "mde80", "phi", "verdict"]].to_string(index=False))
print()
print(kernel_bounds[["kernel", "design", "floor_cm", "phi"]].to_string(index=False))
print()
print(rob[["id", "phi_base", "phi_axis_min", "phi_axis_max",
           "phi_joint_min", "phi_joint_max", "verdict"]].to_string(index=False))
print()
print("Phi reported: " + ", ".join(f"{r.id}={r.phi:.3f}" for r in master.itertuples()))
print("sea-ice interval: %.3f - %.3f" % (3.447 / 2.7, 10.098 / 2.7))
print("kernel ratio (fixed design): %.3f ; at respective optima: %.3f"
      % (10.38 / 3.447, 8.40 / 3.406))
