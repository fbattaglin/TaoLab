"""Python wrapper for the React `Stepper` custom component.

The component is built by `tao_lab/ui/frontend/` (vite + react + tailwind) and
served from `dist/stepper/index.html`. It receives a list of `{index, label,
status}` descriptors and returns the index of any clicked step (or `None`).

Phase D fix: the React component now sends ``{step, ts}`` on each click so
Python can distinguish fresh clicks from stale persisted values that Streamlit
re-sends on every rerun.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

from tao_lab.ui.state import WizardState, steps_status


_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist" / "stepper"

_component = components.declare_component(
    "taolab_stepper",
    path=str(_FRONTEND_DIST),
)

_CLICK_TS_KEY = "_tl_stepper_click_ts"


def render_stepper(state: WizardState, *, clickable: bool = True) -> Optional[int]:
    """Render the stepper. Returns a step index if the user *just* clicked one,
    else ``None``.

    Falls back to a CSS-only stepper if the build artefact is missing — keeps
    the dev loop usable when someone forgets to run ``npm run build``.
    """
    if not (_FRONTEND_DIST / "index.html").exists():
        return _render_fallback(state)

    from tao_lab.ui.theme import get_theme_variables
    theme_vars = get_theme_variables()

    raw = _component(
        steps=steps_status(state),
        clickable=clickable,
        theme_vars=theme_vars,
        default=None,
        key="taolab_stepper",
    )

    if raw is None:
        return None

    # ── Distinguish fresh clicks from stale persisted values ──
    # The React component sends {step: int, ts: float} on each click.
    # Streamlit re-sends the last value on every rerun, so we compare the
    # timestamp to detect whether this is a NEW click.
    if isinstance(raw, dict):
        step = raw.get("step")
        ts = raw.get("ts")
        prev_ts = st.session_state.get(_CLICK_TS_KEY)
        if ts is not None and ts != prev_ts:
            st.session_state[_CLICK_TS_KEY] = ts
            return int(step) if step is not None else None
        return None  # stale persisted value — ignore

    # Legacy fallback: raw is an int (old build without timestamps)
    return int(raw)


def _render_fallback(state: WizardState) -> None:
    parts = ['<nav class="tl-stepper-fallback">']
    for s in steps_status(state):
        cls = "tl-stepper-fallback__item"
        if s["status"] == "active":
            cls += " tl-stepper-fallback__item--active"
        elif s["status"] == "done":
            cls += " tl-stepper-fallback__item--done"
        parts.append(f'<span class="{cls}">{s["index"]}. {s["label"]}</span>')
    parts.append("</nav>")
    st.markdown("".join(parts), unsafe_allow_html=True)
    return None
