"""Per-metric detail cards with progressive disclosure.

Each row shows: metric name + significance icon, relative lift, raw p-value,
and a 'Read more' expander revealing the full statistical row (control vs
treatment means, raw + BH-adjusted p, CI, n, test stat, effect size).
"""

from __future__ import annotations

import streamlit as st

from tao_lab.methods.base import AnalysisResult, MetricResult


_SUCCESS = "#059669"
_DANGER = "#DC2626"
_SLATE = "#475569"


def render_metric_details(result: AnalysisResult) -> None:
    if not result.metrics:
        st.caption("No metrics to display.")
        return

    for m in result.metrics:
        _render_row(m)


def _render_row(m: MetricResult) -> None:
    sig_color, sig_label, sig_icon = _significance_badge(m)
    lift_color = _SUCCESS if m.lift_relative > 0 else (_DANGER if m.lift_relative < 0 else _SLATE)

    p_str = f"{m.p_value:.4g}" if m.p_value is not None else "—"

    st.markdown(
        f"""
        <div class="tl-card" style="padding:1rem 1.25rem;margin-bottom:.5rem;">
          <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
            <div style="flex:1;min-width:160px;">
              <div style="font-weight:600;color:var(--tl-indigo-deep);">{m.metric_name}</div>
              <div style="font-size:.8rem;color:{sig_color};font-weight:500;margin-top:.15rem;">
                {sig_icon} {sig_label}
              </div>
            </div>
            <div style="font-variant-numeric:tabular-nums;text-align:right;min-width:120px;">
              <div style="font-size:.7rem;color:var(--tl-slate);text-transform:uppercase;letter-spacing:.06em;">
                Relative lift
              </div>
              <div style="font-size:1.1rem;font-weight:600;color:{lift_color};">
                {m.lift_relative * 100:+.2f}%
              </div>
            </div>
            <div style="font-variant-numeric:tabular-nums;text-align:right;min-width:90px;">
              <div style="font-size:.7rem;color:var(--tl-slate);text-transform:uppercase;letter-spacing:.06em;">
                p-value
              </div>
              <div style="font-size:1.1rem;font-weight:500;color:var(--tl-indigo-deep);">
                {p_str}
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(f"Detailed statistics — {m.metric_name}", expanded=False):
        rows = _detail_rows(m)
        st.dataframe(rows, use_container_width=True, hide_index=True)
        if m.warning_message:
            st.caption(m.warning_message)


def _significance_badge(m: MetricResult) -> tuple[str, str, str]:
    if m.is_significant:
        return _SUCCESS, "Statistically significant", "●"
    if m.p_value is None:
        return _SLATE, "No p-value computed", "○"
    return _SLATE, "Not significant", "○"


def _detail_rows(m: MetricResult) -> list[dict]:
    fmt = lambda x, spec=".4g": format(x, spec) if x is not None else "—"
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
