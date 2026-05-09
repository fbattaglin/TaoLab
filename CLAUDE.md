# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tao Lab is a modular, statistically rigorous experimentation platform for data scientists. It bridges simple A/B testing scripts and complex causal inference libraries via a unified plugin interface for analysis, diagnosis, and interpretation.

## Commands

All commands use `uv run` for reproducible execution:

```bash
# Launch the Streamlit UI
uv run streamlit run tao_lab/ui/app.py

# Generate canonical test datasets
uv run scripts/fetch_datasets.py

# Run validation tests (run individually, not as a suite)
uv run python3 tests/test_final_mvp.py          # Frequentist A/B + ratio metrics
uv run python3 tests/test_phase2_bayesian.py    # Bayesian MCMC inference
uv run python3 tests/test_phase2_timeseries.py  # Interrupted time-series
uv run python3 tests/test_phase3_causal.py      # Causal inference (DoWhy/EconML)
```

### React Frontend (custom Streamlit components)

The UI includes three custom React components (Stepper, VerdictBanner, PrescriptionCard) built with Vite + React + Tailwind. **Rebuild whenever you change `.tsx` or `.css` files in `tao_lab/ui/frontend/src/`**:

```bash
cd tao_lab/ui/frontend
npm run build          # tsc + vite build + post-build copy to dist/
```

Dist artefacts are committed. Each component has its own entry point (`stepper.html`, `verdict.html`, `prescription.html`) and is served from `dist/<name>/index.html` by its Python wrapper in `tao_lab/ui/components/`.

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

### Statistical Methods

| Module | Class | Engine |
|--------|-------|--------|
| `methods/ab_test.py` | `FrequentistABTest` | Welch's T-Test + Delta Method for ratios |
| `methods/bayesian_ab.py` | Bayesian A/B | NumPyro (JAX) MCMC, HDI, ROPE |
| `methods/time_series.py` | Interrupted TS | CausalPy counterfactual estimation |
| `methods/causal_inference.py` | Observational Causal | DoWhy (identification) + EconML DML (estimation) |

## Implementation Rules

1. **Polars First**: All internal transformations use `polars`. Convert to `pandas` only at the boundary of external libraries (`statsmodels`, `econml`, `causalpy`). **Cast columns in Polars before `to_pandas()`** — PyArrow-backed extension types produced by `to_pandas()` can break standard Pandas reductions (`.mean()`, `.std()`) on float or string columns.
2. **Lazy Imports**: Heavy libraries (NumPyro, JAX, CausalPy, DoWhy) must be imported *inside* `fit()` or `visualize()` — never at module level — to keep the Streamlit UI responsive.
3. **Mandatory SRM**: Every `Method` runner must execute `tao_lab.checks.srm` before returning results (p < 0.001 threshold).
4. **Structured Results**: Use the existing Pydantic models for all result objects; do not return raw dicts.
5. **Config hints flow downstream**: `MethodCandidate.config_hint` is the contract between the diagnosis engine and the configure step. Keys like `timestamp_col`, `date_format`, `assignment_col`, `metric_cols`, `covariates` must be set correctly in each `_score_*()` function so Step 3 pre-populates correctly without requiring user re-entry.

## UI Standards

- **Semaphore colors**: Success `#00C853` (green), Warning `#FFD600` (yellow), Danger `#D50000` (red)
- **Precision**: 3 significant figures by default
- **Progressive disclosure**: Wizard mode (heuristic recommendations) vs. Expert mode (full control over alpha, ratios, covariates)

## Test Datasets

Three canonical datasets in `datasets/`:
- `ab_test_ecommerce.csv` — 10k users, Control/Treatment, revenue + CTR ratio metric
- `causal_lalonde.csv` — Lalonde observational data for causal inference
- `time_series_marketing.csv` — 180 days, intervention date 2023-04-15
