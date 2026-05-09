"""Design tokens and global theme injection for Tao Lab v2.

The single source of truth for colors, typography, spacing, and shadow tokens.
Forced Light Mode to ensure consistency across systems.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import streamlit as st


TOKENS = {
    "color": {
        "indigo_deep": "#1E3A5F",
        "indigo_ink": "#0F172A",
        "slate": "#334155",
        "slate_soft": "#64748B",
        "tangerine": "#F97316",
        "tangerine_soft": "#FFF7ED",
        "mist": "#F8FAFC",
        "cloud": "#FFFFFF",
        "hairline": "#E2E8F0",
        "success": "#059669",
        "warning": "#D97706",
        "danger": "#DC2626",
    },
    "radius": {
        "card": "12px",
        "control": "8px",
        "pill": "999px",
    },
    "shadow": {
        "card": "0 1px 3px rgba(15, 23, 42, 0.04)",
        "lifted": "0 4px 12px rgba(15, 23, 42, 0.06)",
    },
    "font": {
        "sans": '-apple-system, "Inter", "Söhne", system-ui, sans-serif',
        "mono": 'ui-monospace, "SF Mono", Menlo, monospace',
    },
    "max_content_width": "960px",
}


_STYLE_PATH = Path(__file__).parent / "static" / "style.css"


def inject_theme() -> None:
    """Inject the global stylesheet. Call once at the top of `app.py`."""
    css = _STYLE_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def get_theme_variables(theme: Optional[str] = None) -> str:
    """Return the CSS variable declarations for the forced Light Mode."""
    return (
        "--tl-mist: #F8FAFC; "
        "--tl-cloud: #FFFFFF; "
        "--tl-indigo-ink: #0F172A; "
        "--tl-indigo-deep: #1E3A5F; "
        "--tl-hairline: #E2E8F0; "
        "--tl-slate: #334155; "
        "--tl-slate-soft: #64748B; "
        "--tl-tangerine-soft: #FFF7ED; "
        "--tl-shadow-card: 0 1px 3px rgba(15, 23, 42, 0.04); "
        "--tl-shadow-lifted: 0 4px 12px rgba(15, 23, 42, 0.06);"
    )


__all__ = ["TOKENS", "inject_theme", "get_theme_variables"]
