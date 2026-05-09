"""Step 1 — Data.

Phase B redesign: a hero with sample-data chips for one-click loading, the
Streamlit drag-drop uploader styled into a drop zone, and a per-column health
snapshot once data is loaded.

Phase 4 additions:
* Voice-aware sample chips (plain blurbs frame the business question,
  technical blurbs show dataset specs).
* Optional "What are you trying to learn?" question field.
* Plain-language dataset summary below the column snapshot.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import polars as pl
import streamlit as st

from tao_lab.ui import state as wstate
from tao_lab.ui.components.data_health import render_data_snapshot
from tao_lab.ui.strings import Voice, copy


_DATASETS_DIR = Path(__file__).parent.parent.parent.parent / "datasets"
_LOGO = Path(__file__).parent.parent / "static" / "tao_lab_logo.png"

_SAMPLE_CHIPS = [
    {
        "key": "ab",
        "label": "E-commerce A/B test",
        "blurb_plain": "Did a website change increase revenue?",
        "blurb_technical": "10k users · revenue + CTR ratio metric",
        "scenario": "You redesigned the checkout page and randomly showed it to half your visitors.",
        "file": "ab_test_ecommerce.csv",
    },
    {
        "key": "ts",
        "label": "Marketing time-series",
        "blurb_plain": "Did a marketing campaign boost daily revenue?",
        "blurb_technical": "180 days · intervention 2023-04-15",
        "scenario": "You launched a campaign on a specific date and want to know if it moved the needle.",
        "file": "time_series_marketing.csv",
    },
    {
        "key": "ci",
        "label": "Lalonde causal",
        "blurb_plain": "Did a job training program increase earnings?",
        "blurb_technical": "Observational treatment + 7 covariates",
        "scenario": "You have data on who participated in a program but didn't randomly assign them.",
        "file": "causal_lalonde.csv",
    },
]


def render() -> None:
    s = wstate.get_state()
    voice = s.voice

    if s.df is None:
        _render_hero(s, voice=voice)
        return

    _render_loaded(s, voice=voice)


# ─────────────────────── Empty / hero state ───────────────────────
def _render_hero(s: wstate.WizardState, *, voice: Voice) -> None:
    # ── Centred brand mark ──
    _gap, logo_col, _gap2 = st.columns([2, 1, 2])
    with logo_col:
        if _LOGO.exists():
            st.image(str(_LOGO), use_container_width=True)

    st.markdown(
        f"""
        <div class="tl-hero-wash" style="text-align:center;">
          <h1 style="margin:0 auto;max-width:24ch;">{copy.step1_hero_headline(voice)}</h1>
          <p style="color:var(--tl-slate);max-width:50ch;margin:.75rem auto 0;">
            {copy.step1_hero_sub(voice)}
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Business-context primer ──
    question = st.text_input(
        copy.step1_question_label(voice),
        value=s.business_question or "",
        placeholder="e.g. Did the new checkout design increase revenue?",
        key="biz_question_input",
    )
    if question != (s.business_question or ""):
        s.business_question = question if question.strip() else None

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        copy.step1_drop_label(voice),
        type=["csv", "xlsx"],
        label_visibility="collapsed",
    )

    if uploaded is not None:
        df = _read_uploaded_file(uploaded)
        if df is not None:
            s.df = df
            s.file_name = uploaded.name
            s.diagnosis = None  # invalidate downstream state on new upload
            st.rerun()

    st.markdown(
        f"<div style='margin:1.5rem 0 .5rem;color:var(--tl-slate);'>"
        f"{copy.step1_samples_label(voice)}</div>",
        unsafe_allow_html=True,
    )

    chip_cols = st.columns(len(_SAMPLE_CHIPS))
    for slot, chip in zip(chip_cols, _SAMPLE_CHIPS):
        blurb = chip["blurb_plain"] if voice == "plain" else chip["blurb_technical"]
        with slot:
            if st.button(
                chip["label"],
                key=f"sample_chip_{chip['key']}",
                use_container_width=True,
            ):
                _load_sample(s, chip["file"])
                st.rerun()
            st.markdown(
                f"<div style='color:var(--tl-slate);font-size:.8rem;"
                f"line-height:1.4;margin-top:-6px;'>{blurb}</div>",
                unsafe_allow_html=True,
            )


def _read_uploaded_file(uploaded) -> pl.DataFrame | None:
    try:
        if uploaded.name.endswith(".csv"):
            return pl.read_csv(uploaded)
        return pl.from_pandas(pd.read_excel(uploaded))
    except Exception as e:  # noqa: BLE001
        st.error(f"Couldn't read **{uploaded.name}**: {e}")
        return None


def _load_sample(s: wstate.WizardState, filename: str) -> None:
    path = _DATASETS_DIR / filename
    if not path.exists():
        st.error(
            f"Sample dataset not found at `{path}`. "
            "Run `uv run scripts/fetch_datasets.py` first."
        )
        return
    s.df = pl.read_csv(path)
    s.file_name = filename
    s.diagnosis = None


# ─────────────────────── Loaded state ───────────────────────
def _render_loaded(s: wstate.WizardState, *, voice: Voice) -> None:
    df = s.df
    assert df is not None

    head_l, head_r = st.columns([3, 1])
    with head_l:
        st.markdown(
            f"<h1 style='margin:0;'>Your data</h1>"
            f"<div style='color:var(--tl-slate);margin-top:.25rem;'>"
            f"<strong>{s.file_name}</strong> · "
            f"{df.height:,} rows × {df.width} columns</div>",
            unsafe_allow_html=True,
        )
    with head_r:
        if st.button("Use a different file", key="data_reset", use_container_width=True):
            s.df = None
            s.file_name = None
            s.diagnosis = None
            st.rerun()

    # ── Plain-language dataset summary ──
    if voice == "plain":
        assignment_guess = _guess_assignment_col(df)
        summary = _dataset_summary(df, assignment_guess)
        st.markdown(
            f"<div style='color:var(--tl-slate);font-size:.9rem;line-height:1.5;"
            f"margin:.5rem 0;padding:.75rem 1rem;background:var(--tl-mist,#F8FAFC);"
            f"border-radius:8px;'>{summary}</div>",
            unsafe_allow_html=True,
        )
    else:
        assignment_guess = _guess_assignment_col(df)

    st.markdown("<hr class='tl-divider'>", unsafe_allow_html=True)

    render_data_snapshot(df, assignment_col=assignment_guess)

    st.markdown("<hr class='tl-divider'>", unsafe_allow_html=True)
    nav_l, nav_r = st.columns([3, 1])
    with nav_r:
        if st.button(
            copy.step1_continue(voice),
            type="primary",
            use_container_width=True,
            key="data_continue",
        ):
            wstate.advance()


def _guess_assignment_col(df: pl.DataFrame) -> str | None:
    for col in df.columns:
        try:
            if df.select(pl.col(col).n_unique()).item() <= 6 and not df.schema[col].is_numeric():
                return col
        except Exception:  # noqa: BLE001
            continue
    # numeric fallback
    for col in df.columns:
        try:
            if df.schema[col].is_numeric() and df.select(pl.col(col).n_unique()).item() <= 4:
                return col
        except Exception:  # noqa: BLE001
            continue
    return None


def _dataset_summary(df: pl.DataFrame, assignment_col: str | None) -> str:
    """Build a plain-language summary of the dataset for non-technical users."""
    parts = [f"<strong>{df.height:,} rows × {df.width} columns.</strong>"]

    # Guess "one row per..."
    numeric_count = sum(1 for c in df.columns if df.schema[c].is_numeric())
    text_count = sum(1 for c in df.columns if df.schema[c] == pl.Utf8)

    if assignment_col:
        try:
            vals = df.select(assignment_col).unique().to_series().to_list()
            vals_str = ", ".join(str(v) for v in vals[:4])
            n_groups = len(vals)
            parts.append(
                f"Possible group column detected: <strong>{assignment_col}</strong> "
                f"({n_groups} values: {vals_str})."
            )
        except Exception:  # noqa: BLE001
            pass

    if numeric_count:
        parts.append(
            f"{numeric_count} numeric column{'s' if numeric_count != 1 else ''} "
            f"that could be outcome metrics."
        )

    return " ".join(parts)
