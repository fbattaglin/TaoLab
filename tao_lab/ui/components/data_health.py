"""Data Health Snapshot + Score components.

Two surfaces:

* **Snapshot** (Step 1): one row per column with type, missing %, and a
  miniature distribution sparkline. Users see at a glance whether the upload
  is clean before they move forward.
* **Score** (Step 2): a 0–100 composite with breakdown by dimension, rendered
  as a side panel next to the Method Card.

Plotly is used for the sparklines/bar charts because Streamlit already ships
with it; we keep the layout flat and tooltip-rich rather than chasing pixel-
perfect mini-charts.
"""

from __future__ import annotations

from typing import Optional

import polars as pl
import plotly.graph_objects as go
import streamlit as st

from tao_lab.diagnose.engine import DataHealthReport, HealthDimension


_STATUS_COLOR = {
    "pass": "#059669",
    "warn": "#D97706",
    "fail": "#DC2626",
}


# ─────────────────────── Step 1 — Snapshot ───────────────────────
def render_data_snapshot(df: pl.DataFrame, assignment_col: Optional[str] = None) -> None:
    """Render the per-column health snapshot. Rows × columns metric on top,
    then a compact table per column, then a group-balance bar chart if an
    assignment column is detected."""
    top_a, top_b, top_c = st.columns(3)
    top_a.metric("Rows", f"{df.height:,}")
    top_b.metric("Columns", f"{df.width}")
    numeric_n = sum(1 for c in df.columns if df.schema[c].is_numeric())
    top_c.metric("Numeric columns", f"{numeric_n}")

    st.markdown(
        "<div style='font-weight:500;margin:1rem 0 .5rem;color:var(--tl-indigo-deep);'>"
        "Per-column overview"
        "</div>",
        unsafe_allow_html=True,
    )

    rows = []
    for col in df.columns:
        dtype = str(df.schema[col])
        try:
            null_frac = df.select(pl.col(col).is_null().mean()).item() or 0.0
        except Exception:  # noqa: BLE001
            null_frac = 0.0
        try:
            uniq = df.select(pl.col(col).n_unique()).item()
        except Exception:  # noqa: BLE001
            uniq = None
        rows.append(
            {
                "column": col,
                "type": dtype,
                "missing": f"{null_frac:.1%}" if null_frac else "—",
                "unique": uniq if uniq is not None else "—",
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)

    if assignment_col and assignment_col in df.columns:
        try:
            counts = (
                df.group_by(assignment_col).len().sort("len", descending=True)
            )
            labels = counts.select(assignment_col).to_series().to_list()
            sizes = counts.select("len").to_series().to_list()
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=[str(x) for x in labels],
                        y=sizes,
                        marker_color="#1E3A5F",
                        text=[f"{n:,}" for n in sizes],
                        textposition="outside",
                    )
                ]
            )
            fig.update_layout(
                title=f"Group balance — '{assignment_col}'",
                height=220,
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor="white",
                paper_bgcolor="white",
                yaxis=dict(showgrid=True, gridcolor="#E2E8F0"),
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception:  # noqa: BLE001
            pass


# ─────────────────────── Step 2 — Score panel ───────────────────────
def render_health_score(report: DataHealthReport) -> None:
    """Render the score header + per-dimension breakdown as a vertical card."""
    color = _STATUS_COLOR.get(report.overall_status, "#475569")

    st.markdown(
        f"""
        <div class="tl-card" style="margin-bottom:1rem;">
          <div style="font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;color:var(--tl-slate);">
            Data Health Score
          </div>
          <div style="display:flex;align-items:baseline;gap:.5rem;margin-top:.25rem;">
            <div style="font-size:2.25rem;font-weight:600;color:{color};line-height:1;">
              {report.overall_score}
            </div>
            <div style="color:var(--tl-slate-soft);">/ 100</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for dim in report.dimensions:
        _render_dimension_row(dim)


def _render_dimension_row(dim: HealthDimension) -> None:
    color = _STATUS_COLOR.get(dim.status, "#475569")
    icon = {"pass": "✓", "warn": "!", "fail": "✕"}.get(dim.status, "•")
    st.markdown(
        f"""
        <div style="display:flex;gap:.75rem;padding:.6rem .25rem;border-bottom:1px solid var(--tl-hairline);">
          <div style="
            flex:none;width:24px;height:24px;border-radius:9999px;
            background:{color}1A;color:{color};
            display:flex;align-items:center;justify-content:center;
            font-weight:700;font-size:.85rem;
          ">{icon}</div>
          <div style="flex:1;">
            <div style="font-weight:500;color:var(--tl-indigo-deep);">{dim.label}</div>
            <div style="color:var(--tl-slate);font-size:.85rem;line-height:1.4;">{dim.detail}</div>
          </div>
          <div style="flex:none;color:{color};font-weight:600;font-variant-numeric:tabular-nums;">
            {dim.score}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
