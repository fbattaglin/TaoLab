"""Step 2 — Diagnose.

Phase D: ranked selectable method cards replace the single hero card.
Users see all eligible methods scored by the diagnosis engine and can
override the recommendation.  Warnings are shown for the *selected*
method, not just the top-ranked one.
"""

from __future__ import annotations

import streamlit as st

from tao_lab.diagnose.engine import compute_data_health_score, diagnose_data
from tao_lab.ui import state as wstate
from tao_lab.ui.components.data_health import render_health_score
from tao_lab.ui.components.method_card import render_method_selector
from tao_lab.ui.strings import copy


def render() -> None:
    s = wstate.get_state()
    if s.df is None:
        st.info("Upload data first.")
        return

    voice = s.voice
    if s.diagnosis is None:
        s.diagnosis = diagnose_data(s.df)
        s.selected_candidate_idx = 0  # reset selection on new diagnosis
    report = s.diagnosis

    # ── Data health score (uses assignment col from top candidate) ──
    assignment_col = report.config_hint.get("assignment_col")
    health = compute_data_health_score(s.df, assignment_col=assignment_col)

    main_col, side_col = st.columns([2, 1], gap="large")
    with main_col:
        # ── Selectable method cards ──
        new_idx = render_method_selector(
            report.candidates,
            s.selected_candidate_idx,
            voice=voice,
        )
        if new_idx is not None:
            s.selected_candidate_idx = new_idx
            st.rerun()

        # ── Warnings for the *selected* method ──
        selected = report.candidates[s.selected_candidate_idx]
        if selected.warnings:
            st.markdown(
                "<div class='tl-text-deep' style='font-weight:500;margin:1.5rem 0 .5rem;'>"
                "Things to know before you run"
                "</div>",
                unsafe_allow_html=True,
            )
            for w in selected.warnings:
                _render_warning_card(w)

    with side_col:
        st.markdown(
            f"<div class='tl-text-deep' style='font-weight:500;margin:0 0 .75rem;'>"
            f"{copy.step2_health_title(voice)}</div>",
            unsafe_allow_html=True,
        )
        render_health_score(health)

    st.markdown("<hr class='tl-divider'>", unsafe_allow_html=True)

    # ── Navigation ──
    selected_candidate = report.candidates[s.selected_candidate_idx]
    display_name = selected_candidate.method

    nav_a, nav_b = st.columns([1, 3])
    with nav_a:
        if st.button("← Back", key="diag_back", use_container_width=True):
            wstate.go_back()
    with nav_b:
        button_label = copy.step2_use_selected(voice).replace("→", f"({display_name}) →")
        if st.button(
            button_label,
            type="primary",
            use_container_width=True,
            key="diag_continue",
        ):
            s.chosen_method = selected_candidate.method
            # Clear any config from a previous pass so Step 3 re-renders
            s.config = None
            wstate.advance()


def _render_warning_card(text: str) -> None:
    st.markdown(
        f"""
        <div class="tl-card" style="
          border-left:3px solid var(--tl-warning);
          padding:.9rem 1.1rem;margin-bottom:.5rem;
        ">
          <div class="tl-text-ink">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
