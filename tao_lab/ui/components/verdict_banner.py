"""Python wrapper for the React `VerdictBanner` custom component."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import streamlit as st
import streamlit.components.v1 as components


_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist" / "verdict"

_component = components.declare_component(
    "taolab_verdict",
    path=str(_FRONTEND_DIST),
)


VerdictState = Literal["ship", "hold", "dont_ship"]


def render_verdict(
    state: VerdictState,
    headline: str,
    subtitle: Optional[str] = None,
    *,
    key: Optional[str] = None,
) -> None:
    if not (_FRONTEND_DIST / "index.html").exists():
        _render_fallback(state, headline, subtitle)
        return
    _component(
        state=state,
        headline=headline,
        subtitle=subtitle,
        default=None,
        key=key or f"taolab_verdict_{state}",
    )


_FALLBACK_STYLES = {
    "ship": ("#059669", "Ship it."),
    "hold": ("#D97706", "Hold."),
    "dont_ship": ("#DC2626", "Don't ship."),
}


def _render_fallback(state: VerdictState, headline: str, subtitle: Optional[str]) -> None:
    color, label = _FALLBACK_STYLES.get(state, ("#475569", state))
    sub_html = (
        f"<div style='margin-top:.5rem;color:var(--tl-slate);font-size:.9rem;'>{subtitle}</div>"
        if subtitle else ""
    )
    st.markdown(
        f"""
        <div class="tl-card" style="border-left:4px solid {color};">
          <div style="font-size:1.4rem;font-weight:600;color:{color};">{label}</div>
          <div style="margin-top:.4rem;color:var(--tl-indigo-ink);">{headline}</div>
          {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
