"""Step 5 — Prescription.

Phase C: the deliverable.

Layout (redesigned for full-width use):
  Thin top bar: method label + SRM badge (single flex row)
  Hero two-column [3, 2]:
    Left:  VerdictBanner + PrescriptionCard (narrative, caveats, next steps)
    Right: Primary metric big-number card + confidence bar + stacked export buttons
  Full-width section:
    Forest plot + voice-aware explanation caption
    Per-metric detail rows with progressive disclosure
  Method-specific extra visuals in an expander (each with caption)
  Reproducibility section in an expander
  Footer nav: ← Back | Run again | Start over
"""

from __future__ import annotations

import streamlit as st

from tao_lab.interpret.narrator import PrescriptionNarration
from tao_lab.methods.base import AnalysisResult
from tao_lab.ui import state as wstate
from tao_lab.ui.components.exports import to_markdown, to_pdf_bytes, to_yaml_config
from tao_lab.ui.components.forest_plot import render_forest_plot
from tao_lab.ui.components.metric_detail import render_metric_details
from tao_lab.ui.components.prescription_card import render_prescription
from tao_lab.ui.components.verdict_banner import render_verdict
from tao_lab.ui.strings import CopyPair, copy


_CONFIDENCE_LABEL = {
    "strong": "Strong evidence",
    "moderate": "Moderate evidence",
    "weak": "Weak evidence",
    "none": "No evidence",
}

_VERDICT_COLOR = {
    "ship": "#059669",
    "hold": "#D97706",
    "dont_ship": "#DC2626",
}

# ── Method-specific plot explanations ──────────────────────────────────────────
_PLOT_EXPLANATIONS: dict[str, CopyPair] = {
    "Bayesian A/B Test": CopyPair(
        plain=(
            "This curve shows all the values the true effect could plausibly take. "
            "The shaded region is where we're 95% confident the real answer lies. "
            "More area to the right of zero means more confidence the treatment is better."
        ),
        technical=(
            "Posterior distribution of relative lift (MCMC, NumPyro). "
            "Shaded region = 95% Highest Density Interval (HDI). "
            "Area right of x=0 = P(lift > 0) — the probability the treatment strictly dominates."
        ),
    ),
    "Causal Inference": CopyPair(
        plain=(
            "This chart checks whether people who received the treatment were similar enough "
            "to those who didn't. Good overlap between the two groups means we can trust the causal estimate."
        ),
        technical=(
            "Propensity score overlap plot (positivity check). "
            "Distributional overlap between treated/control validates the positivity assumption "
            "required for causal identification. Thin tails or no overlap = estimates unreliable."
        ),
    ),
}

_DEFAULT_PLOT_EXPLANATION = CopyPair(
    plain="This chart shows method-specific diagnostic information.",
    technical="Method diagnostic plot.",
)


def _plot_explanation(method_name: str, voice: str) -> str:
    pair = _PLOT_EXPLANATIONS.get(method_name, _DEFAULT_PLOT_EXPLANATION)
    return pair(voice)


# ──────────────────────────────────────────────────────────────────────────────
def render() -> None:
    s = wstate.get_state()
    if s.result is None or s.prescription is None:
        st.info("No analysis result yet.")
        return

    voice = s.voice
    result = s.result
    p = s.prescription

    # ── Thin top bar: method label + SRM badge ──
    _render_action_bar(s)

    # ── Hero: two-column layout ──
    hero_left, hero_right = st.columns([3, 2], gap="large")

    with hero_left:
        headline = p.headline.plain if voice == "plain" else p.headline.technical
        subtitle = (
            f"{_CONFIDENCE_LABEL[p.confidence]} · "
            f"{int(p.confidence_score * 100)}/100 confidence"
        )
        render_verdict(state=p.verdict, headline=headline, subtitle=subtitle, key="verdict_main")
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        render_prescription(p, voice=voice, key="prescription_main")

    with hero_right:
        _render_key_numbers_card(result, p, voice)
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        _render_export_rail(s)

    st.markdown("<hr class='tl-divider'>", unsafe_allow_html=True)

    # ── Forest plot (full width) ──
    if result.metrics:
        st.markdown(
            f"<div class='tl-text-deep' style='font-weight:500;margin:0 0 .5rem;'>"
            f"{copy.step5_forest_title(voice)}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(render_forest_plot(result), width="stretch")
        st.caption(copy.step5_forest_explanation(voice))

    # ── Per-metric detail rows ──
    st.markdown(
        f"<div class='tl-text-deep' style='font-weight:500;margin:1rem 0 .5rem;'>"
        f"{copy.step5_metrics_title(voice)}"
        f"</div>",
        unsafe_allow_html=True,
    )
    render_metric_details(result, voice=voice)

    # ── Method-specific extra visuals ──
    if s.method_visuals:
        with st.expander("Method-specific diagnostics", expanded=False):
            for fig in s.method_visuals:
                st.plotly_chart(fig, width="stretch")
                st.caption(_plot_explanation(result.method_name, voice))

    # ── Reproducibility ──
    with st.expander("Reproducibility config", expanded=False):
        st.code(to_yaml_config(result), language="yaml")

    st.markdown("<hr class='tl-divider'>", unsafe_allow_html=True)

    # ── Footer nav ──
    nav_a, nav_b, nav_c = st.columns([1, 1, 2])
    with nav_a:
        if st.button("← Back", key="rx_back", use_container_width=True):
            wstate.go_back()
    with nav_b:
        if st.button("Run again", key="rx_run_again", use_container_width=True):
            s.result = None
            s.prescription = None
            s.narration = None
            s.method_visuals = []
            wstate.goto(wstate.STEP_CONFIGURE)
    with nav_c:
        if st.button("Start over", key="rx_start_over", use_container_width=True):
            wstate.reset_state()
            st.rerun()


# ─────────────────────────── Slim action bar ───────────────────────────
def _render_action_bar(s: wstate.WizardState) -> None:
    """Single flex row: method name + SRM badge. No column layout, no buttons."""
    result = s.result
    badge_color = "var(--tl-danger)" if result.srm_detected else "var(--tl-success)"
    if s.voice == "plain":
        badge_text = (
            f"⚠ {copy.step5_srm_fail('plain')}"
            if result.srm_detected
            else f"✓ {copy.step5_srm_pass('plain')}"
        )
    else:
        badge_text = (
            f"⚠ SRM detected · p = {result.srm_p_value:.4g}"
            if result.srm_detected
            else f"✓ SRM passed · p = {result.srm_p_value:.4g}"
        )
    st.markdown(
        f"""<div style="display:flex;gap:.75rem;align-items:center;
                        margin-bottom:1rem;flex-wrap:wrap;">
          <span style="font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;
                       color:var(--tl-slate);font-weight:600;">{result.method_name}</span>
          <span style="color:{badge_color};font-size:.85rem;font-weight:500;">{badge_text}</span>
        </div>""",
        unsafe_allow_html=True,
    )


# ─────────────────────────── Primary metric card ───────────────────────────
def _render_key_numbers_card(
    result: AnalysisResult,
    prescription: PrescriptionNarration,
    voice: str,
) -> None:
    """Big-number card: primary metric lift + confidence bar."""
    primary = next(
        (m for m in result.metrics if m.is_significant),
        result.metrics[0] if result.metrics else None,
    )
    if not primary:
        return

    direction = "▲" if primary.lift_relative >= 0 else "▼"
    lift_color = "#059669" if primary.lift_relative >= 0 else "#DC2626"
    verdict_color = _VERDICT_COLOR[prescription.verdict]
    confidence_label = _CONFIDENCE_LABEL[prescription.confidence]
    confidence_score = prescription.confidence_score

    metric_label = primary.metric_name.replace("_", " ").title()

    # Treat/control subtitle: avoid scientific notation for very small or very large numbers
    try:
        treat_str = f"{primary.treatment_mean:.4g}"
        ctrl_str = f"{primary.control_mean:.4g}"
    except Exception:
        treat_str = str(primary.treatment_mean)
        ctrl_str = str(primary.control_mean)

    st.markdown(
        f"""<div class="tl-card" style="padding:1.25rem 1.5rem;text-align:center;margin-bottom:.5rem;">
          <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;
                      color:var(--tl-tangerine);font-weight:600;margin-bottom:.5rem;">
            {metric_label}
          </div>
          <div style="font-size:2.4rem;font-weight:700;color:{lift_color};line-height:1.1;">
            {direction} {abs(primary.lift_relative * 100):.1f}%
          </div>
          <div style="font-size:.82rem;color:var(--tl-slate);margin-top:.35rem;">
            {treat_str} vs {ctrl_str}
          </div>
          <div style="height:4px;background:#E2E8F0;border-radius:2px;margin-top:.9rem;">
            <div style="height:4px;width:{confidence_score * 100:.0f}%;
                        background:{verdict_color};border-radius:2px;transition:width .4s;"></div>
          </div>
          <div style="font-size:.75rem;color:var(--tl-slate);margin-top:.3rem;">
            {confidence_label} · {int(confidence_score * 100)}/100 confidence
          </div>
        </div>""",
        unsafe_allow_html=True,
    )


# ─────────────────────────── Export rail ───────────────────────────
def _render_export_rail(s: wstate.WizardState) -> None:
    """Stacked export download buttons in the right rail."""
    bq = s.business_question or ""
    md = to_markdown(s.result, s.prescription, voice=s.voice, business_question=bq)

    st.download_button(
        "↓ Markdown report",
        data=md,
        file_name="tao_lab_prescription.md",
        mime="text/markdown",
        use_container_width=True,
        key="exp_md_rail",
    )

    pdf_bytes = to_pdf_bytes(s.result, s.prescription, voice=s.voice, business_question=bq)
    if pdf_bytes is not None:
        st.download_button(
            "↓ PDF report",
            data=pdf_bytes,
            file_name="tao_lab_prescription.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="exp_pdf_rail",
        )
    else:
        st.button(
            "↓ PDF (install WeasyPrint)",
            disabled=True,
            use_container_width=True,
            help="PDF export needs WeasyPrint. Install with `uv pip install 'tao-lab[report]'`.",
            key="exp_pdf_disabled_rail",
        )

    st.download_button(
        "↓ YAML config",
        data=to_yaml_config(s.result),
        file_name="tao_lab_config.yaml",
        mime="text/yaml",
        use_container_width=True,
        key="exp_yaml_rail",
    )
