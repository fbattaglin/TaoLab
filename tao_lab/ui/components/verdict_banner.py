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
    
    from tao_lab.ui.theme import get_theme_variables
    theme_vars = get_theme_variables()

    _component(
        state=state,
        headline=headline,
        subtitle=subtitle,
        theme_vars=theme_vars,
        default=None,
        key=key or f"taolab_verdict_{state}",
    )


_FALLBACK_STYLES = {
    "ship": ("#059669", "Ship it.", "M9 12.75 11.25 15 15 9.75"),
    "hold": ("#D97706", "Hold.", "M10 9v6m4-6v6"),
    "dont_ship": ("#DC2626", "Don't ship.", "M18.364 5.636l-12.728 12.728M5.636 5.636l12.728 12.728"),
}

# Minimal SVG icon paths (24×24 viewBox, stroke-based, matching Lucide style):
#   ship    → checkmark (M9 12.75 11.25 15 15 9.75)
#   hold    → pause bars (M10 9v6m4-6v6)
#   dont_ship → X cross (two diagonal lines)


def _render_fallback(state: VerdictState, headline: str, subtitle: Optional[str]) -> None:
    color, label, icon_path = _FALLBACK_STYLES.get(state, ("#475569", state, ""))
    sub_html = (
        f"<div style='margin-top:.5rem;color:var(--tl-slate);font-size:.9rem;'>{subtitle}</div>"
        if subtitle else ""
    )
    icon_html = (
        f"<div style='flex:none;width:3rem;height:3rem;border-radius:50%;"
        f"background:{color}12;display:flex;align-items:center;justify-content:center;'>"
        f"<svg width='24' height='24' viewBox='0 0 24 24' fill='none' "
        f"stroke='{color}' stroke-width='2.25' stroke-linecap='round' stroke-linejoin='round'>"
        f"<circle cx='12' cy='12' r='10' stroke-width='1.5' opacity='.35'/>"
        f"<path d='{icon_path}'/>"
        f"</svg></div>"
    ) if icon_path else ""
    st.markdown(
        f"""
        <div class="tl-card" style="border-left:4px solid {color};display:flex;align-items:flex-start;gap:1.1rem;">
          {icon_html}
          <div style="min-width:0;">
            <div style="font-size:1.4rem;font-weight:600;color:{color};">{label}</div>
            <div style="margin-top:.4rem;color:var(--tl-indigo-ink);">{headline}</div>
            {sub_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
