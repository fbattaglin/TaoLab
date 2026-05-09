"""Microcopy + glossary for Tao Lab v2.

Two layers of content:

1. **Voice-aware microcopy** (`copy.<key>(voice)`): the same UI string in
   "plain" or "technical" register. Used for headlines, helper text, and
   button captions where the bridge between business and DS readers matters.

2. **Glossary entries** (`GLOSSARY[term]`): structured definitions for the
   `Explainer` component. Each entry has a one-line short answer (rendered as
   a popover) and a longer description (rendered in the drawer). All entries
   are stable across voice — the *plain ↔ technical* contract is that even
   the technical reader benefits from a tight definition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Voice = Literal["plain", "technical"]


@dataclass(frozen=True)
class CopyPair:
    plain: str
    technical: str

    def __call__(self, voice: Voice) -> str:
        return self.plain if voice == "plain" else self.technical


# ─────────────────────── Top-level UI copy ───────────────────────
class _Copy:
    # Header / shell
    voice_toggle_label = CopyPair(
        plain="Reader",
        technical="Reader",
    )
    voice_plain = CopyPair(plain="Plain", technical="Plain")
    voice_technical = CopyPair(plain="Technical", technical="Technical")

    # Step 1 — Data
    step1_hero_headline = CopyPair(
        plain="From raw data to a confident verdict.",
        technical="From raw data to a defensible experimental verdict.",
    )
    step1_hero_sub = CopyPair(
        plain="Drop your experiment data and we'll guide you through the analysis.",
        technical="Upload an experiment dataset; we'll diagnose, configure, and run the appropriate analysis.",
    )
    step1_drop_label = CopyPair(
        plain="Drop a CSV or Excel file here",
        technical="Upload experiment data (CSV / XLSX)",
    )
    step1_samples_label = CopyPair(
        plain="Or try a sample dataset:",
        technical="Or load a canonical example:",
    )
    step1_continue = CopyPair(
        plain="Continue →",
        technical="Continue to Diagnosis →",
    )

    # Step 2 — Diagnose
    step2_method_card_eyebrow = CopyPair(
        plain="Recommended approach",
        technical="Recommended method",
    )
    step2_alternatives_link = CopyPair(
        plain="Why not the alternatives?",
        technical="Compare available methods",
    )
    step2_health_title = CopyPair(
        plain="Data health",
        technical="Data Health Score",
    )
    step2_use_recommended = CopyPair(
        plain="Use this approach →",
        technical="Use recommended method →",
    )
    step2_best_fit_badge = CopyPair(
        plain="Best fit",
        technical="Recommended",
    )
    step2_also_viable_badge = CopyPair(
        plain="Also viable",
        technical="Alternative",
    )
    step2_requirements_label = CopyPair(
        plain="What you'll need to provide",
        technical="Required inputs",
    )
    step2_use_selected = CopyPair(
        plain="Use this approach →",
        technical="Proceed with selected method →",
    )
    step2_ambiguity_note = CopyPair(
        plain="This data could fit more than one method. Pick the one that matches how your data was collected.",
        technical="Multiple methods are viable. Selection depends on the data-generating process.",
    )

    # Step 3 — Configure
    step3_variant_eyebrow = CopyPair(
        plain="Comparison",
        technical="Variant assignment",
    )
    step3_metrics_eyebrow = CopyPair(
        plain="What to measure",
        technical="Metrics",
    )
    step3_advanced_label = CopyPair(
        plain="Advanced settings",
        technical="Advanced parameters",
    )
    step3_run = CopyPair(
        plain="Run analysis →",
        technical="Run analysis →",
    )

    # Step 5 — Prescription (used in Phase C; defined here for cohesion)
    verdict_ship = CopyPair(plain="Ship it.", technical="Ship — significant positive effect.")
    verdict_hold = CopyPair(plain="Hold.", technical="Hold — inconclusive or caveated.")
    verdict_no_ship = CopyPair(plain="Don't ship.", technical="Reject — significant adverse effect.")


copy = _Copy()


# ─────────────────────── Glossary ───────────────────────
@dataclass(frozen=True)
class GlossaryEntry:
    term: str
    short: str       # one-liner for the tooltip
    description: str # 2-4 sentences for the drawer / "Learn more"
    plain_synonym: str = ""  # optional plain-language alias shown above the term


GLOSSARY: dict[str, GlossaryEntry] = {
    "p_value": GlossaryEntry(
        term="p-value",
        plain_synonym="how likely the result is just random noise",
        short="The probability of seeing a result this extreme if the treatment had no effect.",
        description=(
            "If the p-value is small (e.g. < 0.05), the data are unlikely under the assumption of no effect, "
            "so we treat the result as statistically significant. A p-value is *not* the probability that the "
            "treatment has no effect, and a small p-value alone does not tell you the size or business "
            "importance of the effect."
        ),
    ),
    "alpha": GlossaryEntry(
        term="α (significance threshold)",
        plain_synonym="how much false-positive risk we accept",
        short="The maximum probability of declaring a 'win' when there is none.",
        description=(
            "α is the false-positive rate we're willing to tolerate. The default 0.05 means we accept a 5% "
            "chance of incorrectly calling a non-effect 'significant'. Lower α (0.01) makes the test "
            "stricter; higher α (0.10) makes it more sensitive but more error-prone."
        ),
    ),
    "ci": GlossaryEntry(
        term="confidence interval",
        plain_synonym="the plausible range for the true effect",
        short="The range that contains the true effect with the stated probability (e.g. 95%).",
        description=(
            "A 95% confidence interval means: if we re-ran this experiment many times, 95% of the intervals "
            "we'd compute would contain the true effect. If the interval crosses zero, we cannot rule out "
            "'no effect'. Width tells you precision — narrow is more informative."
        ),
    ),
    "srm": GlossaryEntry(
        term="SRM (Sample Ratio Mismatch)",
        plain_synonym="the groups aren't sized the way they should be",
        short="A check that the actual control/treatment split matches what was expected.",
        description=(
            "If you randomised 50/50 but observe 47/53, that gap might just be noise — or it might indicate "
            "a bug in assignment, logging, or filtering. SRM uses a chi-squared test (p < 0.001) to flag "
            "splits that are very unlikely under correct randomisation. When SRM fires, every downstream "
            "result becomes suspect: fix the pipeline before trusting the analysis."
        ),
    ),
    "delta_method": GlossaryEntry(
        term="Delta Method",
        plain_synonym="the right way to compare ratios",
        short="A variance estimator for ratios (e.g. CTR = clicks/impressions).",
        description=(
            "Naively running a t-test on per-row ratios overstates uncertainty because numerator and "
            "denominator are correlated and not i.i.d. The Delta Method propagates the variance of both "
            "components and their covariance, giving correct standard errors. Tao Lab applies it "
            "automatically when you define a ratio metric."
        ),
    ),
    "bh_correction": GlossaryEntry(
        term="Benjamini-Hochberg correction",
        plain_synonym="adjusting for testing many things at once",
        short="Adjusts p-values when you test multiple metrics, controlling the False Discovery Rate.",
        description=(
            "Each independent test at α = 0.05 has a 5% false-positive rate. Test 20 metrics and you'd "
            "expect one false positive on average even with no real effects. The Benjamini-Hochberg "
            "procedure adjusts the threshold so the proportion of false discoveries among your "
            "'significant' metrics stays bounded by α. Tao Lab applies it automatically when you analyse "
            "more than one metric."
        ),
    ),
    "frequentist_vs_bayesian": GlossaryEntry(
        term="Frequentist vs Bayesian",
        plain_synonym="two ways to read the evidence",
        short="Two statistical frameworks: Frequentist gives p-values; Bayesian gives posterior probabilities.",
        description=(
            "Frequentist tests answer 'how surprising is this data, assuming no effect?' (the p-value). "
            "Bayesian methods answer 'given the data, what's the probability the treatment is better?' "
            "(the posterior). For most A/B tests they agree directionally; Bayesian gives richer probability "
            "statements at the cost of slower fits and the need for a prior."
        ),
    ),
    "effect_size": GlossaryEntry(
        term="effect size (Cohen's d)",
        plain_synonym="how big the difference is, in units of noise",
        short="A standardised measure of how large the treatment effect is, regardless of sample size.",
        description=(
            "Cohen's d expresses the difference between groups in units of pooled standard deviation. "
            "Rules of thumb: 0.2 is small, 0.5 is medium, 0.8 is large. Useful when p-values are small "
            "due to sample size but the practical effect may not be meaningful."
        ),
    ),
    "cuped": GlossaryEntry(
        term="CUPED (covariate adjustment)",
        plain_synonym="using pre-experiment data to reduce noise",
        short="A variance reduction technique that subtracts predictable variation from each unit's outcome.",
        description=(
            "If users had measurable behaviour *before* the experiment (e.g. last 30 days of revenue), "
            "we can use that to predict their counterfactual outcome and remove that explained variance. "
            "Result: tighter confidence intervals, smaller required sample sizes, no change to the "
            "estimated effect."
        ),
    ),
}
