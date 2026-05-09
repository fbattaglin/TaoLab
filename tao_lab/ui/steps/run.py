"""Step 4 — Run.

Executes the chosen method against the captured config and stashes
`(result, narration, method_visuals)` on the wizard state. Phase A keeps
the existing `st.status(...)` progress UX; Phase C replaces it with a
gradient progress animation.

The fitted method object is needed in Step 5 for `visualize(result)`. We
recreate it from the chosen method name there to avoid pickling JAX/Pydantic
models into `st.session_state`.
"""

from __future__ import annotations

import streamlit as st

from tao_lab.interpret.narrator import build_prescription, render_markdown
from tao_lab.ui import state as wstate


def render() -> None:
    s = wstate.get_state()
    if s.config is None or s.df is None:
        st.info("Complete configuration first.")
        return

    if s.result is None:
        _execute(s)
        # After execution, advance to the prescription on the next rerun.
        if s.result is not None:
            wstate.advance()
            return

    # Re-entry: result already cached. Offer to navigate forward.
    st.success("Analysis complete.")
    if st.button("View Prescription →", type="primary"):
        wstate.advance()
    if st.button("← Back to Configure"):
        wstate.go_back()


def _execute(s: wstate.WizardState) -> None:
    method = _build_method(s)
    if method is None:
        st.error(
            f"Method '{s.chosen_method}' is not implemented; cannot run analysis."
        )
        return

    with st.status("Analyzing experiment...") as status:
        st.write("Running statistical tests...")
        result = method.fit(s.df, s.config)

        st.write("Building prescription...")
        prescription = build_prescription(result)

        st.write("Rendering diagnostics...")
        try:
            visuals = method.visualize(result)
        except Exception:  # noqa: BLE001
            visuals = []

        status.update(label="Analysis Complete!", state="complete")

    s.result = result
    s.prescription = prescription
    # Keep the legacy markdown narration for any back-compat call paths.
    s.narration = render_markdown(prescription, voice=s.voice)
    s.method_visuals = visuals


def _build_method(s: wstate.WizardState):
    method = s.chosen_method
    if method == "A/B Test":
        if s.engine == "Frequentist":
            from tao_lab.methods.ab_test import FrequentistABTest
            return FrequentistABTest()
        from tao_lab.methods.bayesian_ab import BayesianABTest
        return BayesianABTest()
    if method == "Time-Series Intervention":
        from tao_lab.methods.time_series import TimeSeriesIntervention
        return TimeSeriesIntervention()
    if method == "Causal Inference":
        from tao_lab.methods.causal_inference import CausalInference
        return CausalInference()
    return None
