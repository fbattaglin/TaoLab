"""Structured narrator for the Prescription step.

Produces a `PrescriptionNarration` — the canonical artefact the UI renders.
Two registers (`plain`, `technical`) are produced for every text field so
the user-facing voice toggle never re-runs the analysis.

Strategy:

* **Template-first.** Even without an LLM API key we ship a respectable,
  deterministic narration. This keeps the offline / air-gapped path strong
  and means the UX never depends on Anthropic availability.
* **LLM enhancement (optional).** When `ANTHROPIC_API_KEY` is set, we let
  Claude rewrite the `diagnosis` and `recommendation` fields with richer
  business framing — but only those two. Verdict, confidence, caveats, and
  next-steps remain rule-driven so they cannot drift away from the data.

The legacy `Narrator.narrate_results(result) -> str` API is preserved as a
thin wrapper that materialises the structured narration into Markdown.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from tao_lab.methods.base import AnalysisResult, MetricResult


Verdict = Literal["ship", "hold", "dont_ship"]
Confidence = Literal["strong", "moderate", "weak", "none"]
Severity = Literal["info", "warning", "critical"]


# ─────────────────────────── Models ───────────────────────────
class CaveatItem(BaseModel):
    severity: Severity
    title: str
    body_plain: str
    body_technical: str


class TextPair(BaseModel):
    plain: str
    technical: str


class PrescriptionNarration(BaseModel):
    """The deliverable. Step 5 renders this directly."""

    verdict: Verdict
    confidence: Confidence
    confidence_score: float = Field(ge=0.0, le=1.0)
    headline: TextPair
    diagnosis: TextPair
    recommendation: TextPair
    reasoning: TextPair
    caveats: List[CaveatItem] = Field(default_factory=list)
    next_steps_plain: List[str] = Field(default_factory=list)
    next_steps_technical: List[str] = Field(default_factory=list)


# ─────────────────────────── Public API ───────────────────────────
class Narrator:
    """The legacy entrypoint. Kept for back-compat with v1 callers."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def narrate_results(self, result: AnalysisResult) -> str:
        """Return the Markdown rendering of the structured narration.

        Phase C still publishes a string for the legacy code paths; new code
        should call `build_prescription(result)` directly.
        """
        prescription = build_prescription(result, api_key=self.api_key)
        return render_markdown(prescription, voice="plain")


def build_prescription(
    result: AnalysisResult, *, api_key: Optional[str] = None
) -> PrescriptionNarration:
    """Single source of truth for the prescription content."""
    base = _template_prescription(result)
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _enrich_with_llm(base, result, api_key=api_key)
        except Exception:  # noqa: BLE001
            # We never fail the analysis because the LLM is flaky.
            return base
    return base


# ─────────────────────────── Template-based core ───────────────────────────
@dataclass
class _PrimaryReadout:
    """The 'lead' metric we anchor the verdict on. Heuristic: first metric in
    the user's metric_cols (or first in result.metrics if none)."""

    metric: MetricResult
    direction: Literal["up", "down", "flat"]


def _template_prescription(result: AnalysisResult) -> PrescriptionNarration:
    primary = _pick_primary_metric(result)
    verdict = _decide_verdict(result, primary)
    confidence, confidence_score = _decide_confidence(primary)

    headline = _build_headline(primary, result)
    diagnosis = _build_diagnosis(result, primary)
    recommendation = _build_recommendation(verdict, primary, result)
    reasoning = _build_reasoning(primary, result)
    caveats = _build_caveats(result, primary)
    next_plain, next_tech = _build_next_steps(verdict, result, primary)

    return PrescriptionNarration(
        verdict=verdict,
        confidence=confidence,
        confidence_score=confidence_score,
        headline=headline,
        diagnosis=diagnosis,
        recommendation=recommendation,
        reasoning=reasoning,
        caveats=caveats,
        next_steps_plain=next_plain,
        next_steps_technical=next_tech,
    )


def _effective_p(m: MetricResult) -> Optional[float]:
    """Use the BH-adjusted p when available — that's what `is_significant` is
    based on — otherwise fall back to the raw p."""
    return m.p_value_adjusted if m.p_value_adjusted is not None else m.p_value


def _pick_primary_metric(result: AnalysisResult) -> Optional[_PrimaryReadout]:
    if not result.metrics:
        return None
    metric = result.metrics[0]
    if metric.lift_relative > 0.001:
        direction = "up"
    elif metric.lift_relative < -0.001:
        direction = "down"
    else:
        direction = "flat"
    return _PrimaryReadout(metric=metric, direction=direction)


def _decide_verdict(
    result: AnalysisResult, primary: Optional[_PrimaryReadout]
) -> Verdict:
    # SRM is a hard stop: nothing downstream is trustworthy.
    if result.srm_detected:
        return "hold"
    if primary is None:
        return "hold"
    m = primary.metric
    if not m.is_significant:
        return "hold"
    if primary.direction == "up":
        return "ship"
    if primary.direction == "down":
        return "dont_ship"
    return "hold"


def _decide_confidence(primary: Optional[_PrimaryReadout]) -> tuple[Confidence, float]:
    if primary is None or _effective_p(primary.metric) is None:
        return "none", 0.0
    p = _effective_p(primary.metric)
    # Map p to a 0..1 confidence for the visual bar (saturates at 1 near p=0).
    # 1 - p is too generous; we use a log scale: -log10(p)/3 capped at 1.
    import math
    if p <= 0:
        score = 1.0
    else:
        score = max(0.0, min(1.0, -math.log10(p) / 3.0))
    if p < 0.001:
        return "strong", score
    if p < 0.01:
        return "moderate", score
    if p < 0.05:
        return "weak", score
    return "none", score


# ─────────────────────────── Text builders ───────────────────────────
def _fmt_pct(x: float) -> str:
    return f"{x * 100:+.2f}%"


def _build_headline(
    primary: Optional[_PrimaryReadout], result: AnalysisResult
) -> TextPair:
    if primary is None:
        return TextPair(
            plain="No metric was returned. Re-check your configuration.",
            technical="result.metrics is empty.",
        )
    m = primary.metric
    sign = primary.direction

    # ── Plain: business language, absolute numbers, no jargon ──
    direction_plain = {"up": "more", "down": "less", "flat": "about the same"}[sign]
    if sign == "flat":
        plain = (
            f"The groups performed about the same on {m.metric_name} "
            f"(treatment: {m.treatment_mean:.4g}, control: {m.control_mean:.4g})."
        )
    else:
        plain = (
            f"The treatment group had {abs(m.lift_absolute):.4g} {direction_plain} "
            f"{m.metric_name} on average ({m.treatment_mean:.4g} vs {m.control_mean:.4g}, "
            f"{_fmt_pct(m.lift_relative)})."
        )

    # ── Technical: unchanged precision, full statistical shorthand ──
    p_eff = _effective_p(m)
    if p_eff is None:
        direction_word = {"up": "increased", "down": "decreased", "flat": "did not move"}[sign]
        tech = (
            f"Treatment {direction_word} {m.metric_name} by {_fmt_pct(m.lift_relative)}."
        )
    else:
        p_label = "p (adj)" if m.p_value_adjusted is not None else "p"
        tech_extra = ""
        if m.test_statistic is not None:
            tech_extra += f", stat = {m.test_statistic:.3g}"
        if m.effect_size is not None and m.effect_size != 0:
            tech_extra += f", Cohen's d = {m.effect_size:.3g}"
        tech = (
            f"Treatment Δ {m.metric_name} = {m.lift_absolute:.4g} "
            f"({_fmt_pct(m.lift_relative)}); 95% CI [{m.ci_lower:.3g}, {m.ci_upper:.3g}]; "
            f"{p_label} = {p_eff:.4g}{tech_extra}."
        )
    return TextPair(plain=plain, technical=tech)


def _build_diagnosis(
    result: AnalysisResult, primary: Optional[_PrimaryReadout]
) -> TextPair:
    n_metrics = len(result.metrics)
    method = result.method_name
    sig_count = sum(1 for m in result.metrics if m.is_significant)

    # ── Plain: lead with the finding, then context ──
    plain_parts = []
    if primary is not None:
        m = primary.metric
        if m.is_significant and primary.direction == "up":
            plain_parts.append(
                f"The data shows a real difference on {m.metric_name} — "
                f"the group that got the change performed measurably better."
            )
        elif m.is_significant and primary.direction == "down":
            plain_parts.append(
                f"The data shows a real difference on {m.metric_name} — "
                f"the group that got the change performed measurably worse."
            )
        else:
            plain_parts.append(
                f"The data doesn't show a clear difference on {m.metric_name}. "
                f"The observed gap could easily be due to normal variation."
            )

    if n_metrics > 1:
        if sig_count == 0:
            plain_parts.append(
                f"None of the {n_metrics} metrics showed a clear difference."
            )
        elif sig_count == n_metrics:
            plain_parts.append(
                f"All {n_metrics} metrics showed a real difference."
            )
        else:
            plain_parts.append(
                f"Of {n_metrics} metrics tested, {sig_count} showed a real difference "
                f"(after adjusting for multiple comparisons)."
            )
    if result.srm_detected:
        plain_parts.append(
            "However, the groups aren't sized the way they should be — that usually "
            "points to an assignment or logging bug and undermines every result below."
        )

    plain = " ".join(plain_parts) or "No diagnosis available."

    # ── Technical: unchanged ──
    tech_parts = [f"Method: {method}.", f"n_metrics = {n_metrics}, sig = {sig_count}."]
    if primary is not None and primary.metric.p_value is not None:
        m = primary.metric
        tech_parts.append(
            f"Primary metric '{m.metric_name}': lift_abs = {m.lift_absolute:.4g}, "
            f"lift_rel = {m.lift_relative:.4g}, p = {m.p_value:.4g}, "
            f"CI = [{m.ci_lower:.4g}, {m.ci_upper:.4g}]."
        )
    if result.srm_detected:
        tech_parts.append(
            f"SRM χ² test rejected at p = {result.srm_p_value:.4g} (< 0.001)."
        )
    tech = " ".join(tech_parts)

    return TextPair(plain=plain, technical=tech)


def _build_recommendation(
    verdict: Verdict,
    primary: Optional[_PrimaryReadout],
    result: AnalysisResult,
) -> TextPair:
    if result.srm_detected:
        return TextPair(
            plain=(
                "Don't act on these results yet. First, find and fix the cause of the "
                "group imbalance — a randomisation, filtering, or logging issue is the "
                "most common culprit."
            ),
            technical=(
                "Halt action. SRM detected; downstream estimates are biased. "
                "Audit the assignment pipeline (split logic, filters, deduplication) "
                "before re-running."
            ),
        )
    if verdict == "ship":
        m = primary.metric  # safe by construction
        return TextPair(
            plain=(
                f"Ship the treatment. The lift on {m.metric_name} is large enough and "
                "consistent enough to justify rolling out, ideally with a small holdout "
                "to keep monitoring the impact."
            ),
            technical=(
                f"Roll out treatment. {m.metric_name} shows lift_rel = "
                f"{m.lift_relative:.3%} significant at α = {result.config_snapshot.alpha}. "
                "Recommend a 5–10% holdout for ongoing monitoring."
            ),
        )
    if verdict == "dont_ship":
        m = primary.metric
        return TextPair(
            plain=(
                f"Don't ship. The treatment is dragging {m.metric_name} down "
                "by a real, measurable amount. Roll back and investigate which "
                "behaviour change caused the regression."
            ),
            technical=(
                f"Reject treatment. {m.metric_name} regression of "
                f"{m.lift_relative:.3%} significant at α = {result.config_snapshot.alpha}. "
                "Roll back; instrument additional segments to localise the regression."
            ),
        )
    return TextPair(
        plain=(
            "Hold. The data don't yet say the treatment works (or doesn't). Either "
            "let the experiment accumulate more sample, or design a follow-up that "
            "targets the segment where you expect the effect to be largest."
        ),
        technical=(
            "Inconclusive at α = "
            f"{result.config_snapshot.alpha}. Options: extend runtime to grow power, "
            "add covariate adjustment (CUPED), or restrict to the pre-specified "
            "primary segment."
        ),
    )


def _build_reasoning(
    primary: Optional[_PrimaryReadout], result: AnalysisResult
) -> TextPair:
    if primary is None:
        return TextPair(plain="—", technical="—")
    m = primary.metric
    p_for_text = m.p_value if m.p_value is not None else 1.0

    # ── Plain: three-line decision template ──
    # Line 1: What happened (business terms, absolute numbers)
    direction_word = {"up": "more", "down": "less", "flat": "about the same amount of"}[
        primary.direction
    ]
    line1 = (
        f"On {m.metric_name}, the group that got the change averaged "
        f"{m.treatment_mean:.4g} vs {m.control_mean:.4g} in the baseline group — "
        f"{abs(m.lift_absolute):.4g} {direction_word} ({_fmt_pct(m.lift_relative)})."
    )

    # Line 2: How sure we are (confidence language, anchored to CI)
    confidence_word = _confidence_word(p_for_text)
    line2 = (
        f"We're {confidence_word} the real effect is between "
        f"{m.ci_lower:.3g} and {m.ci_upper:.3g} (95% confidence interval)."
    )

    # Line 3: Decision relevance
    if m.is_significant and primary.direction == "up":
        line3 = "This is large enough and consistent enough to act on."
    elif m.is_significant and primary.direction == "down":
        line3 = "This is a clear negative signal — investigate what's driving the regression."
    else:
        line3 = (
            "The difference isn't large enough relative to noise to be confident it's real. "
            "More data or a different approach may be needed."
        )

    plain = f"{line1} {line2} {line3}"

    # ── Technical: unchanged ──
    tech_extras = []
    if m.test_statistic is not None:
        tech_extras.append(f"test stat = {m.test_statistic:.4g}")
    if m.effect_size is not None and m.effect_size != 0:
        tech_extras.append(f"Cohen's d = {m.effect_size:.4g}")
    if m.p_value_adjusted is not None and m.p_value is not None and m.p_value_adjusted != m.p_value:
        tech_extras.append(f"p_adjusted (BH) = {m.p_value_adjusted:.4g}")
    if m.n_control is not None and m.n_treatment is not None:
        tech_extras.append(f"n = ({m.n_control}, {m.n_treatment})")
    extras = "; ".join(tech_extras)
    tech = (
        f"{m.metric_name}: μ_t = {m.treatment_mean:.4g}, μ_c = {m.control_mean:.4g}, "
        f"Δ = {m.lift_absolute:.4g} ({m.lift_relative:.4g}); "
        f"95% CI [{m.ci_lower:.4g}, {m.ci_upper:.4g}]; p = {p_for_text:.4g}"
    )
    if extras:
        tech += f"; {extras}"
    tech += "."
    return TextPair(plain=plain, technical=tech)


def _confidence_word(p: float) -> str:
    """Map a p-value to a plain-language confidence descriptor."""
    if p < 0.001:
        return "very confident"
    if p < 0.01:
        return "quite confident"
    if p < 0.05:
        return "fairly confident"
    if p < 0.10:
        return "somewhat confident (though not at the standard threshold)"
    return "not confident"


def _build_caveats(
    result: AnalysisResult, primary: Optional[_PrimaryReadout]
) -> List[CaveatItem]:
    caveats: List[CaveatItem] = []

    if result.srm_detected:
        caveats.append(
            CaveatItem(
                severity="critical",
                title="Sample Ratio Mismatch detected",
                body_plain=(
                    "The control and treatment groups aren't the size you expected. "
                    "That's almost always a bug in randomisation, filtering, or logging "
                    "— and it makes every result below this banner suspect."
                ),
                body_technical=(
                    f"Chi-squared SRM test rejected at p = {result.srm_p_value:.4g}, "
                    "well below the conventional 0.001 threshold. Re-run only after "
                    "the assignment pipeline is audited and corrected."
                ),
            )
        )

    if len(result.metrics) > 1:
        caveats.append(
            CaveatItem(
                severity="info",
                title="Multiple metrics tested — corrected for false discovery",
                body_plain=(
                    "Each metric you test adds a small chance of a false positive. "
                    "We adjusted the p-values using the Benjamini-Hochberg procedure "
                    "so the results below already account for this."
                ),
                body_technical=(
                    f"BH/FDR correction applied across {len(result.metrics)} metrics "
                    f"at α = {result.config_snapshot.alpha}. Adjusted p-values surface "
                    "in the metric detail rows."
                ),
            )
        )

    if primary is not None:
        m = primary.metric
        if m.n_control is not None and m.n_treatment is not None:
            n_min = min(m.n_control, m.n_treatment)
            if n_min < 100:
                caveats.append(
                    CaveatItem(
                        severity="warning",
                        title="Small sample size",
                        body_plain=(
                            f"The smaller group has only {n_min} units. Estimates "
                            "with this little data tend to swing wildly between "
                            "experiments — treat the magnitude with caution."
                        ),
                        body_technical=(
                            f"min(n_c, n_t) = {n_min}. Power for typical effect sizes "
                            "(Cohen's d ≈ 0.2–0.3) is below 0.5; consider variance "
                            "reduction (CUPED) or a longer run."
                        ),
                    )
                )

        # Wide CI relative to lift indicates a noisy estimate even if significant.
        if m.lift_absolute and m.ci_lower is not None and m.ci_upper is not None:
            ci_width = m.ci_upper - m.ci_lower
            if ci_width > 0 and abs(m.lift_absolute) > 0:
                width_ratio = ci_width / abs(m.lift_absolute)
                if width_ratio > 1.5 and m.is_significant:
                    caveats.append(
                        CaveatItem(
                            severity="warning",
                            title="Confidence interval is wide",
                            body_plain=(
                                "The size of the effect could plausibly be quite "
                                "different from the central estimate — the data narrows "
                                "it down, but not tightly. Plan for a range of outcomes."
                            ),
                            body_technical=(
                                f"CI width / |lift_abs| ratio ≈ {width_ratio:.2f}. "
                                "Estimate is statistically distinct from zero but "
                                "magnitude is poorly identified."
                            ),
                        )
                    )

    return caveats


def _build_next_steps(
    verdict: Verdict,
    result: AnalysisResult,
    primary: Optional[_PrimaryReadout],
) -> tuple[List[str], List[str]]:
    if result.srm_detected:
        plain = [
            "Pause any rollout and audit the assignment pipeline (randomisation, filters, logging).",
            "Re-run the experiment only after the imbalance is fixed.",
        ]
        tech = [
            "Audit the assignment service and downstream filter steps for bias.",
            "Re-validate counts post-fix; require χ² p > 0.05 before re-analysing.",
        ]
        return plain, tech

    if verdict == "ship":
        plain = [
            "Plan a phased rollout, ideally retaining a 5–10% holdout to keep observing the effect.",
            "Set up an alert on the primary metric so any regression after rollout is caught early.",
        ]
        tech = [
            "Stage rollout with a 5–10% holdout for ongoing observation.",
            "Configure post-launch alerting on lift_rel and SRM for the rolled-out segment.",
        ]
        return plain, tech

    if verdict == "dont_ship":
        plain = [
            "Roll back the change and gather more telemetry on which segment drove the regression.",
            "Form a hypothesis about the failure mode before iterating on the next variant.",
        ]
        tech = [
            "Roll back; segment by user / region / device to localise the regression.",
            "Pre-register the next variant's hypothesis before re-testing.",
        ]
        return plain, tech

    # hold
    plain = [
        "Either let the experiment run longer to gain power, or scope it to the segment where you expect the largest effect.",
        "Consider variance reduction (CUPED) if pre-experiment data is available.",
    ]
    tech = [
        "Compute required sample size for the targeted MDE; extend runtime accordingly.",
        "Add CUPED with pre-period covariates to tighten CIs without extending runtime.",
    ]
    return plain, tech


# ─────────────────────────── LLM enhancement (optional) ───────────────────────────
def _enrich_with_llm(
    base: PrescriptionNarration,
    result: AnalysisResult,
    *,
    api_key: str,
) -> PrescriptionNarration:
    """Replace the diagnosis + recommendation text fields with LLM-rewritten
    versions in both registers. Verdict, confidence, caveats, next-steps are
    untouched — they're rule-driven and must not drift from the data."""
    import anthropic  # local import to keep the top-level cheap

    client = anthropic.Anthropic(api_key=api_key)

    facts = _facts_payload(base, result)

    prompt = f"""You are a Principal Data Scientist writing the diagnosis and recommendation \
sections of an experiment prescription. Rewrite the two sections below in **two registers**: \
plain (business-friendly, jargon-free, second person, 2–3 sentences) and technical \
(statistician-grade, terse, 1–2 sentences). Do not change the verdict or invent numbers.

Verdict: {base.verdict}
Facts:
{facts}

Existing diagnosis (plain): {base.diagnosis.plain}
Existing diagnosis (technical): {base.diagnosis.technical}
Existing recommendation (plain): {base.recommendation.plain}
Existing recommendation (technical): {base.recommendation.technical}

Reply with a JSON object exactly matching this schema, and nothing else:
{{
  "diagnosis_plain": "...",
  "diagnosis_technical": "...",
  "recommendation_plain": "...",
  "recommendation_technical": "..."
}}
"""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text if msg.content else "{}"

    import json

    try:
        # Strip code fences if the model added them.
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.rsplit("```", 1)[0].strip()
        data = json.loads(cleaned)
    except Exception:  # noqa: BLE001
        return base

    return base.model_copy(
        update={
            "diagnosis": TextPair(
                plain=data.get("diagnosis_plain", base.diagnosis.plain),
                technical=data.get("diagnosis_technical", base.diagnosis.technical),
            ),
            "recommendation": TextPair(
                plain=data.get("recommendation_plain", base.recommendation.plain),
                technical=data.get("recommendation_technical", base.recommendation.technical),
            ),
        }
    )


def _facts_payload(base: PrescriptionNarration, result: AnalysisResult) -> str:
    rows = [f"Method: {result.method_name}", f"SRM detected: {result.srm_detected}"]
    for m in result.metrics:
        rows.append(
            f"- {m.metric_name}: lift_rel = {m.lift_relative:.4g}, p = "
            f"{(m.p_value if m.p_value is not None else 'NA'):.4g}, "
            f"sig = {m.is_significant}"
        )
    return "\n".join(rows)


# ─────────────────────────── Markdown rendering ───────────────────────────
def render_markdown(p: PrescriptionNarration, *, voice: Literal["plain", "technical"] = "plain") -> str:
    label = {"ship": "Ship it.", "hold": "Hold.", "dont_ship": "Don't ship."}[p.verdict]
    headline = p.headline.plain if voice == "plain" else p.headline.technical
    diagnosis = p.diagnosis.plain if voice == "plain" else p.diagnosis.technical
    recommendation = p.recommendation.plain if voice == "plain" else p.recommendation.technical
    reasoning = p.reasoning.plain if voice == "plain" else p.reasoning.technical
    next_steps = p.next_steps_plain if voice == "plain" else p.next_steps_technical

    parts = [
        f"## Prescription — {label}",
        f"**{headline}**",
        "",
        f"**Confidence:** {p.confidence} ({int(p.confidence_score * 100)} / 100)",
        "",
        "### Diagnosis",
        diagnosis,
        "",
        "### Recommendation",
        recommendation,
        "",
        "### Reasoning",
        reasoning,
    ]

    if p.caveats:
        parts.extend(["", "### Caveats"])
        for c in p.caveats:
            body = c.body_plain if voice == "plain" else c.body_technical
            sev = {"info": "ℹ", "warning": "!", "critical": "✕"}.get(c.severity, "•")
            parts.append(f"- **{sev} {c.title}** — {body}")

    if next_steps:
        parts.extend(["", "### Next steps"])
        for ns in next_steps:
            parts.append(f"- {ns}")

    return "\n".join(parts)
