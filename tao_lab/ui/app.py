"""Tao Lab v2 — application shell.

Responsibilities:
  1. Page config + global theme injection.
  2. Render the 5-step Stepper at the top of every screen.
  3. Route to the active step's renderer.

All step content lives in `tao_lab/ui/steps/`; cross-cutting state lives in
`tao_lab/ui/state.py`. The router stays deliberately small so phases B and C
can iterate on individual steps without touching this file.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from tao_lab.ui import state as wstate
from tao_lab.ui.components.stepper import render_stepper
from tao_lab.ui.steps import configure as step_configure
from tao_lab.ui.steps import data as step_data
from tao_lab.ui.steps import diagnose as step_diagnose
from tao_lab.ui.steps import prescription as step_prescription
from tao_lab.ui.steps import run as step_run
from tao_lab.ui.theme import inject_theme

# Resolve logo path relative to this file so it works from any working directory.
_LOGO = Path(__file__).parent / "static" / "tao_lab_logo.png"

# ───── Page setup ─────
st.set_page_config(
    page_title="Tao Lab",
    page_icon=str(_LOGO),
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_theme()

# ───── Native Streamlit logo (sidebar + collapsed-sidebar icon) ─────
st.logo(str(_LOGO))

# ───── Header ─────
state = wstate.get_state()

header_left, header_right = st.columns([3, 1])
with header_left:
    st.image(str(_LOGO), width=148)
with header_right:
    voice_choice = st.radio(
        "Reader",
        options=("Signal", "Spectrum"),
        index=0 if state.voice == "signal" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="tl_voice_radio",
        help=(
            "Signal: The Boardroom perspective. Clear verdicts and business impact. "
            "Spectrum: The Lab perspective. Full statistical rigor and diagnostic depth."
        ),
    )
    new_voice = "signal" if voice_choice == "Signal" else "spectrum"
    if new_voice != state.voice:
        state.voice = new_voice
        st.rerun()

# ───── Stepper ─────
clicked = render_stepper(state)
if clicked is not None and clicked != state.current_step:
    wstate.goto(int(clicked))

# ───── Router ─────
ROUTES = {
    wstate.STEP_DATA: step_data.render,
    wstate.STEP_DIAGNOSE: step_diagnose.render,
    wstate.STEP_CONFIGURE: step_configure.render,
    wstate.STEP_RUN: step_run.render,
    wstate.STEP_PRESCRIPTION: step_prescription.render,
}

ROUTES[state.current_step]()
