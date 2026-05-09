"""Metric picker for Step 3.

Two surfaces:

* **Continuous metrics**: a Streamlit multiselect, plus a 'preview' row that
  shows a tiny histogram for the first three picked columns. The hover
  affordance promised by the design plan is realised through the histogram —
  Streamlit can't currently show a tooltip-on-chip without a custom component,
  but seeing the distribution under the picker hits the same goal.
* **Ratio metrics**: a toggle that, when on, exposes one row per ratio with
  numerator + denominator selectboxes and an auto-named field. Defaults are
  prefilled from the diagnose hint.
"""

from __future__ import annotations

from typing import Any, List

import polars as pl
import plotly.graph_objects as go
import streamlit as st

from tao_lab.methods.base import RatioMetric
from tao_lab.ui.components.explainer import helper_caption


def render_metric_picker(
    df: pl.DataFrame,
    default_metrics: List[str],
    default_ratios: List[dict],
) -> tuple[List[str], List[RatioMetric]]:
    numeric_cols = [c for c in df.columns if df.schema[c].is_numeric()]
    metric_cols = st.multiselect(
        "Continuous metrics to evaluate",
        numeric_cols,
        default=[c for c in default_metrics if c in numeric_cols],
        help="Per-unit numeric outcomes. We'll compare averages between groups.",
    )

    if metric_cols:
        _render_distribution_preview(df, metric_cols[:3])

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    use_ratios = st.toggle(
        "Track ratio metrics (e.g. CTR = clicks / impressions)",
        value=bool(default_ratios),
    )
    helper_caption(
        "Ratio metrics use the Delta Method automatically — that's the right way to "
        "estimate uncertainty when both numerator and denominator vary across units."
    )

    ratio_metrics: List[RatioMetric] = []
    if use_ratios:
        ratio_metrics = _render_ratio_rows(df, default_ratios)

    return metric_cols, ratio_metrics


def _render_distribution_preview(df: pl.DataFrame, cols: List[str]) -> None:
    cols_layout = st.columns(len(cols))
    for slot, col in zip(cols_layout, cols):
        try:
            arr = df.select(pl.col(col).cast(pl.Float64)).drop_nulls().to_series().to_numpy()
            fig = go.Figure(
                data=[go.Histogram(x=arr, marker_color="#1E3A5F", nbinsx=30)]
            )
            fig.update_layout(
                title=dict(text=col, x=0.0, xanchor="left", font=dict(size=12)),
                height=140,
                margin=dict(l=20, r=10, t=30, b=20),
                plot_bgcolor="white",
                paper_bgcolor="white",
                showlegend=False,
                bargap=0.05,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#E2E8F0"),
            )
            with slot:
                st.plotly_chart(fig, use_container_width=True)
        except Exception:  # noqa: BLE001
            with slot:
                st.caption(f"{col}: preview unavailable")


def _render_ratio_rows(df: pl.DataFrame, default_ratios: List[dict]) -> List[RatioMetric]:
    n_rows = max(1, len(default_ratios))
    n_rows = st.number_input(
        "How many ratio metrics?",
        min_value=1,
        max_value=5,
        value=n_rows,
        step=1,
    )
    out: List[RatioMetric] = []
    for i in range(int(n_rows)):
        preset = default_ratios[i] if i < len(default_ratios) else None
        st.markdown(
            f"<div style='font-weight:500;color:var(--tl-indigo-deep);"
            f"margin:.75rem 0 .25rem;'>Ratio {i + 1}</div>",
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns([2, 1.2, 1.2])
        with c2:
            num_default = preset["num"] if preset and preset["num"] in df.columns else df.columns[0]
            num_col = st.selectbox(
                f"Numerator (ratio {i + 1})",
                df.columns,
                index=df.columns.index(num_default),
                key=f"ratio_num_{i}",
            )
        with c3:
            den_default = preset["den"] if preset and preset["den"] in df.columns else df.columns[min(1, df.width - 1)]
            den_col = st.selectbox(
                f"Denominator (ratio {i + 1})",
                df.columns,
                index=df.columns.index(den_default),
                key=f"ratio_den_{i}",
            )
        with c1:
            auto_name = f"{num_col} / {den_col}"
            name_default = preset["name"] if preset else auto_name
            name = st.text_input(
                f"Name (ratio {i + 1})",
                value=name_default,
                key=f"ratio_name_{i}",
            )
        out.append(RatioMetric(name=name, numerator_col=num_col, denominator_col=den_col))
    return out
