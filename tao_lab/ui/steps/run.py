"""Step 4 — Run.

Executes the chosen method against the captured config and stashes
`(result, narration, method_visuals)` on the wizard state.

Phase 4: progressive, voice-aware check descriptions with plain-language
results after each step.
"""

from __future__ import annotations

import streamlit as st

from tao_lab.interpret.narrator import build_prescription, render_markdown
from tao_lab.ui import state as wstate
from tao_lab.ui.strings import Voice, copy


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

    voice: Voice = s.voice

    with st.status(copy.step4_title(voice)) as status:
        # ── Show HTE progress hint before fit (if enabled) ──
        if s.config and s.config.method_params.get("hte_enabled"):
            st.write(copy.step4_progress_fit(voice))
            st.write(copy.step4_progress_hte(voice))
        else:
            st.write(copy.step4_progress_fit(voice))
        result = method.fit(s.df, s.config)

        # ── SRM check result (plain-language) ──
        _show_srm_result(result, voice)

        # ── Fit result summary ──
        n_sig = sum(1 for m in result.metrics if m.is_significant)
        if voice == "plain":
            st.write(
                f"✓ Effect estimated across {len(result.metrics)} "
                f"metric{'s' if len(result.metrics) != 1 else ''}"
            )
        else:
            st.write(
                f"✓ {result.method_name} completed, "
                f"{len(result.metrics)} metric{'s' if len(result.metrics) != 1 else ''}, "
                f"{n_sig} significant"
            )

        st.write(copy.step4_progress_narrate(voice))
        prescription = build_prescription(result)

        st.write(copy.step4_progress_viz(voice))
        try:
            visuals = method.visualize(result)
        except Exception:  # noqa: BLE001
            visuals = []

        if voice == "plain":
            status.update(label="Analysis complete!", state="complete")
        else:
            status.update(label="Analysis Complete!", state="complete")

    s.result = result
    s.prescription = prescription
    # Keep the legacy markdown narration for any back-compat call paths.
    s.narration = render_markdown(prescription, voice=s.voice)
    s.method_visuals = visuals


def _show_srm_result(result, voice: Voice) -> None:
    """Show a one-line SRM result after the fit."""
    if result.srm_detected:
        if voice == "plain":
            st.write(
                f"⚠ {copy.step5_srm_fail(voice)} — "
                f"this usually points to a bug upstream"
            )
        else:
            st.write(
                f"⚠ {copy.step5_srm_fail(voice)} · p = {result.srm_p_value:.4g}"
            )
    else:
        if voice == "plain":
            st.write(f"✓ {copy.step5_srm_pass(voice)}")
        else:
            st.write(
                f"✓ {copy.step5_srm_pass(voice)} · p = {result.srm_p_value:.4g}"
            )


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
