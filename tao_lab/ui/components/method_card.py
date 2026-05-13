"""Selectable method cards for the Diagnose step.

Phase D: ranked, clickable cards.
Phase 4: voice-aware blurbs + assumption surfacing.
"""

from __future__ import annotations

from typing import List, Optional

import streamlit as st

from tao_lab.diagnose.engine import MethodCandidate
from tao_lab.ui.strings import METHOD_BLURBS, Voice, copy


def render_method_selector(
    candidates: List[MethodCandidate],
    selected_idx: int,
    *,
    voice: Voice = "plain",
) -> Optional[int]:
    """Render ranked, selectable method cards.

    Returns the newly selected index if the user clicked a different card,
    or ``None`` if selection didn't change.
    """
    if not candidates:
        st.warning("No analysis methods are eligible for this dataset.")
        return None

    new_selection: Optional[int] = None

    # ── Show ambiguity note when ≥2 candidates score above 0.4 ──
    high_scorers = [c for c in candidates if c.score >= 0.4]
    if len(high_scorers) >= 2:
        st.markdown(
            f"<div style='font-size:.85rem;color:var(--tl-slate);margin-bottom:1rem;"
            f"line-height:1.5;'>"
            f"{copy.step2_ambiguity_note(voice)}</div>",
            unsafe_allow_html=True,
        )

    for i, candidate in enumerate(candidates):
        if candidate.score <= 0:
            continue

        is_selected = i == selected_idx
        is_top = i == 0

        # ── Badge ──
        if is_top:
            badge_text = copy.step2_best_fit_badge(voice)
            badge_color = "var(--tl-tangerine)"
        else:
            badge_text = copy.step2_also_viable_badge(voice)
            badge_color = "var(--tl-slate)"

        score_pct = int(candidate.score * 100)

        # ── Display name + voice-aware blurb ──
        blurb = METHOD_BLURBS.get(candidate.method)
        display_name = blurb.display_name if blurb else candidate.method
        description = (blurb.plain if voice == "plain" else blurb.technical) if blurb else ""
        assumptions = (
            (blurb.assumptions_plain if voice == "plain" else blurb.assumptions_technical)
            if blurb else ""
        )

        # ── Border style ──
        border_color = "var(--tl-tangerine)" if is_selected else "var(--tl-hairline)"
        border_width = "2px" if is_selected else "1px"
        bg_color = "var(--tl-tangerine-soft)" if is_selected else "var(--tl-cloud)"

        # ── Radio indicator ──
        radio = "●" if is_selected else "○"
        radio_color = "var(--tl-tangerine)" if is_selected else "var(--tl-slate)"

        # ── Requirements line ──
        req_html = ""
        if candidate.requirements:
            req_label = copy.step2_requirements_label(voice)
            reqs = " · ".join(candidate.requirements)
            req_html = (
                f"<div class='tl-text-slate' style='font-size:.8rem;margin-top:.5rem;'>"
                f"<span style='font-weight:600;'>{req_label}:</span> {reqs}</div>"
            )

        # ── Assumptions line ──
        assume_html = ""
        if assumptions:
            assume_html = (
                f"<div class='tl-text-slate' style='font-size:.82rem;margin-top:.5rem;"
                f"border-left:2px solid var(--tl-hairline);padding-left:.75rem;"
                f"font-style:italic;line-height:1.4;'>"
                f"{assumptions}</div>"
            )

        # ── HTE badge (Causal Inference only) ──
        hte_html = ""
        if (
            candidate.method == "Causal Inference"
            and candidate.config_hint.get("hte_eligible")
        ):
            hte_badge = copy.step2_hte_badge(voice)
            hte_html = (
                f"<div style='font-size:.8rem;color:var(--tl-tangerine);margin-top:.5rem;"
                f"font-weight:500;'>✦ {hte_badge}</div>"
            )

        card_html = f"""
        <div style="
          border:{border_width} solid {border_color};
          border-radius:12px;
          padding:1.25rem 1.5rem;
          margin-bottom:.75rem;
          background:{bg_color};
          cursor:pointer;
          transition:border-color 0.15s, background 0.15s;
        ">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="display:flex;align-items:center;gap:.6rem;">
              <span style="font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;
                           color:{badge_color};font-weight:600;">
                {badge_text}
              </span>
              <span style="font-size:.75rem;color:var(--tl-slate);">
                {score_pct}% match
              </span>
            </div>
            <span style="font-size:1.1rem;color:{radio_color};">{radio}</span>
          </div>
          <h3 class="tl-card-title">
            {display_name}
          </h3>
          <p class="tl-text-ink" style="font-size:.9rem;line-height:1.5;margin:0 0 .3rem;max-width:70ch;">
            {description}
          </p>
          <p class="tl-text-slate" style="font-size:.85rem;line-height:1.45;margin:0;max-width:70ch;">
            {candidate.rationale}
          </p>
          {assume_html}
          {req_html}
          {hte_html}
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        # ── Selection button (visually hidden, overlays the card area) ──
        if not is_selected:
            if st.button(
                f"Select {display_name}",
                key=f"select_method_{i}",
                type="secondary",
                use_container_width=True,
            ):
                new_selection = i

    return new_selection


def render_method_override_picker(
    candidates: List[MethodCandidate],
    selected_idx: int,
    *,
    voice: Voice = "plain",
) -> Optional[int]:
    """Compact picker that lists ALL candidates (including score=0 ones).

    Shown inside an expander so it doesn't clutter the normal flow.
    Returns the newly selected index, or None if unchanged.
    """
    st.markdown(
        f"<div style='font-size:.85rem;color:var(--tl-slate);margin-bottom:1rem;"
        f"line-height:1.5;'>{copy.step2_override_hint(voice)}</div>",
        unsafe_allow_html=True,
    )

    new_selection: Optional[int] = None

    for i, candidate in enumerate(candidates):
        is_selected = i == selected_idx
        blurb = METHOD_BLURBS.get(candidate.method)
        display_name = blurb.display_name if blurb else candidate.method
        radio = "●" if is_selected else "○"
        radio_color = "var(--tl-tangerine)" if is_selected else "var(--tl-slate)"
        score_pct = int(candidate.score * 100)
        score_color = "var(--tl-slate)" if candidate.score > 0 else "#CBD5E1"

        col_name, col_score, col_btn = st.columns([3, 1, 1], gap="small")
        with col_name:
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:.5rem;padding:.4rem 0;'>"
                f"<span style='color:{radio_color};font-size:1rem;'>{radio}</span>"
                f"<span style='font-size:.9rem;font-weight:{'600' if is_selected else '400'};'>"
                f"{display_name}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with col_score:
            st.markdown(
                f"<div style='font-size:.8rem;color:{score_color};padding:.55rem 0;'>"
                f"{score_pct}% match</div>",
                unsafe_allow_html=True,
            )
        with col_btn:
            if not is_selected:
                if st.button(
                    "Select",
                    key=f"override_pick_{i}",
                    use_container_width=True,
                ):
                    new_selection = i

    return new_selection


# ── Backward-compat wrappers (used if any old code calls them) ──

def render_method_card(method_name: str, rationale: str, *, voice: Voice = "plain") -> None:
    """Legacy single-card render. Delegates to a minimal card display."""
    blurb_entry = METHOD_BLURBS.get(method_name)
    title = blurb_entry.display_name if blurb_entry else method_name
    default_blurb = (blurb_entry.plain if voice == "plain" else blurb_entry.technical) if blurb_entry else rationale
    blurb = rationale or default_blurb
    eyebrow = copy.step2_method_card_eyebrow(voice)

    st.markdown(
        f"""
        <div class="tl-card" style="padding:2rem 2rem 1.5rem;">
          <div style="font-size:.75rem;text-transform:uppercase;letter-spacing:.1em;
                      color:var(--tl-tangerine);font-weight:600;">
            {eyebrow}
          </div>
          <h2 class="tl-card-title" style="font-size:1.5rem !important;">{title}</h2>
          <p class="tl-text-ink" style="max-width:70ch;line-height:1.6;margin:0;">
            {blurb}
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alternatives(*, voice: Voice = "plain") -> None:
    """Legacy static table. Kept for backward compat but no longer used in
    the main flow."""
    label = copy.step2_alternatives_link(voice)
    with st.expander(label, expanded=False):
        rows = [
            {
                "Method": "A/B Test",
                "Use when": "You randomised assignment yourself.",
                "Strength": "Causal claims with minimal assumptions.",
                "Watch out for": "SRM, multiple metrics inflating false-positive rate.",
            },
            {
                "Method": "Bayesian A/B (NumPyro)",
                "Use when": "You want probability of being better, not p-values.",
                "Strength": "Direct probability statements; ROPE checks.",
                "Watch out for": "Slower fits; needs prior choice.",
            },
            {
                "Method": "Time-Series Intervention",
                "Use when": "Single series with a known change date.",
                "Strength": "Works without a control group.",
                "Watch out for": "Concurrent confounding (other launches).",
            },
            {
                "Method": "Causal Inference (DML)",
                "Use when": "No randomisation; observed confounders.",
                "Strength": "Recovers ATE under no-unmeasured-confounders.",
                "Watch out for": "Hidden confounders break identification.",
            },
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
