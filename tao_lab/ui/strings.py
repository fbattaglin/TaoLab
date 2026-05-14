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


Voice = Literal["signal", "spectrum"]


@dataclass(frozen=True)
class CopyPair:
    signal: str
    spectrum: str

    def __call__(self, voice: Voice) -> str:
        return self.signal if voice == "signal" else self.spectrum


# ─────────────────────── Top-level UI copy ───────────────────────
class _Copy:
    # Header / shell
    voice_toggle_label = CopyPair(
        signal="Reader",
        spectrum="Reader",
    )
    voice_signal = CopyPair(signal="Signal", spectrum="Signal")
    voice_spectrum = CopyPair(signal="Spectrum", spectrum="Spectrum")

    # Step 1 — Data
    step1_hero_headline = CopyPair(
        signal="From raw data to a confident verdict.",
        spectrum="From raw data to a defensible experimental verdict.",
    )
    step1_hero_sub = CopyPair(
        signal="Drop your experiment data and we'll guide you through the analysis.",
        spectrum="Upload an experiment dataset; we'll diagnose, configure, and run the appropriate analysis.",
    )
    step1_drop_label = CopyPair(
        signal="Drop a CSV or Excel file here",
        spectrum="Upload experiment data (CSV / XLSX)",
    )
    step1_samples_label = CopyPair(
        signal="Or try a sample experiment:",
        spectrum="Or load a canonical example:",
    )
    step1_continue = CopyPair(
        signal="Continue →",
        spectrum="Continue to Diagnosis →",
    )
    step1_question_label = CopyPair(
        signal="What are you trying to learn from this data?",
        spectrum="Business question (optional, included in the report)",
    )

    # Step 2 — Diagnose
    step2_method_card_eyebrow = CopyPair(
        signal="Recommended approach",
        spectrum="Recommended method",
    )
    step2_alternatives_link = CopyPair(
        signal="Why not the alternatives?",
        spectrum="Compare available methods",
    )
    step2_health_title = CopyPair(
        signal="Data health",
        spectrum="Data Health Score",
    )
    step2_use_recommended = CopyPair(
        signal="Use this approach →",
        spectrum="Use recommended method →",
    )
    step2_best_fit_badge = CopyPair(
        signal="Best fit",
        spectrum="Recommended",
    )
    step2_also_viable_badge = CopyPair(
        signal="Also viable",
        spectrum="Alternative",
    )
    step2_requirements_label = CopyPair(
        signal="What you'll need to provide",
        spectrum="Required inputs",
    )
    step2_use_selected = CopyPair(
        signal="Use this approach →",
        spectrum="Proceed with selected method →",
    )
    step2_ambiguity_note = CopyPair(
        signal="This data could fit more than one method. Pick the one that matches how your data was collected.",
        spectrum="Multiple methods are viable. Selection depends on the data-generating process.",
    )
    step2_override_expander = CopyPair(
        signal="Choose a different method",
        spectrum="Override automatic method selection",
    )
    step2_override_hint = CopyPair(
        signal="Our recommendation is based on your data's structure. If you know your analysis goal, pick any method below.",
        spectrum="Engine score reflects structural signals only. Override if domain knowledge contradicts the heuristic.",
    )
    step2_hte_badge = CopyPair(
        signal="Can analyze who benefits most",
        spectrum="HTE eligible (CausalForestDML)",
    )

    # Step 3 — Configure
    step3_variant_eyebrow = CopyPair(
        signal="Comparison",
        spectrum="Variant assignment",
    )
    step3_group_col_label = CopyPair(
        signal="Group column",
        spectrum="Assignment column",
    )
    step3_metrics_eyebrow = CopyPair(
        signal="What to measure",
        spectrum="Metrics",
    )
    step3_outcome_label = CopyPair(
        signal="What outcome are you measuring?",
        spectrum="Continuous metrics to evaluate",
    )
    step3_outcome_help = CopyPair(
        signal="Pick the numbers you want to compare between the groups — e.g. revenue, sessions, time on page.",
        spectrum="Per-unit numeric outcomes. We'll compare averages between groups.",
    )
    step3_advanced_label = CopyPair(
        signal="Advanced settings",
        spectrum="Advanced parameters",
    )
    step3_run = CopyPair(
        signal="Run analysis →",
        spectrum="Run analysis →",
    )
    step3_why_settings = CopyPair(
        signal="Why are these fields pre-filled?",
        spectrum="Inferred configuration",
    )
    step3_hte_toggle = CopyPair(
        signal="Analyze who benefits most",
        spectrum="Enable HTE estimation",
    )
    step3_hte_help = CopyPair(
        signal="Find which groups respond differently to the treatment. Takes a bit longer.",
        spectrum="Fits CausalForestDML alongside LinearDML for individual-level CATE estimates.",
    )
    step3_hte_features_label = CopyPair(
        signal="Which factors might cause different responses?",
        spectrum="Effect modifier features (X)",
    )
    step3_hte_features_help = CopyPair(
        signal="Pick the characteristics that might make people respond differently — like age, income, or location.",
        spectrum="CATE conditioning features. Defaults to same as confounders (W=X).",
    )

    # Step 4 — Run
    step4_title = CopyPair(
        signal="Analyzing your experiment...",
        spectrum="Running analysis...",
    )
    step4_progress_srm = CopyPair(
        signal="Checking that the groups split the way you intended...",
        spectrum="Running SRM check...",
    )
    step4_progress_fit = CopyPair(
        signal="Measuring the effect of the change...",
        spectrum="Fitting statistical model...",
    )
    step4_progress_narrate = CopyPair(
        signal="Writing up the findings...",
        spectrum="Generating prescription...",
    )
    step4_progress_viz = CopyPair(
        signal="Preparing charts...",
        spectrum="Rendering diagnostics...",
    )
    step4_progress_hte = CopyPair(
        signal="Finding which groups respond differently...",
        spectrum="Fitting CausalForestDML for heterogeneous effects...",
    )
    step4_progress_bandit = CopyPair(
        signal="Comparing against dynamic allocation...",
        spectrum="Running Thompson Sampling replay simulation...",
    )

    # Step 5 — Prescription
    step5_srm_pass = CopyPair(
        signal="Groups split as expected",
        spectrum="SRM passed",
    )
    step5_srm_fail = CopyPair(
        signal="Groups aren't split the way they should be",
        spectrum="SRM detected",
    )
    step5_forest_title = CopyPair(
        signal="How much each metric changed",
        spectrum="Lift & 95% confidence intervals",
    )
    step5_metrics_title = CopyPair(
        signal="Results per metric",
        spectrum="Per-metric breakdown",
    )
    step5_lift_label = CopyPair(
        signal="How much it changed",
        spectrum="Relative lift",
    )
    step5_pvalue_label = CopyPair(
        signal="Certainty",
        spectrum="p-value",
    )
    step5_sig_yes = CopyPair(
        signal="Real difference detected",
        spectrum="Statistically significant",
    )
    step5_sig_no = CopyPair(
        signal="Could be random noise",
        spectrum="Not significant",
    )
    step5_forest_explanation = CopyPair(
        signal=(
            "Each dot shows how much the change moved a metric. "
            "Dots to the right mean improvement; dots to the left mean it got worse. "
            "The horizontal bar is our uncertainty — a shorter bar means we're more precise. "
            "Orange diamonds are statistically meaningful results; open circles are inconclusive."
        ),
        spectrum=(
            "Forest plot of relative lift with asymmetric 95% Wald CIs per metric (BH-adjusted). "
            "Orange diamonds = significant (p_adj < α); open circles = non-significant. "
            "X-axis: relative lift when |control_mean| > 0, absolute lift otherwise."
        ),
    )
    verdict_ship = CopyPair(signal="Ship it.", spectrum="Ship — significant positive effect.")
    verdict_hold = CopyPair(signal="Hold.", spectrum="Hold — inconclusive or caveated.")
    verdict_no_ship = CopyPair(signal="Don't ship.", spectrum="Reject — significant adverse effect.")

    # Step 5 — HTE section
    step5_hte_title = CopyPair(
        signal="Who benefits most?",
        spectrum="Heterogeneous Treatment Effects",
    )
    step5_hte_intro = CopyPair(
        signal="Not everyone responds the same way. This section shows which groups benefited more or less than average.",
        spectrum="CATE estimates from CausalForestDML reveal effect heterogeneity across observed covariates.",
    )
    step5_hte_importance_title = CopyPair(
        signal="What drives the difference",
        spectrum="Feature importance for heterogeneity",
    )
    step5_hte_importance_caption = CopyPair(
        signal=(
            "Taller bars mean that characteristic matters more for determining who benefits. "
            "The top variable explains the most variation in how people responded to the treatment."
        ),
        spectrum=(
            "Feature importance from the causal forest, measuring each covariate's contribution "
            "to CATE heterogeneity. Normalized to sum to 1."
        ),
    )
    step5_hte_histogram_title = CopyPair(
        signal="How the effect varies across individuals",
        spectrum="CATE distribution",
    )
    step5_hte_histogram_caption = CopyPair(
        signal=(
            "Each bar represents a group of people with a similar treatment effect. "
            "The orange dotted line is the average effect. "
            "People to the right of zero benefited; people to the left were harmed."
        ),
        spectrum=(
            "Distribution of individual-level CATE estimates. "
            "Orange dotted line = ATE. Red dashed line = zero (no effect). "
            "Spread indicates degree of effect heterogeneity."
        ),
    )
    step5_hte_subgroup_title = CopyPair(
        signal="Effect by group",
        spectrum="Subgroup CATE estimates",
    )
    step5_hte_subgroup_caption = CopyPair(
        signal=(
            "This table splits your data into groups and shows how much each group benefited. "
            "Arrows mark groups that benefited notably more or less than average."
        ),
        spectrum=(
            "Quartile-based CATE decomposition per feature. "
            "CIs are averaged within each segment. Arrows flag segments "
            "deviating >10% from the population ATE."
        ),
    )

    # Step 5 — MAB Regret Simulator
    step5_bandit_title = CopyPair(
        signal="Could smarter traffic allocation have saved time?",
        spectrum="Opportunity Cost Analysis (Thompson Sampling Replay)",
    )
    step5_bandit_intro = CopyPair(
        signal=(
            "In your test, you split traffic equally — 50% to each option — for the "
            "entire duration. An alternative approach called <em>dynamic allocation</em> "
            "gradually sends more traffic to the option that's performing better, "
            "so you waste less time on a losing option. Here's what that would have "
            "looked like with your data."
        ),
        spectrum=(
            "Standard A/B tests use fixed allocation (typically 50/50). Thompson Sampling "
            "adaptively reallocates traffic based on accumulating posterior evidence, "
            "reducing cumulative regret. Below: a replay simulation using your observed data."
        ),
    )
    step5_bandit_reward_title = CopyPair(
        signal="Cumulative results over time",
        spectrum="Cumulative reward: AB vs Thompson Sampling",
    )
    step5_bandit_reward_caption = CopyPair(
        signal=(
            "The gap between the lines shows how much faster a smart allocation "
            "captures value. The dashed green line is the theoretical best "
            "(all traffic to the winner)."
        ),
        spectrum=(
            "Cumulative reward under fixed (50/50) vs adaptive (TS) allocation. "
            "Oracle = all traffic to ex-post winner."
        ),
    )
    step5_bandit_alloc_title = CopyPair(
        signal="How traffic would have shifted",
        spectrum="Allocation trajectory to winning arm",
    )
    step5_bandit_alloc_caption = CopyPair(
        signal=(
            "A dynamic system starts at 50/50 and gradually sends more users to the "
            "winner as evidence builds. The dashed line shows the equal split your test used."
        ),
        spectrum=(
            "Thompson Sampling allocation fraction. "
            "Dashed line = 50% (fixed AB baseline). Convergence defined at ≥75%."
        ),
    )
    step5_bandit_duration_label = CopyPair(
        signal="Test duration",
        spectrum="Periods",
    )
    step5_bandit_duration_help = CopyPair(
        signal="How long the test ran",
        spectrum="",
    )
    step5_bandit_saved_label = CopyPair(
        signal="Exploration cost recovered",
        spectrum="Regret reduction",
    )
    step5_bandit_saved_help = CopyPair(
        signal="How much of the wasted traffic a smarter system would have recovered",
        spectrum="",
    )
    step5_bandit_convergence_label = CopyPair(
        signal="Would converge by",
        spectrum="Convergence (≥75%)",
    )
    step5_bandit_convergence_help = CopyPair(
        signal="When the system would start sending most traffic to the winner",
        spectrum="",
    )


copy = _Copy()


# ─────────────────────── Glossary ───────────────────────
@dataclass(frozen=True)
class GlossaryEntry:
    term: str
    short: str       # one-liner for the tooltip
    description: str # 2-4 sentences for the drawer / "Learn more"
    signal_synonym: str = ""   # signal-language alias shown in signal mode
    learn_more: str = ""      # citation / URL for deep dives
    first_use: str = ""       # inline hint shown the first time the term appears on a step


GLOSSARY: dict[str, GlossaryEntry] = {
    # ── Core statistical concepts ──
    "p_value": GlossaryEntry(
        term="p-value",
        signal_synonym="how likely the result is just random noise",
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
        signal_synonym="how much false-positive risk we accept",
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
        signal_synonym="the plausible range for the true effect",
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
        signal_synonym="the result is unlikely to be just noise",
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
        signal_synonym="whether the effect is big enough to matter",
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
        signal_synonym="how big the difference is, in units of noise",
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
        signal_synonym="the column that says which group each row belongs to",
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
        signal_synonym="the group that got the change",
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
        signal_synonym="the group that did NOT get the change",
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
        signal_synonym="the number you're trying to move",
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
        signal_synonym="a metric that's one number divided by another",
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
        signal_synonym="how much the number changed",
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
        signal_synonym="the percentage change",
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
        signal_synonym="the groups aren't sized the way they should be",
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
        signal_synonym="whether the groups are similar before the change",
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
        signal_synonym="the right way to compare ratios",
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
        signal_synonym="adjusting for testing many things at once",
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
        signal_synonym="two ways to read the evidence",
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
        signal_synonym="the probability the treatment is better",
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
        signal_synonym="the most likely range for the true effect (Bayesian)",
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
        signal_synonym="the range of effects too small to care about",
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
        signal_synonym="a factor that affects both the treatment and the outcome",
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
        signal_synonym="randomly assigning units to groups",
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
        signal_synonym="what would have happened without the change",
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
        signal_synonym="before and after the change",
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
        signal_synonym="the date the change went live",
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
        signal_synonym="using pre-experiment data to reduce noise",
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
        signal_synonym="whether the test can detect an effect this small",
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
    signal: str              # 1-2 sentence "what is this for" in business language
    spectrum: str           # same, in statistical language
    assumptions_signal: str   # what the method needs to be valid, business language
    assumptions_spectrum: str  # same, statistical language


METHOD_BLURBS: dict[str, MethodBlurb] = {
    "A/B Test": MethodBlurb(
        display_name="A/B Test",
        signal=(
            "Compares outcomes between two groups — the ones who got the change and the "
            "ones who didn't. Best when you randomly assigned units to each group."
        ),
        spectrum=(
            "Two groups, randomised. We compare averages with Welch's t-test "
            "(robust to unequal variances) and apply the Delta Method for ratio "
            "metrics so confidence intervals stay valid."
        ),
        assumptions_signal=(
            "Assumes the assignment to groups was random or random-like. "
            "If it wasn't, consider Causal Inference instead."
        ),
        assumptions_spectrum=(
            "Requires randomised assignment (SUTVA, no interference). "
            "Welch's t-test is robust to unequal variances. "
            "Ratio metrics get Delta-method SEs."
        ),
    ),
    "Time-Series Intervention": MethodBlurb(
        display_name="Time-Series Intervention",
        signal=(
            "Measures the impact of a change by comparing what happened after the "
            "change date to what would have happened without it. Best when you "
            "rolled something out to everyone on a specific date."
        ),
        spectrum=(
            "A single series with a known intervention date. We fit a counterfactual "
            "to the pre-period, then compare it against the observed post-period."
        ),
        assumptions_signal=(
            "Assumes nothing else changed on or around the intervention date that could "
            "also affect the metric. If another campaign launched the same week, the "
            "estimate may be confounded."
        ),
        assumptions_spectrum=(
            "Assumes stable pre-period dynamics, no concurrent confounding interventions, "
            "and sufficient pre-period data for counterfactual estimation."
        ),
    ),
    "Causal Inference": MethodBlurb(
        display_name="Observational Causal Inference",
        signal=(
            "Estimates the effect of a change even when you didn't randomly assign who got it. "
            "Uses other measured factors (like demographics or prior behaviour) to adjust for "
            "differences between the groups."
        ),
        spectrum=(
            "No randomisation, but treatment, outcome, and plausible confounders are all "
            "observed. We use DoWhy to identify a valid estimand and EconML's Double "
            "Machine Learning to estimate it."
        ),
        assumptions_signal=(
            "Assumes you've included every important factor that affects both who got the "
            "treatment and the outcome. If there's a hidden factor you haven't measured, "
            "the result may be wrong."
        ),
        assumptions_spectrum=(
            "Requires conditional ignorability (no unmeasured confounders). "
            "DML uses cross-fitting for doubly-robust estimation. "
            "Sensitive to model specification if overlap is poor."
        ),
    ),
    "Exploratory": MethodBlurb(
        display_name="Exploratory mode",
        signal=(
            "We can't identify a clear experiment structure in this data. We'll surface "
            "distributions and patterns to help you understand the dataset before "
            "designing a test."
        ),
        spectrum=(
            "We can't infer a clear experimental structure. Surface distributions "
            "and correlations to understand the data before designing a test."
        ),
        assumptions_signal="No statistical assumptions — this is descriptive, not inferential.",
        assumptions_spectrum="Descriptive only. No causal or inferential claims.",
    ),
}
