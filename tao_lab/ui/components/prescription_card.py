"""Python wrapper for the React `PrescriptionCard` custom component.

Receives a `PrescriptionNarration` plus a voice and forwards the appropriate
text fields to the React side. The card is the hero deliverable of Step 5;
this wrapper exists only to bridge typed Pydantic data into the JS args.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import streamlit as st
import streamlit.components.v1 as components

from tao_lab.interpret.narrator import PrescriptionNarration


_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist" / "prescription"

_component = components.declare_component(
    "taolab_prescription",
    path=str(_FRONTEND_DIST),
)


Voice = Literal["plain", "technical"]


def render_prescription(
    narration: PrescriptionNarration,
    *,
    voice: Voice = "plain",
    key: Optional[str] = None,
) -> None:
    """Render the prescription card. Falls back to a Streamlit-only layout if
    the React build artefact is missing — the dev workflow stays usable when
    someone forgets to build the frontend."""
    args = _build_args(narration, voice=voice)

    if not (_FRONTEND_DIST / "index.html").exists():
        _render_fallback(args)
        return
    _component(
        diagnosis=args["diagnosis"],
        recommendation=args["recommendation"],
        reasoning=args["reasoning"],
        confidenceLabel=args["confidenceLabel"],
        confidenceScore=args["confidenceScore"],
        caveats=args["caveats"],
        nextSteps=args["nextSteps"],
        default=None,
        key=key or "taolab_prescription",
    )


def _build_args(narration: PrescriptionNarration, *, voice: Voice) -> dict:
    pick = (lambda pair: pair.plain) if voice == "plain" else (lambda pair: pair.technical)
    next_steps = (
        narration.next_steps_plain if voice == "plain" else narration.next_steps_technical
    )
    return {
        "diagnosis": pick(narration.diagnosis),
        "recommendation": pick(narration.recommendation),
        "reasoning": pick(narration.reasoning),
        "confidenceLabel": narration.confidence,
        "confidenceScore": float(narration.confidence_score),
        "caveats": [
            {
                "severity": c.severity,
                "title": c.title,
                "body": c.body_plain if voice == "plain" else c.body_technical,
            }
            for c in narration.caveats
        ],
        "nextSteps": list(next_steps),
    }


# ─────────────────────────── Fallback ───────────────────────────
def _render_fallback(args: dict) -> None:
    st.markdown(
        f"""
        <div class="tl-card" style="padding:1.75rem 2rem;">
          <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.18em;
                      color:var(--tl-tangerine);font-weight:700;">Prescription</div>
          <div style="margin-top:.5rem;font-weight:600;color:var(--tl-slate);">Diagnosis</div>
          <div>{args['diagnosis']}</div>
          <div style="margin-top:1rem;font-weight:600;color:var(--tl-slate);">Recommendation</div>
          <div>{args['recommendation']}</div>
          <div style="margin-top:1rem;font-weight:600;color:var(--tl-slate);">Reasoning</div>
          <div style="color:var(--tl-slate);">{args['reasoning']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if args["caveats"]:
        st.markdown("**Caveats**")
        for c in args["caveats"]:
            st.markdown(f"- **{c['title']}** — {c['body']}")
    if args["nextSteps"]:
        st.markdown("**Next steps**")
        for ns in args["nextSteps"]:
            st.markdown(f"- {ns}")
