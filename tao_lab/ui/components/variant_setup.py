"""Visual control vs treatment setup for Step 3.

Two cards side by side, each showing the chosen variant value plus the
observed sample size. Clicking either card opens a selectbox to swap. The
component returns `(assignment_col, control_val, treatment_val)`.

For Phase B the swap UI is a regular Streamlit selectbox below the cards —
streamlit-shadcn-ui's `select` is not stable across versions, so we keep the
fallback. The cards are read-only summaries and the actual mutation happens
through the selectboxes below.
"""

from __future__ import annotations

from typing import Any, Tuple

import polars as pl
import streamlit as st


def render_variant_setup(
    df: pl.DataFrame,
    default_assignment: str,
    default_control: Any,
    default_treatment: Any,
) -> Tuple[str, Any, Any]:
    sel_a, sel_b, sel_c = st.columns(3)
    with sel_a:
        assignment_col = st.selectbox(
            "Assignment column",
            df.columns,
            index=df.columns.index(default_assignment) if default_assignment in df.columns else 0,
            help="The column that says which variant each unit was put into.",
        )
    unique_vals = df.select(assignment_col).unique().to_series().to_list()
    with sel_b:
        ctrl_idx = unique_vals.index(default_control) if default_control in unique_vals else 0
        control_val = st.selectbox("Control variant", unique_vals, index=ctrl_idx)
    with sel_c:
        candidates = [v for v in unique_vals if v != control_val]
        treat_idx = candidates.index(default_treatment) if default_treatment in candidates else 0
        treatment_val = st.selectbox(
            "Treatment variant",
            candidates,
            index=treat_idx if candidates else 0,
        )

    # Live sample-size preview cards.
    n_c = df.filter(pl.col(assignment_col) == control_val).height
    n_t = df.filter(pl.col(assignment_col) == treatment_val).height

    card_c, card_t = st.columns(2)
    _variant_card(card_c, "Control", control_val, n_c, accent=False)
    _variant_card(card_t, "Treatment", treatment_val, n_t, accent=True)

    if n_c and n_t:
        ratio = n_c / (n_c + n_t)
        msg = (
            f"Comparing **{n_t:,} units** in Treatment vs **{n_c:,} units** in Control "
            f"(split: {ratio:.0%} / {1 - ratio:.0%})."
        )
        st.markdown(
            f"<div style='color:var(--tl-slate);margin-top:.5rem;'>{msg}</div>",
            unsafe_allow_html=True,
        )

    return assignment_col, control_val, treatment_val


def _variant_card(slot, label: str, value: Any, n: int, *, accent: bool) -> None:
    border_color = "var(--tl-tangerine)" if accent else "var(--tl-hairline)"
    eyebrow_color = "var(--tl-tangerine)" if accent else "var(--tl-slate)"
    slot.markdown(
        f"""
        <div class="tl-card" style="border-color:{border_color};padding:1.25rem;">
          <div style="font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;
                      color:{eyebrow_color};font-weight:600;">{label}</div>
          <div style="font-size:1.4rem;font-weight:600;color:var(--tl-indigo-deep);
                      margin-top:.25rem;line-height:1.2;">{value}</div>
          <div style="color:var(--tl-slate);margin-top:.75rem;font-size:.9rem;">
            <span style="font-variant-numeric:tabular-nums;font-weight:500;">
              {n:,}
            </span> units observed
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
