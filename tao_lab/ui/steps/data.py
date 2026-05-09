"""Step 1 — Data.

Phase B redesign: a hero with sample-data chips for one-click loading, the
Streamlit drag-drop uploader styled into a drop zone, and a per-column health
snapshot once data is loaded. The aim is that *before* the user chooses a
method, they already understand the shape and quality of their dataset.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import polars as pl
import streamlit as st

from tao_lab.ui import state as wstate
from tao_lab.ui.components.data_health import render_data_snapshot
from tao_lab.ui.strings import copy


_DATASETS_DIR = Path(__file__).parent.parent.parent.parent / "datasets"

_SAMPLE_CHIPS = [
    {
        "key": "ab",
        "label": "E-commerce A/B",
        "blurb": "10k users · revenue + CTR ratio metric",
        "file": "ab_test_ecommerce.csv",
    },
    {
        "key": "ts",
        "label": "Marketing time-series",
        "blurb": "180 days · intervention 2023-04-15",
        "file": "time_series_marketing.csv",
    },
    {
        "key": "ci",
        "label": "Lalonde causal",
        "blurb": "Observational treatment + covariates",
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
def _render_hero(s: wstate.WizardState, *, voice) -> None:
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

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

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
                f"line-height:1.4;margin-top:-6px;'>{chip['blurb']}</div>",
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
def _render_loaded(s: wstate.WizardState, *, voice) -> None:
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

    st.markdown("<hr class='tl-divider'>", unsafe_allow_html=True)

    # Best-effort guess at the assignment column for the balance bar chart.
    assignment_guess = _guess_assignment_col(df)
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
