"""Figures for P4.  All panels are produced from the CSV files written by
phi_core.py, so the figures cannot drift from the numbers quoted in the text.

Out: figures/fig1_power.pdf ... fig5_kernel.pdf  (plus .png previews)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8.5,
    "axes.linewidth": 0.7,
    "axes.labelsize": 9,
    "legend.fontsize": 7.5,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "pdf.fonttype": 42,
    "savefig.bbox": "tight",
})

C_UNVER = "#b0413e"     # not verifiable
C_VER = "#2c5f7c"       # verifiable
C_MID = "#9a8c98"
C_GRID = "#d5d5d5"

master = pd.read_csv(DATA / "phi_master.csv")
kernel = pd.read_csv(DATA / "phi_kernel_bounds.csv")
sens = pd.read_csv(DATA / "phi_sensitivity.csv")
power = pd.read_csv(DATA / "power_curve.csv")

LABEL = {
    "SIT": "Sea-ice thickness",
    "SM": "Soil moisture",
    "SSS": "Sea-surface salinity",
    "PR": "Precipitation",
    "AGB": "Forest biomass",
}


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=300 if ext == "png" else None)
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------------------
# Fig 1: what Phi means.  (a) power versus true effect; (b) Phi versus n_eff
# ---------------------------------------------------------------------------
fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.1, 2.75))

for ph in sorted(power.phi.unique()):
    d = power[power.phi == ph]
    lw = 1.9 if ph in (1.0, 0.25) else 1.0
    col = C_UNVER if ph >= 1 else C_VER
    axa.plot(d.k, d.power, lw=lw, color=col, alpha=0.9 if lw > 1 else 0.55,
             label=f"$\\Phi$ = {ph:g}")
axa.axhline(0.8, ls=":", lw=0.8, color="0.35")
axa.axvline(1.0, ls=":", lw=0.8, color="0.35")
axa.set_xlim(0, 6)
axa.set_ylim(0, 1.02)
axa.set_xlabel("true effect / claimed effect  ($k = \\delta/\\,\\mathrm{claim}$)")
axa.set_ylabel("power to detect")
axa.text(1.03, 0.815, "80 % at $k$ = $\\Phi$", fontsize=7, color="0.3")
axa.legend(frameon=False, ncol=1, loc="lower right", handlelength=1.2)
axa.set_title("(a) the criterion is a power statement", loc="left", fontsize=8.5)

n = np.logspace(0, 6, 400)
lo, hi = 3.447 / 2.7, 10.098 / 2.7
for ratio in (1, 5, 20):
    axb.plot(np.sqrt(n), 2.802 * ratio / np.sqrt(n), lw=0.9, color="0.45")
    xc = 2.802 * ratio          # where the isoline crosses Phi = 1
    axb.annotate(f"$\\sigma_d$/claim = {ratio}", (xc * 1.25, 0.78), fontsize=6.5,
                 color="0.35", rotation=-38, rotation_mode="anchor", ha="left", va="top")
axb.axhline(1, color="0.2", lw=1.0, ls="--")
OFF = {"AGB": (1.35, 1.55, "left", "bottom"),
       "SM": (1.28, 0.55, "left", "top"),
       "PR": (0.85, 1.45, "right", "bottom"),
       "SSS": (0.80, 0.50, "right", "top")}
for _, r in master.iterrows():
    x, y = np.sqrt(r.n_eff), r.phi
    col = C_UNVER if y > 1 else C_VER
    axb.plot(x, y, "o", ms=4.5, mfc=col, mec="white", mew=0.5, zorder=5)
    if r.id == "SIT":
        axb.annotate("Sea-ice thickness", (x, hi * 1.35), fontsize=6.8, color=col,
                     va="bottom", ha="center", zorder=6)
    else:
        fx, fy, ha, va = OFF[r.id]
        axb.annotate(LABEL[r.id], (x * fx, y * fy), fontsize=6.8, color=col,
                     va=va, ha=ha, zorder=6)
lo, hi = 3.447 / 2.7, 10.098 / 2.7
axb.plot([np.sqrt(325.2)] * 2, [lo, hi], color=C_UNVER, lw=2.2, alpha=0.55, zorder=4)
axb.set_xscale("log")
axb.set_yscale("log")
axb.set_xlim(1, 400)
axb.set_ylim(0.01, 20)
axb.set_xlabel("$\\sqrt{n_{\\mathrm{eff}}}$")
axb.set_ylabel("$\\Phi$")
axb.set_title("(b) $\\Phi$ falls as independent information grows", loc="left", fontsize=8.5)
save(fig, "fig1_power")

# ---------------------------------------------------------------------------
# Fig 2: the ranking figure (master).  Sea ice carries an interval.
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.6, 2.9))
order = ["SSS", "PR", "SM", "SIT", "AGB"]
ys = np.arange(len(order))[::-1]
for y, key in zip(ys, order):
    r = master[master.id == key].iloc[0]
    col = C_UNVER if r.phi > 1 else C_VER
    if key == "SIT":
        ax.plot([lo, hi], [y, y], color=col, lw=2.2, solid_capstyle="butt", zorder=4)
        for xe in (lo, hi):
            ax.plot([xe, xe], [y - 0.13, y + 0.13], color=col, lw=1.4, zorder=5)
        ax.plot(np.sqrt(lo * hi), y, "o", ms=4.5, mfc="white", mec=col, mew=1.0, zorder=6)
        ax.annotate(f"{lo:.1f}\u2013{hi:.1f}", (hi * 1.12, y), fontsize=7.5, color=col,
                    va="center")
    else:
        ax.plot(r.phi, y, "o", ms=6, mfc=col, mec="white", mew=0.6, zorder=5)
        ax.annotate(f"{r.phi:.3g}", (r.phi * 1.18, y), fontsize=7.5, color=col, va="center")
    ax.annotate("", xy=(0.0045, y), xytext=(r.phi if key != "SIT" else lo, y),
                arrowprops=dict(arrowstyle="-|>", color=col, lw=1.0, alpha=0.55,
                                shrinkA=0, shrinkB=0))
ax.axvline(1, color="0.15", lw=1.1, ls="--")
ax.axvspan(1, 30, color=C_UNVER, alpha=0.06)
ax.text(1.12, 4.35, "$\\Phi > 1$: not verifiable\nwith this data", fontsize=7.2,
        color=C_UNVER, va="top")
ax.set_xscale("log")
ax.set_xlim(0.004, 30)
ax.set_ylim(-0.55, 4.6)
ax.set_yticks(ys)
ax.set_yticklabels([LABEL[k] for k in order])
ax.set_xlabel("$\\Phi$ = MDE$_{80}$ / claim  (dimensionless)")
ax.xaxis.set_major_locator(LogLocator(base=10, numticks=8))
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:g}"))
ax.grid(axis="x", color=C_GRID, lw=0.5)
ax.set_axisbelow(True)
save(fig, "fig2_ranking")

# ---------------------------------------------------------------------------
# Fig 3: MDE80 versus claim, with Phi iso-lines
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(4.3, 3.6))
xs = np.logspace(-2.3, 2.4, 200)
LBLPOS = {10: (4.0, 40.0), 1: (12.0, 12.0), 0.1: (60.0, 6.0)}
for ph, ls in ((0.1, ":"), (1, "--"), (10, ":")):
    ax.plot(xs, ph * xs, ls=ls, lw=1.0, color="0.4" if ph != 1 else C_UNVER)
    ax.annotate(f"$\\Phi$ = {ph:g}", LBLPOS[ph], fontsize=7,
                color="0.35" if ph != 1 else C_UNVER, ha="left", va="center",
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.2))
ax.fill_between(xs, xs, 100, color=C_UNVER, alpha=0.07)
OFF3 = {"SIT": (1.25, 1.7, "left", "bottom"),
        "AGB": (0.65, 1.45, "right", "bottom"),
        "SM": (1.28, 1.55, "left", "bottom"),
        "PR": (1.30, 1.45, "left", "bottom"),
        "SSS": (0.72, 0.72, "right", "top")}
for _, r in master.iterrows():
    col = C_UNVER if r.phi > 1 else C_VER
    ax.plot(r.claim, r.mde80, "o", ms=5.5, mfc=col, mec="white", mew=0.6, zorder=5)
    fx, fy, ha, va = OFF3[r.id]
    ax.annotate(LABEL[r.id], (r.claim * fx, r.mde80 * fy), fontsize=6.8, color=col,
                ha=ha, va=va)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(0.005, 250)
ax.set_ylim(0.002, 300)
ax.set_xlabel("claim (same units as $\\sigma_d$)")
ax.set_ylabel("MDE$_{80}$")
ax.text(0.007, 60, "floor exceeds claim:\nno test can be built", fontsize=7, color=C_UNVER)
ax.grid(color=C_GRID, lw=0.4)
ax.set_axisbelow(True)
save(fig, "fig3_floor")

# ---------------------------------------------------------------------------
# Fig 4: sensitivity heat maps
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 5, figsize=(7.2, 2.5), sharey=True)
from matplotlib.colors import TwoSlopeNorm
norm = TwoSlopeNorm(vmin=-1.9, vcenter=0.0, vmax=1.1)
for ax, key in zip(axes, order):
    d = sens[sens.id == key]
    z = d.pivot(index="sigma_factor", columns="claim_factor", values="phi").values
    im = ax.imshow(np.log10(z), origin="lower", cmap="RdYlBu_r", norm=norm,
                   extent=[0.375, 1.625, 0.375, 1.625], aspect="auto")
    if z.min() <= 1 <= z.max():
        cs = ax.contour(np.linspace(0.5, 1.5, 5), np.linspace(0.5, 1.5, 5),
                        np.log10(z), levels=[0], colors="k", linewidths=1.2)
        ax.clabel(cs, fmt={0: "$\\Phi$=1"}, fontsize=6)
    ax.set_title(LABEL[key], fontsize=7.8)
    ax.text(0.5, -0.30, f"$\\Phi$ {z.min():.2f}\u2013{z.max():.2f}", transform=ax.transAxes,
            fontsize=6.3, ha="center", va="top", color="0.3")
    ax.set_xticks([0.5, 1.0, 1.5])
    ax.set_yticks([0.5, 1.0, 1.5])
    ax.set_xticklabels(["\u221250", "0", "+50"])
    ax.set_xlabel("claim (%)", fontsize=7.5)
    ax.tick_params(length=2.5)
axes[0].set_ylabel("$\\sigma_d$ (%)", fontsize=7.5)
axes[0].set_yticklabels(["\u221250", "0", "+50"])
cb = fig.colorbar(im, ax=axes, fraction=0.020, pad=0.02)
cb.set_label("$\\log_{10}\\Phi$", fontsize=7.5)
cb.ax.tick_params(labelsize=7)
save(fig, "fig4_sensitivity")

# ---------------------------------------------------------------------------
# Fig 5: the kernel ambiguity (why sea ice can only be an interval)
# ---------------------------------------------------------------------------
fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.1, 2.9),
                               gridspec_kw=dict(width_ratios=[1.0, 1.15], wspace=0.52))

d = np.linspace(0, 400, 400)
axa.plot(d, np.exp(-d / 326.0), color=C_VER, lw=1.6,
         label="exponential kernel, $L$ = 326 km")
anch = np.array([0, 25, 75, 150])
rho = np.array([1.0, 0.269, 0.080, 0.0])
axa.plot(anch, rho, "o-", color=C_UNVER, lw=1.6, ms=4.5, mfc="white", mew=1.0,
         label="empirical difference-field ACF")
axa.axhline(0, color="0.3", lw=0.7)
axa.set_xlim(0, 400)
axa.set_ylim(-0.12, 1.05)
axa.set_xlabel("separation distance (km)")
axa.set_ylabel("correlation of the difference field")
axa.legend(frameon=False, loc="upper right", handlelength=1.2)
axa.set_title("(a) two defensible kernels, same data", loc="left", fontsize=8.5)

bars = [("ACF, opt.", 3.406, C_UNVER, 0.45),
        ("ACF, arch. $m$=8", 3.447, C_UNVER, 1.0),
        ("exp., opt.", 8.40, C_VER, 0.45),
        ("exp., Kish", 10.098, C_VER, 1.0),
        ("exp., arch. $m$=8", 10.38, C_VER, 1.0)]
ys5 = np.arange(len(bars))[::-1]
for y, b in zip(ys5, bars):
    axb.barh([y], [b[1]], color=b[2], alpha=0.55 if b[3] < 1 else 0.95, height=0.62, lw=0)
    axb.annotate(f"{b[1]:.2f} cm  ($\\Phi$ = {b[1]/2.7:.2f})", (b[1] + 0.3, y),
                 fontsize=6.8, va="center", color="0.2")
axb.axvline(2.7, color="0.1", lw=1.2, ls="--")
axb.annotate("claim\n2.7 cm", (2.55, 4.55), fontsize=6.8, ha="right", va="top", color="0.1")
axb.set_yticks(ys5)
axb.set_yticklabels([b[0] for b in bars], fontsize=6.8)
axb.set_xlim(0, 16.5)
axb.set_ylim(-0.6, 4.9)
axb.set_xlabel("floor (cm)")
axb.set_title("(b) the floor cannot be narrowed below 3.4 cm", loc="left", fontsize=8.5)
save(fig, "fig5_kernel")

# ---------------------------------------------------------------------------
# Fig 6: Phi against design, for the two sigma_d ends of the sea-ice archive
# ---------------------------------------------------------------------------
design = pd.read_csv(DATA / "phi_archive_design.csv")

fig, ax = plt.subplots(figsize=(3.5, 2.9))
nn = np.logspace(np.log10(250), np.log10(30000), 400)
for sg, colour, lab in [(0.65, C_VER, r"independence: $\sigma_d$ = 0.65 m"),
                        (0.3892, C_UNVER, r"shared sensor: $\sigma_d$ = 0.389 m")]:
    ax.plot(nn, 2.802 * sg / (0.027 * np.sqrt(nn)), color=colour, lw=1.5, label=lab)
    sub = design[np.isclose(design["sigma_d"], sg)]
    ax.plot(sub["n_eff"], sub["phi"], "o", ms=4.5, mfc="white", mew=1.1, color=colour,
            zorder=3)
ax.axhline(1.0, color="0.1", lw=1.1, ls="--")
ax.annotate(r"$\Phi = 1$", (260, 1.04), fontsize=7, color="0.1")
for x, txt, ytxt in [(325.2, "campaign", 3.9), (4498.2, "14 winters", 0.30),
                     (13815.9, "43 months", 0.16)]:
    ax.annotate(txt, (x, ytxt), fontsize=6.8, ha="center", color="0.3")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel(r"independent units $n_{\mathrm{eff}}$")
ax.set_ylabel(r"$\Phi$")
ax.set_xlim(250, 30000)
ax.set_ylim(0.12, 12)
ax.legend(frameon=False, loc="lower left", handlelength=1.2, fontsize=6.8)
save(fig, "fig6_design")

# ---------------------------------------------------------------------------
# Fig 7: correlation of the CCI--CS2SMOS difference field, both grid axes
# ---------------------------------------------------------------------------
curve = pd.read_csv(DATA / "archive_acf_curve.csv")

fig, ax = plt.subplots(figsize=(3.5, 2.9))
ax.plot(curve["lag_km"], curve["rho_x"], "-", color=C_VER, lw=1.5,
        label=r"along $x$ ($\kappa_x$ = 7.69, 192 km)")
ax.plot(curve["lag_km"], curve["rho_y"], "--", color=C_UNVER, lw=1.5,
        label=r"along $y$ ($\kappa_y$ = 7.07, 177 km)")
ax.axhline(0, color="0.3", lw=0.7)
ax.set_xlim(0, 775)
ax.set_ylim(-0.1, 1.05)
ax.set_xlabel("lag (km)")
ax.set_ylabel("correlation of the difference field")
ax.legend(frameon=False, loc="upper right", handlelength=1.6, fontsize=6.8)
ax.set_title("2019-04, CCI minus CS2SMOS", loc="left", fontsize=8.5)
save(fig, "fig7_acf")

print("figures done")
