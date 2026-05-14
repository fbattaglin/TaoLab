# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tao Lab is a modular, statistically rigorous experimentation platform that serves two audiences simultaneously: data scientists (full statistical detail) and business users (signal-language interpretation). It bridges simple A/B testing scripts and complex causal inference libraries via a unified plugin interface for analysis, diagnosis, and interpretation.

## Commands

All commands use `uv run` for reproducible execution:

```bash
# Launch the Streamlit UI
uv run streamlit run tao_lab/ui/app.py

# Generate canonical test datasets
uv run scripts/fetch_datasets.py

# Run validation tests (run individually, not as a suite — JAX/NumPyro
# initialise global GPU state that leaks between tests in the same process)
uv run python3 tests/test_final_mvp.py          # Frequentist A/B + ratio metrics
uv run python3 tests/test_phase2_bayesian.py    # Bayesian MCMC inference
uv run python3 tests/test_phase2_timeseries.py  # Interrupted time-series
uv run python3 tests/test_phase3_causal.py      # Causal inference (DoWhy/EconML)
uv run python3 tests/test_causal_hte.py         # HTE (CausalForestDML subgroups)
uv run python3 tests/test_bandit_replay.py      # MAB Regret Simulator (Thompson Sampling replay)
```

### React Frontend (custom Streamlit components)

The UI includes three custom React components (Stepper, VerdictBanner, PrescriptionCard) built with Vite + React + Tailwind. **Rebuild whenever you change `.tsx` or `.css` files in `tao_lab/ui/frontend/src/`**:

```bash
cd tao_lab/ui/frontend
npm run build          # tsc + vite build + post-build copy to dist/
```

Dist artefacts are committed. Each component has its own entry point (`stepper.html`, `verdict.html`, `prescription.html`) and is served from `dist/<name>/index.html` by its Python wrapper in `tao_lab/ui/components/`.

A pre-commit hook prevents committing stale `dist/` artefacts. Install once after cloning:

```bash
bash scripts/install_hooks.sh
```

### Optional PDF export

PDF export requires WeasyPrint (not installed by default):

```bash
uv pip install 'tao-lab[report]'
```

## Architecture

### Plugin System

Every statistical method inherits from `tao_lab/methods/base.py::Method` (ABC) and implements three methods:
- `fit(data: pl.DataFrame, config: Dict) -> AnalysisResult` — core algorithm
- `diagnostics() -> Dict[str, Any]` — method-specific health checks
- `visualize() -> List[go.Figure]` — standardized Plotly output

Pydantic models (`ExperimentConfig`, `AnalysisResult`, `MetricResult`, `RatioMetric`) enforce the contract between UI and statistical engines.

### Data Flow

1. **Upload** (CSV/Excel) → **Auto-diagnosis** (`tao_lab/diagnose/engine.py`) → independent scoring of all methods → ranked `MethodCandidate` list
2. **Diagnose** (Step 2) → user sees selectable method cards; can override the top recommendation; selection stored in `WizardState.selected_candidate_idx`
3. **Config** (Step 3) → reads `config_hint` from the *selected* candidate (not always rank-0); builds `ExperimentConfig`
4. **Run** → selected `Method.fit()` → mandatory SRM check (`tao_lab/checks/srm.py`) → optional BH correction (`tao_lab/checks/multiple_testing.py`)
5. **Interpret** → Claude API narration with template fallback (`tao_lab/interpret/narrator.py`)
6. **Report** → Markdown/YAML snapshot (`tao_lab/report/generator.py`)

### Dual-Audience Content System (Phase 4)

The app serves Signal and Spectrum readers at equal depth. Three content layers live in `tao_lab/ui/strings.py`:

**1. `CopyPair` — voice-aware microcopy**
```python
label = CopyPair(signal="Group column", spectrum="Assignment column")
label("signal")  # → "Group column"
label("spectrum")  # → "Assignment column"
```
`copy = _Copy()` is the singleton. All step files import `copy` from `strings.py`. Add new pairs to `_Copy` when any label needs to differ by audience.

**2. `GlossaryEntry` — structured term definitions**
Each entry has `term`, `short` (tooltip), `description` (drawer), `signal_synonym`, `first_use` (shown once per step on first appearance), and `learn_more` (citation URL). 28 entries cover all major statistical terms. Used by `explainer.py` helpers.

**3. `MethodBlurb` / `METHOD_BLURBS` — voice-aware method descriptions**
Central source for method card content. Each blurb has `display_name`, `signal`, `spectrum`, `assumptions_signal`, `assumptions_spectrum`. `method_card.py` imports from here — do not maintain separate blurb dicts in component files.

### Explainer / Inline Education System (`tao_lab/ui/components/explainer.py`)

Four building blocks for inline education:

| Function | Purpose |
|----------|---------|
| `term_label(key, *, voice)` | Styled term with tooltip from GLOSSARY |
| `term_with_hint(key, *, voice, step)` | `term_label` + shows `first_use` text the first time per step (tracked in `st.session_state["_tl_seen_terms_{step}"]`) |
| `concept_drawer(key, *, use_when, avoid_when, data_context)` | Enhanced expander with use/avoid guidance, worked example from user data, and citation link |
| `helper_caption(text)` | Small italic explanatory caption |

### Narrator Signal Mode (`tao_lab/interpret/narrator.py`)

Signal-mode narration follows a three-line decision template — distinct from the spectrum register which stays unchanged:

- **Line 1 (What happened)**: `"The treatment group had {abs_lift} more/less {metric} on average ({treatment_mean} vs {control_mean})."`
- **Line 2 (How sure)**: `"We're {confidence_word} confident the real effect is between {ci_lower} and {ci_upper} (95% confidence interval)."`
- **Line 3 (Decision relevance)**: drawn from the recommendation field.

`_confidence_word(p)` maps p-values → "very confident / quite confident / fairly confident / somewhat confident / not confident". Spectrum mode functions are byte-for-byte unchanged.

### Diagnosis Engine (Phase D)

`engine.py` uses a **score-all-methods** algorithm (not a priority chain):

- **`_detect_column_roles(df)`** classifies every column into `group_cols`, `timestamp_cols`, `numeric_cols`, `id_cols`, and computes `balance_ratio`. ID columns are integers where `n_unique / n_rows > 0.9` (floats with high cardinality are *not* IDs — they are continuous data).
- **`_try_parse_date_col(series)`** samples 50 Utf8 values and tries 6 date formats; returns a format string if ≥90% parse. This is what makes string-date CSVs route to Time-Series correctly.
- **`_score_ab / _score_timeseries / _score_causal / _score_exploratory`** each return an independent 0–1 float. Key design: ≥4 non-treatment numeric columns *penalize* A/B and *boost* Causal (observational datasets with many covariates, e.g. Lalonde, rank Causal #1).
- **`DiagnosisReport`** retains backward-compat fields (`suggested_method`, `rationale`, `config_hint`, `warnings`) populated from `candidates[0]`, plus new `candidates: List[MethodCandidate]` and `detected_signals`.

### Custom Component Stale-Value Pattern

Streamlit custom components persist the last `setComponentValue()` call and re-send it on every rerun. Always include a timestamp when posting values so Python can distinguish a fresh interaction from a stale one:

```ts
// React (TypeScript)
setComponentValue({ step: step.index, ts: Date.now() });
```

```python
# Python wrapper
ts = raw.get("ts")
prev_ts = st.session_state.get(_CLICK_TS_KEY)
if ts != prev_ts:
    st.session_state[_CLICK_TS_KEY] = ts
    return int(raw.get("step"))
return None  # stale — ignore
```

### Prescription Model (`tao_lab/interpret/narrator.py`)

`PrescriptionNarration` is the canonical structured output that drives Step 5:
- **Rule-driven fields**: `verdict` ("ship"/"hold"/"dont_ship"), `confidence`, `confidence_score`, `headline`, `caveats`, `next_steps_signal`, `next_steps_spectrum` — deterministic, based on p-values and effect size thresholds.
- **Optional LLM-enhanced fields**: `diagnosis`, `recommendation` — enriched via Claude API if `ANTHROPIC_API_KEY` is set; template fallback otherwise.
- **HTE field**: `hte_summary: Optional[TextPair]` — populated only when `result.hte` is not None.
- **Bandit field**: `bandit_summary: Optional[TextPair]` — populated when MAB replay simulation ran successfully.

`build_prescription(result, *, bandit_replay=None)` is the single entry point. Template-first strategy: all fields are always populated deterministically, so air-gapped/offline paths work. LLM can only rewrite `diagnosis` and `recommendation` — verdict and caveats remain rule-driven.

### Export Formats (`tao_lab/ui/components/exports.py`)

Three formats, all invoked from Step 5:
- **Markdown** (`to_markdown(...)`) — narrative + metrics table + YAML config block + HTE section when present
- **PDF** (`to_pdf_bytes(...)`) — single-page A4 via WeasyPrint (optional `[report]` extra); returns `None` if WeasyPrint not installed
- **YAML** (`to_yaml_config(...)`) — config snapshot for reproducibility

`tao_lab/report/generator.py` exists but is a legacy wrapper — `exports.py` is the canonical export path.

### Statistical Methods

| Module | Class | Engine | Maturity |
|--------|-------|--------|----------|
| `methods/ab_test.py` | `FrequentistABTest` | Welch's T-Test + Delta Method for ratios | Production |
| `methods/bayesian_ab.py` | Bayesian A/B | NumPyro (JAX) MCMC, HDI, ROPE | Production |
| `methods/time_series.py` | Interrupted TS | CausalPy counterfactual estimation | **Stub** — see Known Limitations |
| `methods/causal_inference.py` | Observational Causal | DoWhy (identification) + EconML DML (estimation) | Production |

### Heterogeneous Treatment Effects (HTE)

HTE is an optional mode within Causal Inference, not a separate method. When enabled via `ExperimentConfig.method_params["hte_enabled"]`, `CausalInference.fit()` runs `CausalForestDML` alongside `LinearDML` to estimate individual-level treatment effects (CATE).

**Key models:** `HTEResult`, `SubgroupEffect` in `base.py`. The `AnalysisResult.hte` field is `Optional[HTEResult]` — `None` when HTE is not enabled.

**Guardrails:** HTE is only offered when N ≥ 3,000 and ≥ 2 covariates exist. The diagnosis engine sets `config_hint["hte_eligible"]` to control UI visibility.

**UI flow:** Step 2 badge on Causal card → Step 3 checkbox toggle → Step 4 dual-model fit → Step 5 "Who benefits most?" section with feature importance bar chart, CATE histogram, and subgroup table.

**Architecture:** LinearDML provides ATE (more efficient, lower variance). CausalForestDML provides CATE (heterogeneity detection). Both run independently; ATE is reported from LinearDML, CATE from the forest. Effect modifiers (X) default to confounders (W) but can be customized in spectrum mode.

### MAB Regret Simulator (`tao_lab/methods/bandit_replay.py`)

Not a Method subclass — a **post-hoc insight** that appears in Step 5 for A/B tests when sufficient signal exists. Compares fixed 50/50 allocation against adaptive Thompson Sampling using the observed data.

**Activation conditions** (all required): A/B Test method, ≥200 observations, at least one metric with p < 0.10 (relaxed threshold — bandit needs some signal to converge), and ≥7 periods after aggregation.

**Two modes:**
- **Daily** (with timestamps): aggregates by day, x-axis = dates
- **Sequential** (no timestamps): shuffles data with fixed seed, chunks into batches of ~100, x-axis = "Users processed"

**Architecture:** `_prepare_daily_aggregates()` and `_prepare_sequential_batches()` both return `List[PeriodStats]`, so `_run_thompson_sampling()` is mode-agnostic. Posteriors: Beta-Binomial (binary metrics, MC sampling), Normal-Normal (continuous, analytical Φ formula).

**Key model:** `BanditReplayResult` in `base.py`. Stored on `WizardState.bandit_replay`. Step 5 renders a didactic section with two Plotly charts (cumulative reward + allocation trajectory) and key numbers (duration, regret reduction, convergence).

**Narration:** `_build_bandit_narration()` in `narrator.py` produces a `TextPair` with signal/spectrum descriptions. Signal mode explains the concept; spectrum mode reports numbers (mode, metric_type, cumulative regret delta).

## Implementation Rules

1. **Polars First**: All internal transformations use `polars`. Convert to `pandas` only at the boundary of external libraries (`statsmodels`, `econml`, `causalpy`). **Cast columns in Polars before `to_pandas()`** — PyArrow-backed extension types produced by `to_pandas()` can break standard Pandas reductions (`.mean()`, `.std()`) on float or string columns.
2. **Lazy Imports**: Heavy libraries (NumPyro, JAX, CausalPy, DoWhy) must be imported *inside* `fit()` or `visualize()` — never at module level — to keep the Streamlit UI responsive.
3. **Mandatory SRM**: Every `Method` runner must execute `tao_lab.checks.srm` before returning results (p < 0.001 threshold). Exception: observational methods (Causal Inference) and Time-Series set `srm_p_value=1.0, srm_detected=False` because they have no randomisation to validate — add a code comment when doing this.
4. **Structured Results**: Use the existing Pydantic models for all result objects; do not return raw dicts.
5. **Config hints flow downstream**: `MethodCandidate.config_hint` is the contract between the diagnosis engine and the configure step. Keys like `timestamp_col`, `date_format`, `assignment_col`, `metric_cols`, `covariates` must be set correctly in each `_score_*()` function so Step 3 pre-populates correctly without requiring user re-entry.
6. **Voice threading**: Every UI component that renders user-visible text accepts a `voice: Voice` parameter and uses `copy.<key>(voice)` for labels. Never hard-code English strings that a business user would read — add a `CopyPair` instead.
7. **Street-cred preservation**: Spectrum mode shows identical numbers, precision (3–4 sig figs), and terminology to the original implementation. p-values, CI bounds, effect sizes are never hidden — they may be secondary in signal mode but always accessible via "Show details" or tooltip.

## UI Standards

- **Design tokens** (source of truth: `tao_lab/ui/theme.py`): indigo-deep `#1E3A5F`, tangerine `#F97316`, slate `#475569`, success `#059669`, warning `#D97706`, danger `#DC2626`
- **Precision**: 3–4 significant figures (use `:.4g` format spec)
- **Progressive disclosure**: helper captions visible by default; statistical detail in expanders
- **Logo**: source in `logo/tao_lab_logo.png`, served from `tao_lab/ui/static/tao_lab_logo.png`. Applied via `st.logo()` (sidebar), `st.image()` (header + hero), and base64 in PDF exports. Do not embed the PNG as base64 in live UI renders (562 KB) — use the file path.

## WizardState Key Fields (`tao_lab/ui/state.py`)

| Field | Type | Purpose |
|-------|------|---------|
| `voice` | `"signal" \| "spectrum"` | Reader mode, flows to every component |
| `business_question` | `Optional[str]` | Free-form question entered on Step 1; included in Markdown and PDF exports |
| `selected_candidate_idx` | `int` | Which ranked method candidate the user chose (not always rank-0) |
| `engine` | `str` | `"Frequentist"` or `"Bayesian (NumPyro)"` for A/B tests |
| `prescription` | `Optional[PrescriptionNarration]` | Structured narration output from `build_prescription()`; drives Step 5 rendering |
| `method_visuals` | `List[go.Figure]` | Plotly figures from `Method.visualize()`, shown in the method-diagnostics expander |
| `bandit_replay` | `Optional[BanditReplayResult]` | MAB regret simulation result; drives the "Could smarter allocation..." section in Step 5 |
| `dataset_hints` | `dict` | Populated when a sample chip is loaded; keys include `"intervention_date"`, `"intervention_label"` — used by Step 3 to pre-populate fields |

## Test Datasets

Four canonical datasets in `datasets/`:
- `ab_test_ecommerce.csv` — 10k users, Control/Treatment, revenue + CTR ratio metric
- `causal_lalonde.csv` — Lalonde observational data for causal inference
- `causal_401k.csv` — 401(k) participation data; age and income are known effect modifiers (used for HTE demonstrations)
- `time_series_marketing.csv` — 180 days, intervention date 2023-04-15

## Known Limitations

These are documented so future contributors don't mistake stubs for production code:

1. **Time-Series is a stub.** `time_series.py` imports CausalPy but doesn't use it — the model fitting block is `try: pass except: pass`. The counterfactual is `mean(pre)`, p-value is hardcoded `0.01`, CIs are `lift * 0.8 / 1.2`. Completing this module requires implementing CausalPy's `SyntheticControl` or `InterruptedTimeSeries` model and extracting real posterior intervals.

2. **Ratio metric has no denominator-zero guard.** `_analyze_ratio()` in `ab_test.py` divides by `mu_y` without checking for zero or near-zero denominators. Edge cases (empty cohorts, very rare events) will produce `inf` or `nan`. Needs a guard and appropriate fallback.

3. **Causal Inference `MetricResult` fields are incomplete.** `control_mean` and `treatment_mean` are set to `0.0`, `lift_relative` to `0.0`. The narrator and prescription rendering should not rely on these fields for Causal Inference results.

4. **Propensity score overlap diagnostic trains on full data.** The `RandomForestClassifier` in `causal_inference.py` fits and predicts on the same dataset (no cross-validation), so the overlap plot is optimistically biased. The `LinearDML` estimator internally cross-fits, so ATE estimates are unaffected — only the diagnostic visualization is inflated.

5. **`networkx==2.8.8` pin.** Exact version pin in `pyproject.toml`, likely a transitive dependency conflict between EconML/DoWhy/CausalML. Test removal periodically.
