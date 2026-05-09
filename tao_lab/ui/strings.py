"""Microcopy + glossary for Tao Lab v2.

Three layers of content:

1. **Voice-aware microcopy** (`copy.<key>(voice)`): the same UI string in
   "plain" or "technical" register. Used for headlines, helper text, and
   button captions where the bridge between business and DS readers matters.

2. **Glossary entries** (`GLOSSARY[term]`): structured definitions for the
   `Explainer` component. Each entry has a one-line short answer (rendered as
   a popover), a longer description (rendered in the drawer), and a
   ``first_use`` hint shown the first time the term appears on each step.

3. **Method blurbs** (`METHOD_BLURBS[method_key]`): voice-aware descriptions
   and assumption summaries for each analysis method, centralised so
   ``method_card.py`` renders the right reading level.
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
        plain="Or try a sample experiment:",
        technical="Or load a canonical example:",
    )
    step1_continue = CopyPair(
        plain="Continue →",
        technical="Continue to Diagnosis →",
    )
    step1_question_label = CopyPair(
        plain="What are you trying to learn from this data?",
        technical="Business question (optional, included in the report)",
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
    step3_group_col_label = CopyPair(
        plain="Group column",
        technical="Assignment column",
    )
    step3_metrics_eyebrow = CopyPair(
        plain="What to measure",
        technical="Metrics",
    )
    step3_outcome_label = CopyPair(
        plain="What outcome are you measuring?",
        technical="Continuous metrics to evaluate",
    )
    step3_outcome_help = CopyPair(
        plain="Pick the numbers you want to compare between the groups — e.g. revenue, sessions, time on page.",
        technical="Per-unit numeric outcomes. We'll compare averages between groups.",
    )
    step3_advanced_label = CopyPair(
        plain="Advanced settings",
        technical="Advanced parameters",
    )
    step3_run = CopyPair(
        plain="Run analysis →",
        technical="Run analysis →",
    )
    step3_why_settings = CopyPair(
        plain="Why are these fields pre-filled?",
        technical="Inferred configuration",
    )

    # Step 4 — Run
    step4_title = CopyPair(
        plain="Analyzing your experiment...",
        technical="Running analysis...",
    )
    step4_progress_srm = CopyPair(
        plain="Checking that the groups split the way you intended...",
        technical="Running SRM check...",
    )
    step4_progress_fit = CopyPair(
        plain="Measuring the effect of the change...",
        technical="Fitting statistical model...",
    )
    step4_progress_narrate = CopyPair(
        plain="Writing up the findings...",
        technical="Generating prescription...",
    )
    step4_progress_viz = CopyPair(
        plain="Preparing charts...",
        technical="Rendering diagnostics...",
    )

    # Step 5 — Prescription
    step5_srm_pass = CopyPair(
        plain="Groups split as expected",
        technical="SRM passed",
    )
    step5_srm_fail = CopyPair(
        plain="Groups aren't split the way they should be",
        technical="SRM detected",
    )
    step5_forest_title = CopyPair(
        plain="How much each metric changed",
        technical="Lift & 95% confidence intervals",
    )
    step5_metrics_title = CopyPair(
        plain="Results per metric",
        technical="Per-metric breakdown",
    )
    step5_lift_label = CopyPair(
        plain="How much it changed",
        technical="Relative lift",
    )
    step5_pvalue_label = CopyPair(
        plain="Certainty",
        technical="p-value",
    )
    step5_sig_yes = CopyPair(
        plain="Real difference detected",
        technical="Statistically significant",
    )
    step5_sig_no = CopyPair(
        plain="Could be random noise",
        technical="Not significant",
    )
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
    plain_synonym: str = ""   # plain-language alias shown in plain mode
    learn_more: str = ""      # citation / URL for deep dives
    first_use: str = ""       # inline hint shown the first time the term appears on a step


GLOSSARY: dict[str, GlossaryEntry] = {
    # ── Core statistical concepts ──
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
        first_use="the chance this result is just noise — smaller means more confident",
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
        first_use="the false-positive rate you're willing to accept (default 5%)",
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
        first_use="the range where the true effect most likely falls",
    ),
    "statistical_significance": GlossaryEntry(
        term="statistical significance",
        plain_synonym="the result is unlikely to be just noise",
        short="The effect is large enough relative to randomness that we consider it real.",
        description=(
            "When we say a result is 'statistically significant', we mean the chance of seeing "
            "this large an effect (or larger) purely by random variation is below our threshold "
            "(typically 5%). It does NOT mean the effect is large or important — only that it is "
            "distinguishable from no effect at all."
        ),
        first_use="the difference is large enough relative to randomness that we treat it as real",
    ),
    "practical_significance": GlossaryEntry(
        term="practical significance",
        plain_synonym="whether the effect is big enough to matter",
        short="Whether the observed effect is large enough to justify action.",
        description=(
            "A statistically significant result can still be too small to care about. Practical "
            "significance asks: is the change big enough to justify the cost of shipping it? "
            "A 0.01% lift in revenue might be statistically significant with millions of users "
            "but may not be worth the engineering effort to maintain."
        ),
        first_use="whether the effect is large enough to justify acting on it",
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
        first_use="how big the difference is in standardised units — 0.2 small, 0.5 medium, 0.8 large",
    ),

    # ── Experiment structure ──
    "assignment_column": GlossaryEntry(
        term="assignment column",
        plain_synonym="the column that says which group each row belongs to",
        short="The column in your data that indicates which variant (e.g. Control or Treatment) each unit was in.",
        description=(
            "Also called the 'group column'. This column is what separates your data into the groups you "
            "want to compare. Common names include 'variant', 'group', 'arm', 'bucket', or 'condition'. "
            "It typically has two values — one for the group that didn't get the change (control) and one "
            "for the group that did (treatment)."
        ),
        first_use="the column that says which group each row belongs to (e.g. Control vs Treatment)",
    ),
    "treatment_group": GlossaryEntry(
        term="treatment group",
        plain_synonym="the group that got the change",
        short="The set of units that received the change you're testing.",
        description=(
            "In an experiment, the treatment group is the set of users (or stores, sessions, etc.) "
            "that experienced the new version — the redesigned page, the new pricing, the updated email. "
            "We compare their outcomes against the control group to measure the change's effect."
        ),
        first_use="the group that received the change you're testing",
    ),
    "control_group": GlossaryEntry(
        term="control group",
        plain_synonym="the group that did NOT get the change",
        short="The set of units that experienced the original version (no change).",
        description=(
            "The control group serves as the baseline. They saw the existing experience — the old page, "
            "the old pricing, the original email. By comparing the treatment group's outcomes to the "
            "control group's, we can attribute any difference to the change itself rather than to "
            "external factors."
        ),
        first_use="the group that did NOT receive the change — the baseline for comparison",
    ),
    "outcome_metric": GlossaryEntry(
        term="outcome metric",
        plain_synonym="the number you're trying to move",
        short="The measurable quantity you want the experiment to improve (e.g. revenue, clicks, retention).",
        description=(
            "The outcome metric (or 'primary metric') is the number that tells you whether the change "
            "worked. Choose the metric closest to the business goal. Common examples: revenue per user, "
            "conversion rate, time on page, retention rate. Avoid vanity metrics that don't connect to "
            "real outcomes."
        ),
        first_use="the number you want the experiment to improve — e.g. revenue, clicks, retention",
    ),
    "ratio_metric": GlossaryEntry(
        term="ratio metric",
        plain_synonym="a metric that's one number divided by another",
        short="A metric defined as numerator / denominator (e.g. CTR = clicks / impressions).",
        description=(
            "Ratio metrics like click-through rate (clicks / impressions) or average order value "
            "(revenue / orders) need special statistical treatment. A standard t-test on per-row ratios "
            "gives wrong uncertainty estimates because numerator and denominator are correlated. "
            "Tao Lab uses the Delta Method to handle this automatically."
        ),
        first_use="a metric that's one number divided by another (e.g. CTR = clicks / impressions)",
    ),

    # ── Lift ──
    "lift_absolute": GlossaryEntry(
        term="absolute lift",
        plain_synonym="how much the number changed",
        short="The raw difference between the treatment and control averages.",
        description=(
            "Absolute lift = treatment average − control average. If control averaged $100 and "
            "treatment averaged $110, the absolute lift is $10. This is the number that translates "
            "most directly into business impact (e.g. '$10 more revenue per customer')."
        ),
        first_use="the raw difference between the two groups' averages",
    ),
    "lift_relative": GlossaryEntry(
        term="relative lift",
        plain_synonym="the percentage change",
        short="The lift expressed as a percentage of the control average.",
        description=(
            "Relative lift = (treatment − control) / control. If control averaged $100 and treatment "
            "averaged $110, the relative lift is +10%. Useful for comparing across metrics with "
            "different scales, but can be misleading when the baseline is small."
        ),
        first_use="the change expressed as a percentage of the baseline",
    ),

    # ── Checks & corrections ──
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
        first_use="a check that the groups are sized the way you intended",
    ),
    "group_balance": GlossaryEntry(
        term="group balance",
        plain_synonym="whether the groups are similar before the change",
        short="Whether the control and treatment groups are comparable on observable characteristics.",
        description=(
            "For a fair comparison, the groups should look similar on everything *except* the change "
            "you introduced. If the treatment group has higher incomes or more active users, the observed "
            "effect might be due to those differences, not the change. Balance checks compare group "
            "characteristics before the experiment starts."
        ),
        first_use="whether the groups were similar before the change was introduced",
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
        learn_more="Deng et al. (2017). 'Trustworthy Analysis of Online A/B Tests.' WSDM.",
        first_use="a technique for correctly estimating uncertainty in ratio metrics",
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
        first_use="adjusts for the extra false-positive risk of testing multiple metrics",
    ),

    # ── Frameworks & engines ──
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
        first_use="Frequentist gives p-values, Bayesian gives probabilities — two ways to read the same evidence",
    ),
    "posterior_probability": GlossaryEntry(
        term="posterior probability",
        plain_synonym="the probability the treatment is better",
        short="After seeing the data, the probability that the treatment outperforms control.",
        description=(
            "In Bayesian analysis, the posterior probability answers the question most decision-makers "
            "actually want: 'how likely is it that the treatment is better?' A posterior probability of "
            "0.97 means there's a 97% chance the treatment outperforms control. Unlike p-values, this "
            "is a direct statement about the probability of the hypothesis."
        ),
        first_use="the probability the treatment is actually better, given the data you observed",
    ),
    "hdi_credible_interval": GlossaryEntry(
        term="HDI (highest density interval)",
        plain_synonym="the most likely range for the true effect (Bayesian)",
        short="The narrowest interval that contains a specified fraction (e.g. 95%) of the posterior.",
        description=(
            "The HDI is the Bayesian analogue of a confidence interval. A 95% HDI contains the 95% most "
            "probable values of the treatment effect. Unlike a frequentist CI, you can directly say "
            "'there's a 95% probability the true effect is in this range'. The HDI is always the "
            "narrowest such interval."
        ),
        first_use="the Bayesian version of a confidence interval — the most probable range for the effect",
    ),
    "rope": GlossaryEntry(
        term="ROPE (Region of Practical Equivalence)",
        plain_synonym="the range of effects too small to care about",
        short="A pre-defined range around zero within which any effect is 'practically zero'.",
        description=(
            "ROPE is a Bayesian concept for separating statistical from practical significance. "
            "You define a range (e.g. -1% to +1% lift) that you consider 'close enough to zero to "
            "ignore'. If the HDI falls entirely inside the ROPE, the effect is practically zero. If "
            "it falls entirely outside, it's practically meaningful."
        ),
        first_use="a range of effects so small they'd be too trivial to act on",
    ),

    # ── Causal & observational ──
    "confounder": GlossaryEntry(
        term="confounder",
        plain_synonym="a factor that affects both the treatment and the outcome",
        short="A variable that influences both who gets the treatment and the outcome, creating a spurious association.",
        description=(
            "Confounders create the illusion of an effect where none exists (or hide a real one). "
            "Example: ice cream sales and drowning rates both go up in summer — temperature is the "
            "confounder. In observational studies, confounders must be identified and adjusted for, "
            "otherwise the estimated effect is biased."
        ),
        first_use="a factor that affects both who got the treatment and the outcome, which can distort results",
    ),
    "randomization": GlossaryEntry(
        term="randomization",
        plain_synonym="randomly assigning units to groups",
        short="The process of randomly assigning units to treatment or control.",
        description=(
            "Randomization is the gold standard for causal inference because it ensures, on average, "
            "that the groups are balanced on all characteristics — observed and unobserved. "
            "When randomization is absent (observational data), more sophisticated methods are needed "
            "to control for confounders."
        ),
        first_use="randomly assigning each unit to a group — the gold standard for fair comparisons",
    ),
    "counterfactual": GlossaryEntry(
        term="counterfactual",
        plain_synonym="what would have happened without the change",
        short="The outcome that would have occurred in the absence of the treatment.",
        description=(
            "The fundamental question of causal inference: what would the outcome have been if the "
            "treatment had *not* been applied? In an A/B test, the control group approximates this. "
            "In time-series analysis, we estimate it by extrapolating pre-period trends. The "
            "counterfactual is never directly observed — it's always estimated."
        ),
        first_use="an estimate of what would have happened without the change",
    ),

    # ── Time-series ──
    "pre_post_period": GlossaryEntry(
        term="pre-period / post-period",
        plain_synonym="before and after the change",
        short="The time before the intervention (pre) and after it (post).",
        description=(
            "In time-series analysis, the pre-period is the time before the change was introduced. "
            "We use it to learn the baseline pattern. The post-period is the time after the change, "
            "where we look for a shift. More pre-period data generally means a more reliable "
            "counterfactual estimate."
        ),
        first_use="the data before the change (used to learn the baseline) and after it (where we look for the effect)",
    ),
    "intervention_date": GlossaryEntry(
        term="intervention date",
        plain_synonym="the date the change went live",
        short="The specific date when the treatment or change was introduced.",
        description=(
            "In time-series analysis, the intervention date splits the data into a pre-period "
            "(before the change) and a post-period (after the change). Choosing the right date is "
            "critical — if the actual rollout was gradual, pick the date when most users/units "
            "were affected."
        ),
        first_use="the date when the change or intervention went live",
    ),

    # ── Variance reduction ──
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
        learn_more="Deng et al. (2013). 'Improving the Sensitivity of Online Controlled Experiments by Utilizing Pre-Experiment Data.' WSDM.",
        first_use="uses each unit's pre-experiment behaviour to reduce noise in the estimate",
    ),

    # ── Power ──
    "power_mde": GlossaryEntry(
        term="power / MDE",
        plain_synonym="whether the test can detect an effect this small",
        short="The probability the test detects a real effect (power), and the smallest effect it can detect (MDE).",
        description=(
            "Power (typically 80%) is the probability of correctly detecting a real effect. "
            "The Minimum Detectable Effect (MDE) is the smallest effect size the test can reliably "
            "catch at the given sample size and α. If your observed effect is smaller than the MDE, "
            "the test may miss it even though the effect is real."
        ),
        first_use="whether your test has enough data to detect an effect of the size you care about",
    ),
}


# ─────────────────────── Method blurbs ───────────────────────
@dataclass(frozen=True)
class MethodBlurb:
    """Voice-aware description and assumptions for a single analysis method."""
    display_name: str
    plain: str              # 1-2 sentence "what is this for" in business language
    technical: str           # same, in statistical language
    assumptions_plain: str   # what the method needs to be valid, business language
    assumptions_technical: str  # same, statistical language


METHOD_BLURBS: dict[str, MethodBlurb] = {
    "A/B Test": MethodBlurb(
        display_name="A/B Test",
        plain=(
            "Compares outcomes between two groups — the ones who got the change and the "
            "ones who didn't. Best when you randomly assigned units to each group."
        ),
        technical=(
            "Two groups, randomised. We compare averages with Welch's t-test "
            "(robust to unequal variances) and apply the Delta Method for ratio "
            "metrics so confidence intervals stay valid."
        ),
        assumptions_plain=(
            "Assumes the assignment to groups was random or random-like. "
            "If it wasn't, consider Causal Inference instead."
        ),
        assumptions_technical=(
            "Requires randomised assignment (SUTVA, no interference). "
            "Welch's t-test is robust to unequal variances. "
            "Ratio metrics get Delta-method SEs."
        ),
    ),
    "Time-Series Intervention": MethodBlurb(
        display_name="Time-Series Intervention",
        plain=(
            "Measures the impact of a change by comparing what happened after the "
            "change date to what would have happened without it. Best when you "
            "rolled something out to everyone on a specific date."
        ),
        technical=(
            "A single series with a known intervention date. We fit a counterfactual "
            "to the pre-period, then compare it against the observed post-period."
        ),
        assumptions_plain=(
            "Assumes nothing else changed on or around the intervention date that could "
            "also affect the metric. If another campaign launched the same week, the "
            "estimate may be confounded."
        ),
        assumptions_technical=(
            "Assumes stable pre-period dynamics, no concurrent confounding interventions, "
            "and sufficient pre-period data for counterfactual estimation."
        ),
    ),
    "Causal Inference": MethodBlurb(
        display_name="Observational Causal Inference",
        plain=(
            "Estimates the effect of a change even when you didn't randomly assign who got it. "
            "Uses other measured factors (like demographics or prior behaviour) to adjust for "
            "differences between the groups."
        ),
        technical=(
            "No randomisation, but treatment, outcome, and plausible confounders are all "
            "observed. We use DoWhy to identify a valid estimand and EconML's Double "
            "Machine Learning to estimate it."
        ),
        assumptions_plain=(
            "Assumes you've included every important factor that affects both who got the "
            "treatment and the outcome. If there's a hidden factor you haven't measured, "
            "the result may be wrong."
        ),
        assumptions_technical=(
            "Requires conditional ignorability (no unmeasured confounders). "
            "DML uses cross-fitting for doubly-robust estimation. "
            "Sensitive to model specification if overlap is poor."
        ),
    ),
    "Exploratory": MethodBlurb(
        display_name="Exploratory mode",
        plain=(
            "We can't identify a clear experiment structure in this data. We'll surface "
            "distributions and patterns to help you understand the dataset before "
            "designing a test."
        ),
        technical=(
            "We can't infer a clear experimental structure. Surface distributions "
            "and correlations to understand the data before designing a test."
        ),
        assumptions_plain="No statistical assumptions — this is descriptive, not inferential.",
        assumptions_technical="Descriptive only. No causal or inferential claims.",
    ),
}
