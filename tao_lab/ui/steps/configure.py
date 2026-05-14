"""Step 3 — Configure.

Phase D update:
* Reads ``config_hint`` from the *selected* candidate (not always the
  top-ranked one), so the form adapts when the user overrides the method.
* Time-Series form handles string-typed date columns by casting via the
  ``date_format`` stored in the candidate's ``config_hint``.
"""

from __future__ import annotations

import pandas as pd
import polars as pl
import streamlit as st

from tao_lab.methods.base import ExperimentConfig
from tao_lab.ui import state as wstate
from tao_lab.ui.components.explainer import concept_drawer, explainer_drawer, helper_caption
from tao_lab.ui.components.metric_picker import render_metric_picker
from tao_lab.ui.components.variant_setup import render_variant_setup
from tao_lab.ui.strings import copy


def render() -> None:
    s = wstate.get_state()
    if s.df is None or s.diagnosis is None:
        st.info("Complete previous steps first.")
        return

    method = s.chosen_method or s.diagnosis.suggested_method
    s.chosen_method = method

    # ── Read config_hint from the selected candidate ──
    candidates = s.diagnosis.candidates
    idx = s.selected_candidate_idx
    if idx < len(candidates):
        hint = candidates[idx].config_hint
    else:
        hint = s.diagnosis.config_hint

    if method == "A/B Test":
        _render_ab_form(s, hint)
    elif method == "Time-Series Intervention":
        _render_timeseries_form(s, hint)
    elif method == "Causal Inference":
        _render_causal_form(s, hint)
    else:
        st.warning(
            f"The selected method '{method}' is not yet fully implemented."
        )

    st.markdown("<hr class='tl-divider'>", unsafe_allow_html=True)
    if st.button("← Back", key="cfg_back"):
        wstate.go_back()


# ───────────────────────── A/B Test ─────────────────────────
def _render_ab_form(s: wstate.WizardState, hint: dict) -> None:
    df = s.df
    voice = s.voice

    # ── Why these settings? ──
    _render_why_settings(hint, voice)

    _eyebrow(copy.step3_variant_eyebrow(voice))
    assignment_col, control_val, treatment_val = render_variant_setup(
        df,
        default_assignment=hint.get("assignment_col", df.columns[0]),
        default_control=hint.get("control_val", "control"),
        default_treatment=hint.get("treatment_val", "treatment"),
        voice=voice,
    )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    _eyebrow(copy.step3_metrics_eyebrow(voice))
    metric_cols, ratio_metrics = render_metric_picker(
        df,
        default_metrics=hint.get("metric_cols", []),
        default_ratios=hint.get("ratio_metrics", []),
        voice=voice,
    )

    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)

    with st.expander(copy.step3_advanced_label(voice), expanded=False):
        col_left, col_right = st.columns(2)
        with col_left:
            engine = st.selectbox(
                "Statistical engine",
                ["Frequentist", "Bayesian (NumPyro)"],
                help=(
                    "Frequentist gives p-values and confidence intervals. "
                    "Bayesian gives the posterior probability the treatment is better."
                ),
            )
            helper_caption(
                "Frequentist is faster and the default expectation in most teams. "
                "Bayesian is richer but slower."
            )
            explainer_drawer("frequentist_vs_bayesian")

        with col_right:
            alpha = st.slider(
                "Significance threshold (α)",
                min_value=0.01,
                max_value=0.20,
                value=0.05,
                step=0.01,
                help="The false-positive rate you're willing to accept.",
            )
            helper_caption(
                "Default 0.05 means we accept a 5% chance of declaring a 'win' that "
                "isn't really there. Lower α = stricter."
            )
            explainer_drawer("alpha")

        expected_ratio_c = st.slider(
            "Expected control proportion (used for SRM check)",
            min_value=0.1,
            max_value=0.9,
            value=0.5,
            step=0.05,
            help="The split you intended at randomisation, e.g. 0.5 for a 50/50 test.",
        )
        helper_caption(
            "If observed split differs strongly from this, we'll flag a Sample Ratio "
            "Mismatch — usually a sign of an assignment or logging bug."
        )
        concept_drawer(
            "srm",
            use_when="You randomised assignment and want to verify the split is clean.",
            avoid_when="You're doing observational analysis (no randomisation to check).",
        )

    unit_val, aud_size = _render_business_impact_inputs(voice, key_suffix="ab")

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    if st.button(
        copy.step3_run(voice), type="primary", key="ab_run", use_container_width=False
    ):
        s.config = ExperimentConfig(
            assignment_col=assignment_col,
            control_val=control_val,
            treatment_val=treatment_val,
            metric_cols=metric_cols,
            ratio_metrics=ratio_metrics,
            alpha=alpha,
            expected_ratio={
                control_val: expected_ratio_c,
                treatment_val: 1.0 - expected_ratio_c,
            },
            business_unit_value=unit_val,
            audience_size=aud_size,
        )
        s.engine = engine
        wstate.advance()


# ───────────────────────── Time-Series ─────────────────────────
def _render_timeseries_form(s: wstate.WizardState, hint: dict) -> None:
    df = s.df
    voice = s.voice

    _eyebrow("Series and intervention")
    helper_caption(
        "Pick the timestamp column and the metric you want to evaluate. "
        "We'll fit a counterfactual to the pre-intervention period and contrast "
        "it with what actually happened after."
    )

    # ── Detect date format from diagnosis (handles string dates) ──
    date_format = hint.get("date_format")

    c1, c2 = st.columns(2)
    with c1:
        default_ts_col = hint.get("timestamp_col", df.columns[0])
        ts_col_idx = df.columns.index(default_ts_col) if default_ts_col in df.columns else 0
        timestamp_col = st.selectbox(
            "Timestamp column",
            df.columns,
            index=ts_col_idx,
        )

        default_metrics = hint.get("metrics", [])
        metric_options = [c for c in df.columns if c != timestamp_col]
        default_metric = default_metrics[0] if default_metrics else (metric_options[0] if metric_options else "")
        metric_col = st.selectbox(
            "Outcome metric",
            metric_options,
            index=metric_options.index(default_metric) if default_metric in metric_options else 0,
        )

    # ── Parse the timestamp column to get min/max and observation count ──
    ts_series = df[timestamp_col]
    ts_parsed = None
    if ts_series.dtype == pl.Utf8:
        fmt = date_format or "%Y-%m-%d"
        try:
            ts_parsed = ts_series.str.to_date(fmt, strict=False).drop_nulls()
        except Exception:  # noqa: BLE001
            pass
    elif ts_series.dtype in (pl.Date, pl.Datetime):
        ts_parsed = ts_series.drop_nulls()

    min_date = ts_parsed.min() if ts_parsed is not None else None
    max_date = ts_parsed.max() if ts_parsed is not None else None
    n_obs = ts_parsed.len() if ts_parsed is not None else 0

    with c2:
        if min_date is not None and max_date is not None:
            import datetime as _dt
            min_d = min_date.date() if hasattr(min_date, "date") else min_date
            max_d = max_date.date() if hasattr(max_date, "date") else max_date
            span_days = (max_d - min_d).days

            # ── Data range summary ──
            st.markdown(
                f"""<div class="tl-card" style="padding:.8rem 1rem;margin-bottom:.75rem;">
                  <div style="font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;
                              color:var(--tl-tangerine);font-weight:600;margin-bottom:.4rem;">
                    Available range
                  </div>
                  <div style="display:flex;justify-content:space-between;align-items:baseline;">
                    <span style="font-size:.9rem;font-weight:500;color:var(--tl-indigo-deep);">
                      {min_d.strftime('%b %d, %Y')}
                    </span>
                    <span style="font-size:.75rem;color:var(--tl-slate);">→</span>
                    <span style="font-size:.9rem;font-weight:500;color:var(--tl-indigo-deep);">
                      {max_d.strftime('%b %d, %Y')}
                    </span>
                  </div>
                  <div style="font-size:.8rem;color:var(--tl-slate);margin-top:.3rem;">
                    {n_obs} observations · {span_days} days
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )

            # ── Default intervention date: from dataset_hints if available, else midpoint ──
            hint_date_str = s.dataset_hints.get("intervention_date")
            if hint_date_str:
                try:
                    default_date = _dt.date.fromisoformat(hint_date_str)
                    # Clamp to actual data range
                    default_date = max(min_d, min(max_d, default_date))
                except ValueError:
                    default_date = min_d + (max_d - min_d) // 2
            else:
                default_date = min_d + (max_d - min_d) // 2

            intervention_date = st.date_input(
                "Intervention date",
                value=default_date,
                min_value=min_d,
                max_value=max_d,
                help="Select the date when the change went live. Only dates within your data range are allowed.",
            )

            # ── Live pre/post split preview ──
            if ts_parsed is not None and isinstance(intervention_date, _dt.date):
                n_pre = int((ts_parsed < intervention_date).sum())
                n_post = n_obs - n_pre
                pct_pre = n_pre / n_obs * 100 if n_obs > 0 else 0
                pct_post = n_post / n_obs * 100 if n_obs > 0 else 0

                # Visual split bar
                st.markdown(
                    f"""<div style="margin-top:.5rem;">
                      <div style="font-size:.8rem;color:var(--tl-slate);margin-bottom:.3rem;">
                        Pre / Post split
                      </div>
                      <div style="display:flex;height:8px;border-radius:4px;overflow:hidden;">
                        <div style="width:{pct_pre:.1f}%;background:var(--tl-indigo-deep);"></div>
                        <div style="width:{pct_post:.1f}%;background:var(--tl-tangerine);"></div>
                      </div>
                      <div style="display:flex;justify-content:space-between;margin-top:.25rem;">
                        <span style="font-size:.8rem;color:var(--tl-indigo-deep);font-weight:500;">
                          Pre: {n_pre} obs
                        </span>
                        <span style="font-size:.8rem;color:var(--tl-tangerine);font-weight:500;">
                          Post: {n_post} obs
                        </span>
                      </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

                if n_pre < 10:
                    st.warning(
                        f"Only {n_pre} pre-intervention observations. "
                        "The counterfactual estimate may be unreliable — "
                        "consider choosing an earlier intervention date."
                    )
                if n_post < 5:
                    st.warning(
                        f"Only {n_post} post-intervention observations. "
                        "Very few data points to measure the effect."
                    )
        else:
            import datetime as _dt
            st.info("Could not parse dates from the selected column. Enter the intervention date manually.")
            intervention_date = st.date_input(
                "Intervention date",
                help="The date when the change or intervention went live.",
            )

    # ── Time-series chart (full-width, below column layout) ──
    if ts_parsed is not None and metric_col:
        import datetime as _dt
        inter_dt = intervention_date if isinstance(intervention_date, _dt.date) else None
        _render_timeseries_chart(df, timestamp_col, metric_col, ts_parsed, inter_dt, date_format, voice)

    unit_val, aud_size = _render_business_impact_inputs(voice, key_suffix="ts")

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    if st.button(copy.step3_run(voice), type="primary", key="ts_run"):
        method_params = {
            "timestamp_col": timestamp_col,
            "intervention_date": pd.Timestamp(intervention_date),
        }
        if date_format:
            method_params["date_format"] = date_format

        s.config = ExperimentConfig(
            assignment_col="",
            control_val="",
            treatment_val="",
            metric_cols=[metric_col],
            method_params=method_params,
            business_unit_value=unit_val,
            audience_size=aud_size,
        )
        wstate.advance()


# ───────────────────────── Causal Inference ─────────────────────────
def _render_causal_form(s: wstate.WizardState, hint: dict) -> None:
    df = s.df
    voice = s.voice

    _eyebrow("Treatment, outcome, and confounders")
    if voice == "signal":
        helper_caption(
            "Causal inference estimates the effect of a change even when assignment wasn't random "
            "— but it needs you to include every factor that might affect both who got the treatment "
            "and the outcome."
        )
    else:
        helper_caption(
            "Causal inference recovers a causal effect from observational data — "
            "but only under the assumption that you've measured every confounder. "
            "Be deliberate about which columns you list."
        )

    # ── Why these settings? ──
    _render_why_settings(hint, voice)

    c1, c2 = st.columns(2)
    with c1:
        default_treatment = hint.get("assignment_col", df.columns[0])
        treat_idx = df.columns.index(default_treatment) if default_treatment in df.columns else 0
        treatment_col = st.selectbox(
            "Treatment column",
            df.columns,
            index=treat_idx,
            help="The column that indicates who received the treatment.",
        )
        if voice == "signal":
            helper_caption("The column indicating who received the change (0/1 or similar).")

        default_outcomes = hint.get("metrics", [])
        outcome_options = [c for c in df.columns if c != treatment_col]
        default_outcome = default_outcomes[0] if default_outcomes else (outcome_options[0] if outcome_options else "")
        outcome_col = st.selectbox(
            "Outcome metric",
            outcome_options,
            index=outcome_options.index(default_outcome) if default_outcome in outcome_options else 0,
            help="The number you want to measure the effect on.",
        )

    with c2:
        default_covariates = hint.get("covariates", [])
        available_covariates = [c for c in df.columns if c not in [treatment_col, outcome_col]]
        confounders_label = "Confounders" if voice == "signal" else "Confounders (W)"
        covariates = st.multiselect(
            confounders_label,
            available_covariates,
            default=[c for c in default_covariates if c in available_covariates],
            help="Variables that plausibly affect both treatment and outcome.",
        )
        if voice == "signal":
            helper_caption(
                "Factors that might affect both who got the treatment and the outcome. "
                "Including them helps isolate the true effect of the change."
            )

    # ── HTE toggle (only when eligible) ──
    hte_enabled = False
    hte_features = covariates  # default: same as confounders
    hte_eligible = hint.get("hte_eligible", False) and len(covariates) >= 2
    if hte_eligible:
        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
        hte_enabled = st.checkbox(
            copy.step3_hte_toggle(voice),
            value=False,
            key="ci_hte_toggle",
            help=copy.step3_hte_help(voice),
        )
        if hte_enabled:
            helper_caption(copy.step3_hte_help(voice))
            # Advanced: let experts customize effect modifiers
            if voice == "spectrum":
                with st.expander("Advanced: separate effect modifiers from confounders", expanded=False):
                    hte_features = st.multiselect(
                        copy.step3_hte_features_label(voice),
                        covariates,
                        default=covariates,
                        help=copy.step3_hte_features_help(voice),
                        key="ci_hte_features",
                    )
                    if not hte_features:
                        hte_features = covariates

    unit_val, aud_size = _render_business_impact_inputs(voice, key_suffix="ci")

    if st.button(copy.step3_run(voice), type="primary", key="ci_run"):
        s.clear_results()
        method_params = {}
        if hte_enabled:
            method_params["hte_enabled"] = True
            method_params["hte_features"] = hte_features
        s.config = ExperimentConfig(
            assignment_col=treatment_col,
            control_val="",
            treatment_val="",
            metric_cols=[outcome_col],
            covariate_cols=covariates,
            method_params=method_params,
            business_unit_value=unit_val,
            audience_size=aud_size,
        )
        wstate.advance()


# ───────────────────────── Time-series chart ─────────────────────────
def _render_timeseries_chart(
    df: pl.DataFrame,
    timestamp_col: str,
    metric_col: str,
    ts_parsed,
    intervention_date,
    date_format: str | None,
    voice: str,
) -> None:
    """Full-width Plotly chart showing the metric over time, split pre/post intervention."""
    import datetime as _dt

    try:
        import plotly.graph_objects as go
    except ImportError:
        return  # Plotly not available — skip silently

    # ── Build a unified date + value series ──
    try:
        metric_series = df[metric_col]
        # Parse timestamps to date objects
        if df[timestamp_col].dtype == pl.Utf8:
            fmt = date_format or "%Y-%m-%d"
            dates_parsed = df[timestamp_col].str.to_date(fmt, strict=False)
        elif df[timestamp_col].dtype in (pl.Date, pl.Datetime):
            dates_parsed = df[timestamp_col]
        else:
            return  # Can't parse

        # Convert to Python objects for Plotly
        dates = [d.date() if hasattr(d, "date") else d for d in dates_parsed.to_list() if d is not None]
        values = metric_series.to_list()

        if len(dates) != len(values) or len(dates) == 0:
            return

        # Sort by date
        pairs = sorted(zip(dates, values), key=lambda x: x[0])
        dates_sorted = [p[0] for p in pairs]
        values_sorted = [p[1] for p in pairs]

    except Exception:  # noqa: BLE001
        return  # Silently skip chart on any parse failure

    # ── Split into pre / post ──
    INDIGO = "#1E3A5F"
    TANGERINE = "#F97316"
    DANGER = "#DC2626"

    pre_dates, pre_vals, post_dates, post_vals = [], [], [], []
    for d, v in zip(dates_sorted, values_sorted):
        if intervention_date and d < intervention_date:
            pre_dates.append(d)
            pre_vals.append(v)
        else:
            post_dates.append(d)
            post_vals.append(v)

    fig = go.Figure()

    # Pre-intervention trace (indigo)
    if pre_dates:
        fig.add_trace(go.Scatter(
            x=pre_dates,
            y=pre_vals,
            mode="lines+markers",
            name="Pre-intervention",
            line=dict(color=INDIGO, width=2),
            marker=dict(color=INDIGO, size=5),
            hovertemplate="%{x|%b %d, %Y}: %{y:,.2f}<extra>Pre</extra>",
        ))

    # Post-intervention trace (tangerine)
    if post_dates:
        fig.add_trace(go.Scatter(
            x=post_dates,
            y=post_vals,
            mode="lines+markers",
            name="Post-intervention",
            line=dict(color=TANGERINE, width=2),
            marker=dict(color=TANGERINE, size=5),
            hovertemplate="%{x|%b %d, %Y}: %{y:,.2f}<extra>Post</extra>",
        ))

    # Intervention date line — use add_shape + add_annotation separately to avoid
    # Plotly's buggy annotation-position calculation on string-typed date axes.
    if intervention_date:
        x_iso = intervention_date.isoformat()
        fig.add_shape(
            type="line",
            x0=x_iso, x1=x_iso,
            y0=0, y1=1,
            yref="paper",
            line=dict(dash="dash", color=DANGER, width=1.5),
        )
        fig.add_annotation(
            x=x_iso,
            y=0.98,
            yref="paper",
            text=intervention_date.strftime("Intervention · %b %d, %Y"),
            showarrow=False,
            xanchor="left",
            yanchor="top",
            font=dict(size=11, color=DANGER),
            bgcolor="rgba(255,255,255,0.75)",
        )

    metric_label = metric_col.replace("_", " ").title()
    fig.update_layout(
        height=260,
        margin=dict(l=0, r=0, t=28, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#F8FAFC",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#0F172A"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=11),
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            gridcolor="#E2E8F0",
            zeroline=False,
            tickfont=dict(size=11),
            title=metric_label,
            title_font=dict(size=11),
        ),
        hovermode="x unified",
    )

    label = "signal" if voice == "signal" else "spectrum"
    caption = (
        f"**{metric_label}** over time. "
        "The dashed line marks the intervention date — drag the date picker above to explore different splits."
    ) if label == "signal" else (
        f"**{metric_label}** time series. Pre-period (indigo) feeds the counterfactual model; "
        "post-period (tangerine) is compared against it."
    )

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption(caption)


# ───────────────────────── helpers ─────────────────────────
def _eyebrow(text: str) -> None:
    st.markdown(
        f"<div style='font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;"
        f"color:var(--tl-tangerine);font-weight:600;margin-bottom:.5rem;'>{text}</div>",
        unsafe_allow_html=True,
    )


def _render_why_settings(hint: dict, voice: str) -> None:
    """Collapsible explaining why the form fields are pre-filled."""
    if not hint:
        return

    parts = []
    if hint.get("assignment_col"):
        col_name = hint["assignment_col"]
        if voice == "signal":
            parts.append(
                f"We detected <strong>{col_name}</strong> as the group column "
                f"because it has a small number of distinct values."
            )
        else:
            parts.append(
                f"Assignment column inferred as <code>{col_name}</code> "
                f"(low cardinality categorical)."
            )

    if hint.get("metric_cols"):
        metrics = hint["metric_cols"]
        if voice == "signal":
            parts.append(
                f"We found {len(metrics)} numeric column{'s' if len(metrics) != 1 else ''} "
                f"that look like outcome metrics: {', '.join(metrics)}."
            )
        else:
            parts.append(
                f"Candidate metrics: {', '.join(metrics)}."
            )

    if hint.get("timestamp_col"):
        if voice == "signal":
            parts.append(
                f"We detected <strong>{hint['timestamp_col']}</strong> as a date column."
            )
        else:
            parts.append(f"Timestamp column: <code>{hint['timestamp_col']}</code>.")

    if not parts:
        return

    with st.expander(copy.step3_why_settings(voice), expanded=False):
        for p in parts:
            st.markdown(p, unsafe_allow_html=True)


def _render_business_impact_inputs(voice: str, key_suffix: str) -> tuple[float | None, int | None]:
    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
    
    label = "Business Impact Simulation (Optional)" if voice == "signal" else "Decision Intelligence / ROI (Optional)"
    with st.expander(label, expanded=False):
        helper_caption(
            "Map your primary metric to dollars to simulate the expected ROI and Risk of a full rollout."
        )
        c1, c2 = st.columns(2)
        with c1:
            unit_val = st.number_input(
                "Value per unit ($)",
                min_value=0.0,
                value=0.0,
                step=1.0,
                help="e.g. 50 if one conversion is worth $50.",
                key=f"bui_val_{key_suffix}",
            )
        with c2:
            aud_size = st.number_input(
                "Total Audience Size",
                min_value=0,
                value=0,
                step=1000,
                help="How many users would be affected if you roll this out to 100%?",
                key=f"bui_aud_{key_suffix}",
            )
        
        return float(unit_val) if unit_val > 0 else None, int(aud_size) if aud_size > 0 else None
