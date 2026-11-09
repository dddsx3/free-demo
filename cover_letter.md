# Cover letter — submission to *Computers & Geosciences*

**Manuscript title:** A dimensionless verification floor for model assessment: which accuracy claims can an observational archive actually resolve?

**Authors:** [AUTHOR GIVEN NAME] [AUTHOR SURNAME]^1, [AUTHOR GIVEN NAME] [AUTHOR SURNAME]^1, [AUTHOR GIVEN NAME] [AUTHOR SURNAME]^2

**Affiliations:** ^1[AUTHOR AFFILIATION 1]; ^2[AUTHOR AFFILIATION 2]

**Corresponding author:** [AUTHOR GIVEN NAME] [AUTHOR SURNAME], [AUTHOR EMAIL]

**Manuscript type:** Research paper

**Suggested editors:** [EDITOR NAME] (handling editor, computational methods for geoscience and model evaluation)

---

Dear Editors,

Please consider the enclosed manuscript for publication in *Computers & Geosciences* as a research paper presenting a computational method for model assessment.

**What the paper provides.** Model assessment compares a simulated field, or an observation-based reference, against independent truth and reports an error metric. It almost never asks whether that archive is large and accurate enough to resolve the discrepancy the assessment is asked to detect. We present a dimensionless method that answers the question and that can be applied to any variable, unit or domain. Its inputs are three quantities an assessment already reports — the standard deviation σ_d of the product–truth difference, the effective number of independent truth samples n_eff, and the magnitude of the asserted claim — and its output is a testability index Φ together with the largest claim the archive can support.

Writing n_eff for the Kish design effect (n_eff = n²/Σρ_ij) and "claim" for the asserted magnitude,

  Φ = 2.802 σ_d / (claim √n_eff) = MDE₈₀ / claim,

where 2.802 = z₀.₉₇₅ + z₀.₈₀ encodes a two-sided test at α = 0.05 with 80 % power. Φ > 1 means the claim lies below the verification floor of the archive and cannot be supported by it at the stated power; Φ < 1 means that it can be tested, not that it is correct. Φ is dimensionless, invariant to rescaling of both σ_d and the claim, and computable from quantities that assessment papers already report.

**Scope of the method, stated with the method.** The manuscript defines what the method assesses (one quantitative claim attached to a model field or to an observation-based reference), its inputs, its outputs (a testability index, the independent sample size n_eff Φ² that a claim would require, and the largest claim MDE₈₀ the archive can support) and its applicability boundary (one claim at a time; independent truth; a reported correlation model; a single space–time scale). Two of the five candidate domains fail the provenance condition and are reported as "not assessable" rather than estimated.

**Why this belongs in *Computers & Geosciences*.** The contribution is a computational method, not a result about one Earth system: a criterion that operates on the comparison between a modelled or reference field and truth, that can be implemented in a few dozen lines, and that returns a number a reader can recompute. It gives the community a way to state, before an evaluation is run, what that evaluation can and cannot decide, and it converts the design question into a budget line (n_eff Φ² independent samples). As the journal requires, the submission carries a complete, tested implementation rather than an illustration of one, and a public code repository exists at submission.

**Example implementation and code availability.** `code/phi_core.py` holds the three closures, the constants of the criterion and the five domain records; `code/run_all.py` runs the arithmetic, checks every headline number against the manuscript, regenerates the seven figures and builds the PDF. The Code availability section lists the dependency versions (Python 3.14.2, NumPy 2.4.1, SciPy 1.17.0, pandas 3.0.0, Matplotlib 3.10.8), the run commands, and the seven derived tables written to `data/` and the seven figures written to `figures/`. The public repository required by the journal is prepared, accompanies the submission and is openly available at https://github.com/dddsx3/free-demo; the archive DOI, which can only be minted after the first public release, replaces `[DOI: ZENODO-TO-BE-ASSIGNED]`. A nine-test suite (`python -m pytest code`) reproduces the five headline values and the three closure identities.

**What the five domains show.** Salinity (Φ = 0.019), precipitation (Φ = 0.043) and soil moisture (Φ = 0.24) are comfortably verifiable; the bottleneck in those domains is sensor accuracy, not verification capacity. Regional forest biomass (Φ = 2.71) and Arctic sea-ice thickness (Φ = 1.3–3.7) are not verifiable at their published claims. The ordering, not any single value, is the result.

**The honesty requirement that shaped the paper.** Sea-ice thickness cannot be reduced to a single number, and we do not pretend otherwise. Two defensible correlation kernels applied to the same difference field give floors of 3.447 cm and 10.38 cm — a factor of 2.5 to 3.0 — and the manuscript reports the resulting interval (1.3–3.7) with error bars in every figure and table where it appears. The kernel ambiguity is derived in the Methods, not relegated to a footnote, because the credibility of the whole exercise rests on showing exactly where the arithmetic stops being determinate. A ±50 % perturbation of σ_d and of the claim is likewise reported cell by cell (Fig. 5, Table 4): salinity, precipitation and soil moisture stay verifiable across the entire perturbation box; sea ice stays unverifiable at its exponential-kernel bound; biomass crosses Φ = 1 only at the most optimistic corner (Φ = 0.90), which we flag as a falsification condition rather than bury.

**What the paper does not claim.** Φ > 1 is not a statement that a study is worthless, and Φ < 1 is not a certificate of correctness. Section 5.2 draws that boundary explicitly and gives three counter-examples: the SMAP mission accuracy claim has Φ = 0.24 and was met at only 18 of 34 core validation sites (Colliander et al., 2017); the IMERG daily product has Φ = 0.043 and still missed its stated error bound in an independent gauge comparison (Li et al., 2018); and a global biomass calibration with Φ = 0.18 is unassessable because of train–test leakage. The criterion is necessary but not sufficient, and the manuscript says so in the abstract, in Sect. 5.2 and in the concluding paragraph.

**Provenance and reproducibility.** Table 1 gives, domain by domain, the raw count n, its source, the closure rule that converts n into n_eff, the value of σ_d with its provenance, and the claim with its provenance; two candidate domains for which a defensible provenance could not be assembled (global biomass and snow depth) are listed as "not assessable" and are excluded from the ranking rather than estimated. In the preprint layout of the journal's class (single wide column, 12 pt) the manuscript runs to 40 pages, with seven figures and four tables; the abstract is 286 words. The reference list is generated from a BibTeX file of 60 entries: 59 were resolved against Crossref or DataCite by DOI or by title and the 60th is the 1965 Kish monograph, typeset by hand. All 60 are cited in the text and are the entries typeset in the PDF, so the file, the citations and the printed list agree. The resolution log is included.

**Declarations.** The manuscript is original, is not under consideration elsewhere, and all authors have approved the submission. We declare no competing interests. Author contributions, funding, acknowledgements and data availability statements are marked as placeholders for completion before submission.

We believe the paper will interest the journal's readership in model evaluation, data assimilation and observational reference preparation alike, and we hope you will find it suitable for review.

Yours sincerely,

[AUTHOR GIVEN NAME] [AUTHOR SURNAME]
on behalf of all authors
[AUTHOR AFFILIATION 1]
[AUTHOR EMAIL]
[DATE]

---

## Suggested reviewers (to be completed by the corresponding author)

| # | Name | Affiliation | Expertise | Conflict |
|---|------|-------------|-----------|----------|
| 1 | [REVIEWER NAME] | [AFFILIATION] | Statistical power and equivalence testing in geoscience | None |
| 2 | [REVIEWER NAME] | [AFFILIATION] | Sea-ice thickness validation and CryoSat-2/SMOS retrieval | None |
| 3 | [REVIEWER NAME] | [AFFILIATION] | Satellite soil moisture validation and core-site networks | None |
| 4 | [REVIEWER NAME] | [AFFILIATION] | Precipitation product evaluation and gauge networks | None |
| 5 | [REVIEWER NAME] | [AFFILIATION] | Forest biomass remote sensing and GEDI calibration | None |

## Opposed reviewers

None. [LIST ANY EXCLUSIONS HERE]

## Alternative journal

None requested. The manuscript is submitted to *Computers & Geosciences* as its
first choice; if the editors judge it out of scope we would welcome a transfer
suggestion from them rather than nominate a venue in advance.
