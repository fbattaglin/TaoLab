"""Wizard state machine for the 5-step Tao Lab v2 flow.

The flow:  Data → Diagnose → Configure → Run → Prescription.

`current_step` is the only step the user sees rendered. They may navigate back
to any *completed* step but cannot jump forward; advancing requires the
preceding step to be `completed` (typically by the step writer setting the
relevant payload — `df`, `diagnosis`, `config`, `result`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import polars as pl
import streamlit as st

from tao_lab.diagnose.engine import DiagnosisReport
from tao_lab.interpret.narrator import PrescriptionNarration
from tao_lab.methods.base import AnalysisResult, BanditReplayResult, ExperimentConfig


STEP_DATA = 1
STEP_DIAGNOSE = 2
STEP_CONFIGURE = 3
STEP_RUN = 4
STEP_PRESCRIPTION = 5

STEP_LABELS = {
    STEP_DATA: "Data",
    STEP_DIAGNOSE: "Diagnose",
    STEP_CONFIGURE: "Configure",
    STEP_RUN: "Run",
    STEP_PRESCRIPTION: "Prescription",
}


@dataclass
class WizardState:
    """Mutable session state, lifted out of `st.session_state` for typing."""

    current_step: int = STEP_DATA

    # Step 1 — Data
    df: Optional[pl.DataFrame] = None
    file_name: Optional[str] = None
    business_question: Optional[str] = None  # free-form question, shown in report

    # Step 2 — Diagnose
    diagnosis: Optional[DiagnosisReport] = None
    selected_candidate_idx: int = 0  # index into diagnosis.candidates

    # Step 3 — Configure
    config: Optional[ExperimentConfig] = None
    engine: str = "Frequentist"  # Frequentist | Bayesian (NumPyro)
    chosen_method: Optional[str] = None  # mirrors DiagnosisReport.suggested_method

    # Step 4 — Run
    result: Optional[AnalysisResult] = None
    narration: Optional[str] = None  # legacy markdown render, kept for back-compat
    prescription: Optional[PrescriptionNarration] = None
    method_visuals: list[Any] = field(default_factory=list)
    bandit_replay: Optional[BanditReplayResult] = None  # MAB regret simulation

    # Cross-cutting (Phase B/C will use this — kept here for forward compat)
    voice: str = "plain"  # plain | technical

    # Dataset-specific hints (populated when a sample chip is loaded)
    # Keys: "intervention_date" (ISO str), "intervention_label" (display str), etc.
    dataset_hints: dict = field(default_factory=dict)

    def clear_results(self) -> None:
        """Clear all analysis artifacts. Call this when configuration changes."""
        self.result = None
        self.narration = None
        self.prescription = None
        self.method_visuals = []
        self.bandit_replay = None


_STATE_KEY = "tl_state"


def get_state() -> WizardState:
    """Return the singleton wizard state, creating it on first call."""
    if _STATE_KEY not in st.session_state:
        st.session_state[_STATE_KEY] = WizardState()
    return st.session_state[_STATE_KEY]


def reset_state() -> None:
    """Clear all wizard state — used by 'Start over' affordances."""
    st.session_state[_STATE_KEY] = WizardState()


def goto(step: int) -> None:
    """Navigate to a specific step. Bounded to [1, 5]; never advances past
    the furthest reachable step. Triggers a rerun."""
    state = get_state()
    target = max(STEP_DATA, min(STEP_PRESCRIPTION, step))
    if target > _max_reachable(state):
        return
    state.current_step = target
    st.rerun()


def advance() -> None:
    """Move to the next step if reachable."""
    state = get_state()
    if state.current_step < _max_reachable(state):
        goto(state.current_step + 1)


def go_back() -> None:
    """Move to the previous step (if any)."""
    state = get_state()
    if state.current_step > STEP_DATA:
        goto(state.current_step - 1)


def _max_reachable(state: WizardState) -> int:
    """Highest step the user is allowed to view, given the data they've supplied."""
    if state.df is None:
        return STEP_DATA
    if state.diagnosis is None:
        return STEP_DIAGNOSE
    if state.config is None:
        return STEP_CONFIGURE
    if state.result is None:
        return STEP_RUN
    return STEP_PRESCRIPTION


def steps_status(state: WizardState) -> list[dict]:
    """Render-friendly view: one entry per step with `label`, `status`, `index`."""
    reachable = _max_reachable(state)
    out = []
    for idx, label in STEP_LABELS.items():
        if idx < state.current_step:
            status = "done"
        elif idx == state.current_step:
            status = "active"
        elif idx <= reachable:
            status = "available"
        else:
            status = "locked"
        out.append({"index": idx, "label": label, "status": status})
    return out
