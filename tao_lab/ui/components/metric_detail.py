"""Per-metric detail cards with progressive disclosure.

Each row shows: metric name + significance icon, relative lift, raw p-value,
and a 'Read more' expander revealing the full statistical row (control vs
treatment means, raw + BH-adjusted p, CI, n, test stat, effect size).

Phase 4: voice-aware labels for plain/spectrum modes.
"""

from __future__ import annotations

from typing import Literal

import streamlit as st

from tao_lab.methods.base import AnalysisResult, MetricResult
from tao_lab.ui.strings import Voice, copy


_SUCCESS = "#059669"
_DANGER = "#DC2626"
_SLATE = "#475569"


def render_metric_details(result: AnalysisResult, *, voice: Voice = "signal") -> None:
    if not result.metrics:
        st.caption("No metrics to display.")
        return

    for m in result.metrics:
        _render_row(m, voice=voice)


def _render_row(m: MetricResult, *, voice: Voice) -> None:
    sig_color, sig_label, sig_icon = _significance_badge(m, voice=voice)
    lift_color = _SUCCESS if m.lift_relative > 0 else (_DANGER if m.lift_relative < 0 else _SLATE)

    lift_header = copy.step5_lift_label(voice)
    certainty_header = copy.step5_pvalue_label(voice)
    p_str = f"{m.p_value:.4g}" if m.p_value is not None else "—"

    # ── Signal one-liner summary ──
    signal_summary = ""
    if voice == "signal":
        direction = "higher" if m.lift_relative > 0 else "lower" if m.lift_relative < 0 else "the same"
        signal_summary = (
            f"<div class='tl-text-slate' style='font-size:.82rem;margin-top:.4rem;"
            f"line-height:1.4;'>"
            f"The treatment group averaged {m.treatment_mean:.4g} vs {m.control_mean:.4g} "
            f"in the control group ({direction} by {abs(m.lift_absolute):.4g})."
            f"</div>"
        )

    st.markdown(
        f"""
        <div class="tl-card" style="padding:1rem 1.25rem;margin-bottom:.5rem;">
          <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
            <div style="flex:1;min-width:160px;">
              <div class="tl-text-deep" style="font-weight:600;">{m.metric_name}</div>
              <div style="font-size:.8rem;color:{sig_color};font-weight:500;margin-top:.15rem;">
                {sig_icon} {sig_label}
              </div>
            </div>
            <div style="font-variant-numeric:tabular-nums;text-align:right;min-width:120px;">
              <div class="tl-text-slate" style="font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;">
                {lift_header}
              </div>
              <div style="font-size:1.1rem;font-weight:600;color:{lift_color};">
                {m.lift_relative * 100:+.2f}%
              </div>
            </div>
            <div style="font-variant-numeric:tabular-nums;text-align:right;min-width:90px;">
              <div class="tl-text-slate" style="font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;">
                {certainty_header}
              </div>
              <div class="tl-text-deep" style="font-size:1.1rem;font-weight:500;">
                {p_str}
              </div>
            </div>
          </div>
          {signal_summary}
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(f"Detailed statistics — {m.metric_name}", expanded=False):
        rows = _detail_rows(m, voice=voice)
        st.dataframe(rows, use_container_width=True, hide_index=True)
        if m.warning_message:
            st.caption(m.warning_message)


def _significance_badge(m: MetricResult, *, voice: Voice = "signal") -> tuple[str, str, str]:
    if m.is_significant:
        label = copy.step5_sig_yes(voice)
        return _SUCCESS, label, "●"
    if m.p_value is None:
        return _SLATE, "No p-value computed", "○"
    label = copy.step5_sig_no(voice)
    return _SLATE, label, "○"


def _detail_rows(m: MetricResult, *, voice: Voice = "signal") -> list[dict]:
    fmt = lambda x, spec=".4g": format(x, spec) if x is not None else "—"
    if voice == "signal":
        rows = [
            {"Quantity": "Average (group without the change)", "Value": fmt(m.control_mean)},
            {"Quantity": "Average (group with the change)", "Value": fmt(m.treatment_mean)},
            {"Quantity": "Difference", "Value": fmt(m.lift_absolute)},
            {"Quantity": "Percentage change", "Value": fmt(m.lift_relative * 100, ".4g") + " %"},
            {"Quantity": "Plausible range (95% CI)", "Value": f"[{fmt(m.ci_lower)}, {fmt(m.ci_upper)}]"},
            {"Quantity": "p-value", "Value": fmt(m.p_value, ".4g")},
            {"Quantity": "p-value (adjusted)", "Value": fmt(m.p_value_adjusted, ".4g")},
            {"Quantity": "Effect size", "Value": fmt(m.effect_size)},
            {"Quantity": "Rows in control", "Value": fmt(m.n_control, ",d") if m.n_control else "—"},
            {"Quantity": "Rows in treatment", "Value": fmt(m.n_treatment, ",d") if m.n_treatment else "—"},
        ]
    else:
        rows = [
            {"Quantity": "Control mean", "Value": fmt(m.control_mean)},
            {"Quantity": "Treatment mean", "Value": fmt(m.treatment_mean)},
            {"Quantity": "Absolute lift", "Value": fmt(m.lift_absolute)},
            {"Quantity": "Relative lift", "Value": fmt(m.lift_relative * 100, ".4g") + " %"},
            {"Quantity": "95% CI (absolute)", "Value": f"[{fmt(m.ci_lower)}, {fmt(m.ci_upper)}]"},
            {"Quantity": "p-value (raw)", "Value": fmt(m.p_value, ".4g")},
            {"Quantity": "p-value (BH-adjusted)", "Value": fmt(m.p_value_adjusted, ".4g")},
            {"Quantity": "Test statistic", "Value": fmt(m.test_statistic)},
            {"Quantity": "Effect size (Cohen's d)", "Value": fmt(m.effect_size)},
            {"Quantity": "Sample size (control)", "Value": fmt(m.n_control, ",d") if m.n_control else "—"},
            {"Quantity": "Sample size (treatment)", "Value": fmt(m.n_treatment, ",d") if m.n_treatment else "—"},
            {"Quantity": "Metric type", "Value": m.metric_type},
        ]
    return rows
