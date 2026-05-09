"""Inline 'Why this?' explainer for technical terms.

`term_label(key, voice="plain")` renders the term with an info dot. Hovering
the dot shows the one-line description (a native browser tooltip, since
Streamlit's popovers can't be inlined into arbitrary markdown). The full
glossary entry is exposed through `explainer_drawer(key)` which renders an
expander with the long description.

This is intentionally lightweight: Phase C may upgrade to a custom React
popover, but for Phase B a styled span with `title` + a companion expander
already hits the goal — a user who wonders 'what's this?' has the answer
within reach without leaving the screen.
"""

from __future__ import annotations

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


def term_label(key: str, *, voice: Voice = "plain") -> str:
    """Return an HTML snippet rendering the glossary term with an info dot.

    Use inside `st.markdown(..., unsafe_allow_html=True)`. In Plain voice the
    rendered surface is the plain-language synonym (when one exists); in
    Technical voice it's the canonical term. Hovering surfaces the short blurb.
    """
    entry = GLOSSARY.get(key)
    if entry is None:
        return key
    surface = entry.plain_synonym if (voice == "plain" and entry.plain_synonym) else entry.term
    title = entry.short.replace('"', "&quot;")
    return (
        f'<span class="tl-term" title="{title}" '
        f'style="border-bottom:1px dotted var(--tl-slate-soft);cursor:help;">'
        f"{surface}"
        f'<span style="color:var(--tl-slate-soft);margin-left:4px;">{_DOT_SVG}</span>'
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
        if entry.plain_synonym:
            st.caption(f"In plain words: *{entry.plain_synonym}*")
        st.write(entry.description)


def helper_caption(text: str) -> None:
    """A muted caption used alongside form controls to teach a concept inline.
    Centralised here so the styling stays consistent."""
    st.markdown(
        f'<div style="color:var(--tl-slate);font-size:0.85rem;margin:-8px 0 12px 2px;">{text}</div>',
        unsafe_allow_html=True,
    )
