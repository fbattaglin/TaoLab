"""Step 5 — Prescription.

Phase C: the deliverable.

Layout:
  Verdict banner (React)
  Prescription card (React)
  Forest plot (Plotly, design-system colours)
  Per-metric detail rows with progressive disclosure
  Method-specific extra visuals (e.g. Bayesian posteriors) in an expander
  Reproducibility section
  Sidebar action panel: voice toggle, exports (PDF, Markdown, YAML), Run-again

The verdict banner and prescription card receive whichever voice is set on
the wizard state — toggling rebuilds args without re-running the analysis.
"""

from __future__ import annotations

import streamlit as st

from tao_lab.interpret.narrator import render_markdown
from tao_lab.ui import state as wstate
from tao_lab.ui.components.exports import to_markdown, to_pdf_bytes, to_yaml_config
from tao_lab.ui.components.forest_plot import render_forest_plot
from tao_lab.ui.components.metric_detail import render_metric_details
from tao_lab.ui.components.prescription_card import render_prescription
from tao_lab.ui.components.verdict_banner import render_verdict


_CONFIDENCE_LABEL = {
    "strong": "Strong evidence",
    "moderate": "Moderate evidence",
    "weak": "Weak evidence",
    "none": "No evidence",
}


def render() -> None:
    s = wstate.get_state()
    if s.result is None or s.prescription is None:
        st.info("No analysis result yet.")
        return

    voice = s.voice
    result = s.result
    p = s.prescription

    # ── Top action bar: SRM badge + exports inline ──
    _render_action_bar(s)

    # ── Verdict ──
    headline = p.headline.plain if voice == "plain" else p.headline.technical
    subtitle = (
        f"{_CONFIDENCE_LABEL[p.confidence]} · "
        f"{int(p.confidence_score * 100)}/100 confidence"
    )
    render_verdict(state=p.verdict, headline=headline, subtitle=subtitle, key="verdict_main")

    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)

    # ── Prescription card ──
    render_prescription(p, voice=voice, key="prescription_main")

    st.markdown("<hr class='tl-divider'>", unsafe_allow_html=True)

    # ── Forest plot ──
    if result.metrics:
        st.markdown(
            "<div style='font-weight:500;margin:0 0 .5rem;color:var(--tl-indigo-deep);'>"
            "Lift overview"
            "</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(render_forest_plot(result), use_container_width=True)

    # ── Per-metric detail rows ──
    st.markdown(
        "<div style='font-weight:500;margin:1rem 0 .5rem;color:var(--tl-indigo-deep);'>"
        "Per-metric breakdown"
        "</div>",
        unsafe_allow_html=True,
    )
    render_metric_details(result)

    # ── Method-specific extra visuals (Bayesian posteriors, causal diagnostics, …) ──
    if s.method_visuals:
        with st.expander("Method-specific diagnostics", expanded=False):
            for fig in s.method_visuals:
                st.plotly_chart(fig, use_container_width=True)

    # ── Reproducibility ──
    with st.expander("Reproducibility config", expanded=False):
        st.code(to_yaml_config(result), language="yaml")

    st.markdown("<hr class='tl-divider'>", unsafe_allow_html=True)

    # ── Footer nav ──
    nav_a, nav_b, nav_c = st.columns([1, 1, 2])
    with nav_a:
        if st.button("← Back", key="rx_back", use_container_width=True):
            wstate.go_back()
    with nav_b:
        if st.button("Run again", key="rx_run_again", use_container_width=True):
            s.result = None
            s.prescription = None
            s.narration = None
            s.method_visuals = []
            wstate.goto(wstate.STEP_CONFIGURE)
    with nav_c:
        if st.button("Start over", key="rx_start_over", use_container_width=True):
            wstate.reset_state()
            st.rerun()


# ─────────────────────────── Action bar (inline) ───────────────────────────
def _render_action_bar(s: wstate.WizardState) -> None:
    """Inline action bar above the verdict: SRM status badge + three export
    buttons. Inline beats a sidebar here because business users don't always
    know to look for the sidebar collapse handle."""
    result = s.result
    badge_color = "var(--tl-danger)" if result.srm_detected else "var(--tl-success)"
    badge_text = (
        f"⚠ SRM detected · p = {result.srm_p_value:.4g}"
        if result.srm_detected
        else f"✓ SRM passed · p = {result.srm_p_value:.4g}"
    )
    method_label = result.method_name

    head_a, head_b = st.columns([3, 4])
    with head_a:
        st.markdown(
            f"""
            <div style="display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;">
              <div style="font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;
                          color:var(--tl-slate);font-weight:600;">{method_label}</div>
              <div style="color:{badge_color};font-size:.85rem;font-weight:500;">{badge_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with head_b:
        b1, b2, b3 = st.columns(3)
        md = to_markdown(s.result, s.prescription, voice=s.voice)
        with b1:
            st.download_button(
                "Markdown",
                data=md,
                file_name="tao_lab_prescription.md",
                mime="text/markdown",
                use_container_width=True,
                key="exp_md",
            )
        pdf_bytes = to_pdf_bytes(s.result, s.prescription, voice=s.voice)
        with b2:
            if pdf_bytes is not None:
                st.download_button(
                    "PDF",
                    data=pdf_bytes,
                    file_name="tao_lab_prescription.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="exp_pdf",
                )
            else:
                st.button(
                    "PDF (install WeasyPrint)",
                    disabled=True,
                    use_container_width=True,
                    help=(
                        "PDF export needs WeasyPrint. "
                        "Install with `uv pip install 'tao-lab[report]'`."
                    ),
                    key="exp_pdf_disabled",
                )
        with b3:
            st.download_button(
                "YAML",
                data=to_yaml_config(s.result),
                file_name="tao_lab_config.yaml",
                mime="text/yaml",
                use_container_width=True,
                key="exp_yaml",
            )
