"""Visual control vs treatment setup for Step 3.

Two cards side by side, each showing the chosen variant value plus the
observed sample size. Clicking either card opens a selectbox to swap. The
component returns `(assignment_col, control_val, treatment_val)`.

Phase 4 updates:
* Voice-aware labels: "Group column" (plain) / "Assignment column" (technical).
* Helper captions on Control/Treatment selectboxes.
* Contextual unit noun on variant cards.
"""

from __future__ import annotations

from typing import Any, Literal, Tuple

import polars as pl
import streamlit as st

from tao_lab.ui.components.explainer import helper_caption
from tao_lab.ui.strings import Voice, copy


def render_variant_setup(
    df: pl.DataFrame,
    default_assignment: str,
    default_control: Any,
    default_treatment: Any,
    *,
    voice: Voice = "signal",
) -> Tuple[str, Any, Any]:
    sel_a, sel_b, sel_c = st.columns(3)
    with sel_a:
        assignment_col = st.selectbox(
            copy.step3_group_col_label(voice),
            df.columns,
            index=df.columns.index(default_assignment) if default_assignment in df.columns else 0,
            help="The column that says which variant each unit was put into.",
        )
        if voice == "signal":
            helper_caption(
                "The column that says which group each row belongs to "
                "— e.g. Control vs Treatment, A vs B."
            )
    unique_vals = df.select(assignment_col).unique().to_series().to_list()
    with sel_b:
        ctrl_idx = unique_vals.index(default_control) if default_control in unique_vals else 0
        control_val = st.selectbox(
            "Control variant",
            unique_vals,
            index=ctrl_idx,
            help="The group that did NOT receive the change.",
        )
        if voice == "signal":
            helper_caption("The group that did NOT receive the change — the baseline.")
    with sel_c:
        candidates = [v for v in unique_vals if v != control_val]
        treat_idx = candidates.index(default_treatment) if default_treatment in candidates else 0
        treatment_val = st.selectbox(
            "Treatment variant",
            candidates,
            index=treat_idx if candidates else 0,
            help="The group that received the change you're testing.",
        )
        if voice == "signal":
            helper_caption("The group that received the change you're testing.")

    # Live sample-size preview cards.
    n_c = df.filter(pl.col(assignment_col) == control_val).height
    n_t = df.filter(pl.col(assignment_col) == treatment_val).height

    card_c, card_t = st.columns(2)
    _variant_card(card_c, "Control", control_val, n_c, accent=False)
    _variant_card(card_t, "Treatment", treatment_val, n_t, accent=True)

    if n_c and n_t:
        ratio = n_c / (n_c + n_t)
        if voice == "signal":
            msg = (
                f"Comparing <strong>{n_t:,} rows</strong> in the Treatment group "
                f"vs <strong>{n_c:,} rows</strong> in the Control group "
                f"(split: {ratio:.0%} / {1 - ratio:.0%})."
            )
        else:
            msg = (
                f"Comparing **{n_t:,} units** in Treatment vs **{n_c:,} units** in Control "
                f"(split: {ratio:.0%} / {1 - ratio:.0%})."
            )
        st.markdown(
            f"<div class='tl-text-slate' style='margin-top:.5rem;'>{msg}</div>",
            unsafe_allow_html=True,
        )

    return assignment_col, control_val, treatment_val


def _variant_card(slot, label: str, value: Any, n: int, *, accent: bool) -> None:
    border_color = "var(--tl-tangerine)" if accent else "var(--tl-hairline)"
    eyebrow_class = "tl-text-tangerine" if accent else "tl-text-slate"
    # Note: tl-text-tangerine doesn't exist yet, I should add it or use style
    eyebrow_style = "color:var(--tl-tangerine) !important;" if accent else ""
    eyebrow_class = "" if accent else "tl-text-slate"
    
    slot.markdown(
        f"""
        <div class="tl-card" style="border-color:{border_color};padding:1.25rem;">
          <div class="{eyebrow_class}" style="font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;
                      {eyebrow_style} font-weight:600;">{label}</div>
          <div class="tl-text-deep" style="font-size:1.4rem;font-weight:600;
                      margin-top:.25rem;line-height:1.2;">{value}</div>
          <div class="tl-text-slate" style="margin-top:.75rem;font-size:.9rem;">
            <span style="font-variant-numeric:tabular-nums;font-weight:500;">
              {n:,}
            </span> rows
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
