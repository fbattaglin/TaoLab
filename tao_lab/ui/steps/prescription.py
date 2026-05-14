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
        _render_decision_intelligence_card(result, p, voice)
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

    # ── MAB Regret Simulator section ──
    if s.bandit_replay is not None:
        st.markdown("<hr class='tl-divider'>", unsafe_allow_html=True)
        _render_bandit_section(s, p, voice)

    # ── HTE section (when available) ──
    if result.hte is not None:
        st.markdown("<hr class='tl-divider'>", unsafe_allow_html=True)
        _render_hte_section(result, p, voice)

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

def _render_decision_intelligence_card(result: AnalysisResult, prescription: PrescriptionNarration, voice: str) -> None:
    primary = next((m for m in result.metrics if m.is_significant), result.metrics[0] if result.metrics else None)
    if not primary or primary.expected_loss is None or primary.expected_impact is None:
        return
        
    exp_loss = primary.expected_loss
    exp_impact = primary.expected_impact
    
    st.markdown(
        f"<div class='tl-text-deep' style='font-weight:600;font-size:.95rem;text-transform:uppercase;letter-spacing:.05em;"
        f"margin:1.5rem 0 .5rem;'>Decision Intelligence</div>",
        unsafe_allow_html=True,
    )
    
    # Financial Impact Card
    loss_color = "#DC2626"
    impact_color = "#059669" if exp_impact >= 0 else "#DC2626"
    
    impact_str = f"${exp_impact:,.0f}"
    loss_str = f"${exp_loss:,.0f}"
    
    st.markdown(
        f"""<div class="tl-card" style="padding:1.25rem 1.5rem;margin-bottom:1rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
             <div>
               <div style="font-size:.65rem;text-transform:uppercase;letter-spacing:.1em;color:var(--tl-slate);font-weight:600;margin-bottom:.2rem;">
                 Expected Impact
               </div>
               <div style="font-size:1.4rem;font-weight:700;color:{impact_color};">
                 {impact_str}
               </div>
             </div>
             <div style="text-align:right;">
               <div style="font-size:.65rem;text-transform:uppercase;letter-spacing:.1em;color:var(--tl-slate);font-weight:600;margin-bottom:.2rem;">
                 Risk Exposure
               </div>
               <div style="font-size:1.4rem;font-weight:700;color:{loss_color};">
                 {loss_str}
               </div>
             </div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
    
    # For technical voice, show the slider to override the verdict based on risk tolerance
    if voice == "technical":
        st.markdown(
            f"<div style='font-size:.85rem;color:var(--tl-slate);margin-bottom:.5rem;'>"
            f"Set your acceptable risk threshold to override the statistical verdict.</div>",
            unsafe_allow_html=True,
        )
        max_slider_val = max(100.0, exp_loss * 5.0 if exp_loss > 0 else 1000.0)
        acceptable_risk = st.slider(
            "Acceptable Risk ($)",
            min_value=0.0,
            max_value=float(max_slider_val),
            value=float(max_slider_val * 0.1),
            step=float(max_slider_val / 100.0),
            key="acceptable_risk_slider"
        )
        
        if exp_impact <= 0:
            custom_verdict = "dont_ship"
            custom_text = "Kill (Negative Impact)"
        elif exp_loss <= acceptable_risk:
            custom_verdict = "ship"
            custom_text = "Ship (Risk is acceptable)"
        else:
            custom_verdict = "hold"
            custom_text = "Hold (Risk exceeds threshold)"
            
        color = _VERDICT_COLOR[custom_verdict]
        st.markdown(
            f"""<div style="padding:.75rem;border-left:4px solid {color};background:#F8FAFC;margin-top:.5rem;">
              <span style="font-size:.8rem;color:var(--tl-slate);text-transform:uppercase;letter-spacing:.05em;">
                Risk-Adjusted Verdict:
              </span>
              <strong style="color:{color};margin-left:.5rem;font-size:.9rem;">{custom_text}</strong>
            </div>""",
            unsafe_allow_html=True
        )

# ─────────────────────────── HTE section ───────────────────────────
def _render_hte_section(
    result: AnalysisResult,
    prescription: PrescriptionNarration,
    voice: str,
) -> None:
    """Render the 'Who benefits most?' section when HTE results are available."""
    hte = result.hte
    if hte is None:
        return

    # ── Section title ──
    st.markdown(
        f"<div class='tl-text-deep' style='font-weight:600;font-size:1.15rem;"
        f"margin:0 0 .5rem;'>{copy.step5_hte_title(voice)}</div>",
        unsafe_allow_html=True,
    )

    # ── HTE narration ──
    if prescription.hte_summary is not None:
        hte_text = (
            prescription.hte_summary.plain
            if voice == "plain"
            else prescription.hte_summary.technical
        )
        st.markdown(
            f"<div style='font-size:.92rem;line-height:1.55;color:var(--tl-slate);"
            f"margin-bottom:1.25rem;max-width:80ch;'>{hte_text}</div>",
            unsafe_allow_html=True,
        )

    # ── Two-column: importance + histogram ──
    col_imp, col_hist = st.columns([1, 1], gap="large")

    with col_imp:
        st.markdown(
            f"<div class='tl-text-deep' style='font-weight:500;margin:0 0 .5rem;'>"
            f"{copy.step5_hte_importance_title(voice)}</div>",
            unsafe_allow_html=True,
        )
        _render_hte_importance(hte)
        st.caption(copy.step5_hte_importance_caption(voice))

    with col_hist:
        st.markdown(
            f"<div class='tl-text-deep' style='font-weight:500;margin:0 0 .5rem;'>"
            f"{copy.step5_hte_histogram_title(voice)}</div>",
            unsafe_allow_html=True,
        )
        _render_hte_histogram(hte)
        st.caption(copy.step5_hte_histogram_caption(voice))

    # ── Subgroup table (full width) ──
    if hte.subgroups:
        st.markdown(
            f"<div class='tl-text-deep' style='font-weight:500;margin:1rem 0 .5rem;'>"
            f"{copy.step5_hte_subgroup_title(voice)}</div>",
            unsafe_allow_html=True,
        )
        _render_hte_subgroup_table(hte, voice)
        st.caption(copy.step5_hte_subgroup_caption(voice))


def _render_hte_importance(hte) -> None:
    """Horizontal bar chart of feature importances for heterogeneity."""
    import plotly.graph_objects as go

    sorted_feats = sorted(
        hte.feature_importances.items(), key=lambda x: x[1], reverse=True
    )
    names = [f[0].replace("_", " ").title() for f in sorted_feats]
    values = [f[1] for f in sorted_feats]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=names,
            orientation="h",
            marker_color="#F97316",  # tangerine
            text=[f"{v:.0%}" for v in values],
            textposition="outside",
        )
    )
    fig.update_layout(
        height=max(180, 45 * len(names)),
        margin=dict(l=0, r=50, t=10, b=0),
        xaxis=dict(
            range=[0, max(values) * 1.25] if values else [0, 1],
            showticklabels=False,
            showgrid=False,
        ),
        yaxis=dict(autorange="reversed"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#F8FAFC",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#0F172A"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_hte_histogram(hte) -> None:
    """Histogram of individual CATE values."""
    import numpy as np
    import plotly.graph_objects as go

    cate = np.array(hte.cate_values)

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=cate,
            nbinsx=40,
            marker_color="#1E3A5F",  # indigo-deep
            opacity=0.85,
        )
    )
    # Zero reference line
    fig.add_vline(x=0, line_dash="dash", line_color="#DC2626", line_width=1.5)
    # ATE reference line
    fig.add_vline(
        x=hte.ate_from_forest,
        line_dash="dot",
        line_color="#F97316",
        line_width=2,
        annotation_text="ATE",
        annotation_position="top right",
        annotation_font_size=11,
        annotation_font_color="#F97316",
    )

    fig.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title="Individual treatment effect",
        yaxis_title="Count",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#F8FAFC",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#0F172A"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_hte_subgroup_table(hte, voice: str) -> None:
    """Render a dataframe of subgroup CATE estimates."""
    ate = hte.ate_from_forest
    rows = []
    for sg in hte.subgroups:
        # Arrow for segments deviating >10% from ATE
        if ate != 0:
            deviation = (sg.mean_cate - ate) / abs(ate)
            if deviation > 0.10:
                direction = "▲ "
            elif deviation < -0.10:
                direction = "▼ "
            else:
                direction = ""
        else:
            direction = ""

        rows.append(
            {
                "Feature": sg.feature.replace("_", " ").title(),
                "Segment": sg.segment_label,
                "Size": sg.segment_size,
                "Effect (CATE)": f"{direction}{sg.mean_cate:,.0f}",
                "95% CI": f"[{sg.ci_lower:,.0f}, {sg.ci_upper:,.0f}]",
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


# ─────────────────────────── MAB Regret Simulator ───────────────────────────
def _render_bandit_section(
    s: wstate.WizardState,
    prescription: PrescriptionNarration,
    voice: str,
) -> None:
    """Render the 'Could smarter allocation have saved time?' section."""
    br = s.bandit_replay
    if br is None:
        return

    # ── Section title ──
    st.markdown(
        f"<div class='tl-text-deep' style='font-weight:600;font-size:1.15rem;"
        f"margin:0 0 .5rem;'>{copy.step5_bandit_title(voice)}</div>",
        unsafe_allow_html=True,
    )

    # ── Didactic intro ──
    st.markdown(
        f"<div style='font-size:.92rem;line-height:1.55;color:var(--tl-slate);"
        f"margin-bottom:1rem;max-width:80ch;'>{copy.step5_bandit_intro(voice)}</div>",
        unsafe_allow_html=True,
    )

    # ── Narration ──
    if prescription.bandit_summary is not None:
        narr_text = (
            prescription.bandit_summary.plain
            if voice == "plain"
            else prescription.bandit_summary.technical
        )
        st.markdown(
            f"<div style='font-size:.92rem;line-height:1.55;color:#0F172A;"
            f"margin-bottom:1.25rem;max-width:80ch;'>{narr_text}</div>",
            unsafe_allow_html=True,
        )

    # ── Charts (two columns) ──
    col_reward, col_alloc = st.columns([1, 1], gap="large")

    with col_reward:
        st.markdown(
            f"<div class='tl-text-deep' style='font-weight:500;margin:0 0 .5rem;'>"
            f"{copy.step5_bandit_reward_title(voice)}</div>",
            unsafe_allow_html=True,
        )
        _render_bandit_reward_chart(br)
        st.caption(copy.step5_bandit_reward_caption(voice))

    with col_alloc:
        st.markdown(
            f"<div class='tl-text-deep' style='font-weight:500;margin:0 0 .5rem;'>"
            f"{copy.step5_bandit_alloc_title(voice)}</div>",
            unsafe_allow_html=True,
        )
        _render_bandit_allocation_chart(br)
        st.caption(copy.step5_bandit_alloc_caption(voice))

    # ── Key numbers card ──
    _render_bandit_key_numbers(br, voice)


def _render_bandit_reward_chart(br) -> None:
    """Cumulative reward: AB vs TS vs Optimal."""
    import plotly.graph_objects as go

    labels = br.period_labels
    fig = go.Figure()

    # AB line
    fig.add_trace(go.Scatter(
        x=labels, y=br.cumulative_ab,
        mode="lines",
        name="Your A/B Test",
        line=dict(color="#475569", width=2),
    ))

    # Bandit line
    fig.add_trace(go.Scatter(
        x=labels, y=br.cumulative_bandit,
        mode="lines",
        name="Dynamic Allocation",
        line=dict(color="#F97316", width=2.5),
    ))

    # Optimal line
    fig.add_trace(go.Scatter(
        x=labels, y=br.cumulative_optimal,
        mode="lines",
        name="Best Possible",
        line=dict(color="#059669", width=1.5, dash="dash"),
    ))

    fig.update_layout(
        height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis_title="",
        yaxis_title="Cumulative reward",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#F8FAFC",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font_size=11,
        ),
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#0F172A"),
    )
    # Reduce x-axis clutter for many labels
    if len(labels) > 15:
        fig.update_xaxes(tickangle=-45, nticks=10)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_bandit_allocation_chart(br) -> None:
    """Allocation trajectory to the winning arm over time."""
    import plotly.graph_objects as go

    labels = br.period_labels
    alloc_pct = [a * 100 for a in br.allocation_to_winner]

    fig = go.Figure()

    # Fill area between 50% and the allocation line
    fig.add_trace(go.Scatter(
        x=labels, y=[50] * len(labels),
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=labels, y=alloc_pct,
        mode="lines",
        name="Allocation to winner",
        line=dict(color="#F97316", width=2.5),
        fill="tonexty",
        fillcolor="rgba(249, 115, 22, 0.12)",
    ))

    # 50% dashed reference
    fig.add_hline(
        y=50,
        line_dash="dash",
        line_color="#94A3B8",
        line_width=1,
        annotation_text="Equal split (A/B)",
        annotation_position="bottom right",
        annotation_font_size=10,
        annotation_font_color="#94A3B8",
    )

    # 75% convergence threshold
    fig.add_hline(
        y=75,
        line_dash="dot",
        line_color="#059669",
        line_width=1,
        annotation_text="Convergence (75%)",
        annotation_position="top right",
        annotation_font_size=10,
        annotation_font_color="#059669",
    )

    fig.update_layout(
        height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis_title="",
        yaxis_title="% traffic to winner",
        yaxis=dict(range=[0, 105]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#F8FAFC",
        showlegend=False,
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#0F172A"),
    )
    if len(labels) > 15:
        fig.update_xaxes(tickangle=-45, nticks=10)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_bandit_key_numbers(br, voice: str) -> None:
    """Three-column key numbers: Duration, Regret Saved, Convergence."""
    period_word = "days" if br.mode == "daily" else "batches"
    duration_val = f"{br.n_periods} {period_word}"
    saved_val = f"{br.regret_saved_pct:.0%}"
    saved_sub = f"≈ {br.regret_saved:,.0f} units of {br.metric_name}"

    if br.convergence_period is not None:
        conv_val = (
            f"Day {br.convergence_period}" if br.mode == "daily"
            else f"Batch {br.convergence_period}"
        )
    else:
        conv_val = "—"

    # Helper captions only in plain mode
    dur_help = copy.step5_bandit_duration_help(voice)
    saved_help = copy.step5_bandit_saved_help(voice)
    conv_help = copy.step5_bandit_convergence_help(voice)

    def _helper_html(text: str) -> str:
        if not text:
            return ""
        return (
            f"<div style='font-size:.7rem;color:#94A3B8;margin-top:.25rem;"
            f"font-style:italic;'>{text}</div>"
        )

    st.markdown(
        f"""<div class="tl-card" style="display:flex;justify-content:space-around;
                text-align:center;padding:1.25rem 1rem;margin-top:.75rem;flex-wrap:wrap;gap:1rem;">
          <div style="min-width:100px;">
            <div style="font-size:.65rem;text-transform:uppercase;letter-spacing:.1em;
                        color:var(--tl-tangerine);font-weight:600;margin-bottom:.25rem;">
              {copy.step5_bandit_duration_label(voice)}
            </div>
            <div style="font-size:1.4rem;font-weight:700;color:#0F172A;">{duration_val}</div>
            {_helper_html(dur_help)}
          </div>
          <div style="min-width:120px;">
            <div style="font-size:.65rem;text-transform:uppercase;letter-spacing:.1em;
                        color:var(--tl-tangerine);font-weight:600;margin-bottom:.25rem;">
              {copy.step5_bandit_saved_label(voice)}
            </div>
            <div style="font-size:1.4rem;font-weight:700;color:var(--tl-success);">{saved_val}</div>
            <div style="font-size:.75rem;color:var(--tl-slate);margin-top:.1rem;">{saved_sub}</div>
            {_helper_html(saved_help)}
          </div>
          <div style="min-width:100px;">
            <div style="font-size:.65rem;text-transform:uppercase;letter-spacing:.1em;
                        color:var(--tl-tangerine);font-weight:600;margin-bottom:.25rem;">
              {copy.step5_bandit_convergence_label(voice)}
            </div>
            <div style="font-size:1.4rem;font-weight:700;color:#0F172A;">{conv_val}</div>
            {_helper_html(conv_help)}
          </div>
        </div>""",
        unsafe_allow_html=True,
    )


# ─────────────────────────── Export rail ───────────────────────────
def _render_export_rail(s: wstate.WizardState) -> None:
    """Stacked export download buttons in the right rail."""
    bq = s.business_question or ""
    md = to_markdown(
        s.result, s.prescription, voice=s.voice,
        business_question=bq, bandit_replay=s.bandit_replay,
    )

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
