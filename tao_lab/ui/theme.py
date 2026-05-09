"""Design tokens and global theme injection for Tao Lab v2.

The single source of truth for colors, typography, spacing, and shadow tokens.
Mirrors the Tailwind config in `frontend/tailwind.config.js` so React custom
components and Streamlit-rendered surfaces share an identical visual language.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st


TOKENS = {
    "color": {
        "indigo_deep": "#1E3A5F",
        "indigo_ink": "#0F172A",
        "slate": "#475569",
        "slate_soft": "#94A3B8",
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


__all__ = ["TOKENS", "inject_theme"]
