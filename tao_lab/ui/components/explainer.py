"""Inline explainers, first-use hints, and concept drawers.

Three helpers, from lightest to richest:

1. **`term_label(key, voice)`** — renders a term with an info dot + tooltip.
   Use inside ``st.markdown(..., unsafe_allow_html=True)``.

2. **`term_with_hint(key, voice, step)`** — like ``term_label`` but shows the
   ``first_use`` hint the first time the term appears on a given step.
   Subsequent renders on the same step omit the hint and fall back to
   tooltip-only. Uses ``st.session_state`` for tracking.

3. **`concept_drawer(key, data_context)`** — an enhanced ``st.expander`` with
   signal explanation, spectrum anchor, "when to use / avoid" pairs, optional
   worked example from the user's data, and a citation link.

Plus:

- **`explainer_drawer(key)`** — lighter version of `concept_drawer` (original).
- **`helper_caption(text)`** — muted caption used alongside form controls.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from tao_lab.ui.strings import GLOSSARY, Voice


_DOT_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" '
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;">'
    '<circle cx="12" cy="12" r="10"></circle>'
    '<path d="M12 16v-4"></path><path d="M12 8h.01"></path>'
    "</svg>"
)

_SEEN_KEY_PREFIX = "_tl_seen_terms_"


def term_label(key: str, *, voice: Voice = "signal") -> str:
    """Return an HTML snippet rendering the glossary term with an info dot.

    Use inside `st.markdown(..., unsafe_allow_html=True)`. In Signal voice the
    rendered surface is the signal-language synonym (when one exists); in
    Spectrum voice it's the canonical term. Hovering surfaces the short blurb.
    """
    entry = GLOSSARY.get(key)
    if entry is None:
        return key
    surface = entry.signal_synonym if (voice == "signal" and entry.signal_synonym) else entry.term
    title = entry.short.replace('"', "&quot;")
    return (
        f'<span class="tl-term" title="{title}" '
        f'style="border-bottom:1px dotted var(--tl-slate-soft);cursor:help;">'
        f"{surface}"
        f'<span style="color:var(--tl-slate-soft);margin-left:4px;">{_DOT_SVG}</span>'
        f"</span>"
    )


def term_with_hint(key: str, *, voice: Voice = "signal", step: int = 0) -> str:
    """Return a term label with a first-use hint.

    On the first call for a given ``key`` + ``step`` combination within the
    session, the ``first_use`` hint text from the glossary is appended as a
    styled italic span. Subsequent calls for the same key on the same step
    return the plain ``term_label`` (tooltip only), avoiding repetition.

    If the glossary entry has no ``first_use`` text, falls back to
    ``term_label`` always.
    """
    entry = GLOSSARY.get(key)
    if entry is None:
        return key

    base_label = term_label(key, voice=voice)

    # No first_use text → always just the term
    if not entry.first_use:
        return base_label

    # Track seen terms per step
    state_key = f"{_SEEN_KEY_PREFIX}{step}"
    seen: set = st.session_state.get(state_key, set())

    if key in seen:
        return base_label

    # Mark as seen
    seen.add(key)
    st.session_state[state_key] = seen

    # Append the first-use hint
    return (
        f'{base_label}'
        f'<span class="tl-text-slate" style="font-style:italic;font-size:.85em;'
        f'margin-left:6px;">'
        f"— {entry.first_use}"
        f"</span>"
    )


def explainer_drawer(key: str) -> None:
    """Render an expander with the long-form glossary entry. Use sparingly —
    only where a parameter has a one-time educational moment (e.g. next to
    the α slider in advanced settings)."""
    entry = GLOSSARY.get(key)
    if entry is None:
        return
    with st.expander(f"What is {entry.term}?", expanded=False):
        if entry.signal_synonym:
            st.caption(f"In signal words: *{entry.signal_synonym}*")
        st.write(entry.description)
        if entry.learn_more:
            st.caption(f"Reference: {entry.learn_more}")


def concept_drawer(
    key: str,
    *,
    data_context: Optional[Dict[str, Any]] = None,
    use_when: str = "",
    avoid_when: str = "",
) -> None:
    """A richer explainer with optional worked example and use/avoid guidance.

    Parameters
    ----------
    key : str
        Glossary key.
    data_context : dict, optional
        Key-value pairs from the user's actual data to build a worked example.
        The template expects keys like ``ci_lower``, ``ci_upper``, ``metric``,
        etc. — callers pass whatever is relevant.
    use_when : str
        "When you'd use this" guidance. If empty, section is omitted.
    avoid_when : str
        "When you'd avoid this" guidance. If empty, section is omitted.
    """
    entry = GLOSSARY.get(key)
    if entry is None:
        return

    with st.expander(f"What is {entry.term}?", expanded=False):
        # ── Signal explanation ──
        if entry.signal_synonym:
            st.caption(f"In signal words: *{entry.signal_synonym}*")
        st.write(entry.description)

        # ── Worked example from user data ──
        if data_context:
            example_text = _build_worked_example(key, data_context)
            if example_text:
                st.markdown(
                    f'<div style="background:var(--tl-tangerine-soft, #FFF7ED);'
                    f'border-left:3px solid var(--tl-tangerine, #F97316);'
                    f'padding:.75rem 1rem;border-radius:4px;margin:.5rem 0;'
                    f'font-size:.9rem;">'
                    f"<strong>In your data:</strong> {example_text}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # ── When to use / avoid ──
        if use_when or avoid_when:
            cols = st.columns(2)
            if use_when:
                with cols[0]:
                    st.markdown(f"**When you'd use this:** {use_when}")
            if avoid_when:
                with cols[1]:
                    st.markdown(f"**When you'd avoid this:** {avoid_when}")

        # ── Spectrum anchor / citation ──
        if entry.learn_more:
            st.caption(f"Reference: {entry.learn_more}")


def helper_caption(text: str) -> None:
    """A muted caption used alongside form controls to teach a concept inline.
    Centralised here so the styling stays consistent."""
    st.markdown(
        f'<div class="tl-text-slate" style="font-size:0.85rem;margin:-8px 0 12px 2px;">{text}</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────── Worked-example templates ───────────────────────
def _build_worked_example(key: str, ctx: Dict[str, Any]) -> str:
    """Build a context-specific worked example sentence. Returns empty string
    if the key has no template or the required context keys are missing."""
    templates = {
        "ci": (
            lambda c: (
                f"The 95% CI of [{c['ci_lower']:.2f}, {c['ci_upper']:.2f}] means the "
                f"true effect on {c.get('metric', 'the metric')} most likely falls between "
                f"those values."
            )
            if "ci_lower" in c and "ci_upper" in c
            else ""
        ),
        "p_value": (
            lambda c: (
                f"A p-value of {c['p_value']:.4g} means there's a "
                f"{c['p_value'] * 100:.1f}% chance of seeing a result this extreme "
                f"if the change had no real effect."
            )
            if "p_value" in c
            else ""
        ),
        "effect_size": (
            lambda c: (
                f"Cohen's d = {c['effect_size']:.2f} on {c.get('metric', 'the metric')} "
                f"— {'a small' if abs(c['effect_size']) < 0.3 else 'a medium' if abs(c['effect_size']) < 0.6 else 'a large'} "
                f"effect relative to the natural variation in your data."
            )
            if "effect_size" in c
            else ""
        ),
        "srm": (
            lambda c: (
                f"Your groups split {c.get('pct_control', '?')} / {c.get('pct_treatment', '?')}, "
                f"which {'is close to' if not c.get('srm_detected') else 'differs from'} the "
                f"expected split."
            )
            if "pct_control" in c
            else ""
        ),
    }
    builder = templates.get(key)
    if builder is None:
        return ""
    try:
        return builder(ctx)
    except Exception:  # noqa: BLE001
        return ""
