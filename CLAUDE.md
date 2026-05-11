# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tao Lab is a modular, statistically rigorous experimentation platform that serves two audiences simultaneously: data scientists (full statistical detail) and business users (plain-language interpretation). It bridges simple A/B testing scripts and complex causal inference libraries via a unified plugin interface for analysis, diagnosis, and interpretation.

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

The app serves Plain and Technical readers at equal depth. Three content layers live in `tao_lab/ui/strings.py`:

**1. `CopyPair` — voice-aware microcopy**
```python
label = CopyPair(plain="Group column", technical="Assignment column")
label("plain")  # → "Group column"
label("technical")  # → "Assignment column"
```
`copy = _Copy()` is the singleton. All step files import `copy` from `strings.py`. Add new pairs to `_Copy` when any label needs to differ by audience.

**2. `GlossaryEntry` — structured term definitions**
Each entry has `term`, `short` (tooltip), `description` (drawer), `plain_synonym`, `first_use` (shown once per step on first appearance), and `learn_more` (citation URL). 28 entries cover all major statistical terms. Used by `explainer.py` helpers.

**3. `MethodBlurb` / `METHOD_BLURBS` — voice-aware method descriptions**
Central source for method card content. Each blurb has `display_name`, `plain`, `technical`, `assumptions_plain`, `assumptions_technical`. `method_card.py` imports from here — do not maintain separate blurb dicts in component files.

### Explainer / Inline Education System (`tao_lab/ui/components/explainer.py`)

Four building blocks for inline education:

| Function | Purpose |
|----------|---------|
| `term_label(key, *, voice)` | Styled term with tooltip from GLOSSARY |
| `term_with_hint(key, *, voice, step)` | `term_label` + shows `first_use` text the first time per step (tracked in `st.session_state["_tl_seen_terms_{step}"]`) |
| `concept_drawer(key, *, use_when, avoid_when, data_context)` | Enhanced expander with use/avoid guidance, worked example from user data, and citation link |
| `helper_caption(text)` | Small italic explanatory caption |

### Narrator Plain Mode (`tao_lab/interpret/narrator.py`)

Plain-mode narration follows a three-line decision template — distinct from the technical register which stays unchanged:

- **Line 1 (What happened)**: `"The treatment group had {abs_lift} more/less {metric} on average ({treatment_mean} vs {control_mean})."`
- **Line 2 (How sure)**: `"We're {confidence_word} confident the real effect is between {ci_lower} and {ci_upper} (95% confidence interval)."`
- **Line 3 (Decision relevance)**: drawn from the recommendation field.

`_confidence_word(p)` maps p-values → "very confident / quite confident / fairly confident / somewhat confident / not confident". Technical mode functions are byte-for-byte unchanged.

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
6. **Voice threading**: Every UI component that renders user-visible text accepts a `voice: Voice` parameter and uses `copy.<key>(voice)` for labels. Never hard-code English strings that a business user would read — add a `CopyPair` instead.
7. **Street-cred preservation**: Technical mode shows identical numbers, precision (3–4 sig figs), and terminology to the original implementation. p-values, CI bounds, effect sizes are never hidden — they may be secondary in plain mode but always accessible via "Show details" or tooltip.

## UI Standards

- **Design tokens** (source of truth: `tao_lab/ui/theme.py`): indigo-deep `#1E3A5F`, tangerine `#F97316`, slate `#475569`, success `#059669`, warning `#D97706`, danger `#DC2626`
- **Precision**: 3–4 significant figures (use `:.4g` format spec)
- **Progressive disclosure**: helper captions visible by default; statistical detail in expanders
- **Logo**: source in `logo/tao_lab_logo.png`, served from `tao_lab/ui/static/tao_lab_logo.png`. Applied via `st.logo()` (sidebar), `st.image()` (header + hero), and base64 in PDF exports. Do not embed the PNG as base64 in live UI renders (562 KB) — use the file path.

## WizardState Key Fields (`tao_lab/ui/state.py`)

| Field | Type | Purpose |
|-------|------|---------|
| `voice` | `"plain" \| "technical"` | Reader mode, flows to every component |
| `business_question` | `Optional[str]` | Free-form question entered on Step 1; included in Markdown and PDF exports |
| `selected_candidate_idx` | `int` | Which ranked method candidate the user chose (not always rank-0) |
| `engine` | `str` | `"Frequentist"` or `"Bayesian (NumPyro)"` for A/B tests |
| `method_visuals` | `List[go.Figure]` | Plotly figures from `Method.visualize()`, shown in the method-diagnostics expander |

## Test Datasets

Three canonical datasets in `datasets/`:
- `ab_test_ecommerce.csv` — 10k users, Control/Treatment, revenue + CTR ratio metric
- `causal_lalonde.csv` — Lalonde observational data for causal inference
- `time_series_marketing.csv` — 180 days, intervention date 2023-04-15
