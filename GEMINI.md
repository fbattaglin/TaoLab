# ☯️ Tao Lab: Statistical Experimentation Platform

Tao Lab is a modular, statistically rigorous experimentation platform designed for both data scientists and business stakeholders. It bridges the gap between simple A/B testing and advanced causal inference through a unified, high-performance interface.

## 🏗️ Project Overview

-   **Core Philosophy**: Statistical rigour with premium design.
-   **Tech Stack**:
    -   **Data Engine**: [Polars](https://pola.rs/) (Sub-millisecond wrangling)
    -   **UI**: [Streamlit](https://streamlit.io/) with custom [React](https://react.dev/) + [TailwindCSS](https://tailwindcss.com/) components.
    -   **Statistical Engines**:
        -   **Frequentist**: Welch's T-Test + **Delta Method** (Taylor expansion) for ratios.
        -   **Bayesian**: [NumPyro](https://num.pyro.ai/) (JAX) for MCMC inference. Posteriors, 95% HDI, and ROPE.
        -   **Causal Inference**: [DoWhy](https://py-why.github.io/dowhy/) (Identification) + [EconML](https://econml.azurewebsites.net/) (LinearDML/Double ML).
        -   **HTE**: Individual-level estimation via **CausalForestDML** (CATE) for subgroup discovery.
        -   **MAB**: Post-hoc **Thompson Sampling** replay simulator for Regret analysis.
        -   **Time-Series**: [CausalPy](https://causalpy.readthedocs.io/) for Interrupted Time-Series (ITS).
    -   **Decision Intelligence (Phase E)**: Automated **Expected Loss (Risk)** and **Expected Impact** (Monetary value) calculations.
    -   **Package Management**: [uv](https://github.com/astral-sh/uv).

## 🚀 Key Commands

### Setup & Data
```bash
# Initialize project and download canonical datasets
uv run scripts/fetch_datasets.py

# Install pre-commit hooks for frontend build validation
bash scripts/install_hooks.sh
```

### Development & UI
```bash
# Launch the Streamlit application
uv run streamlit run tao_lab/ui/app.py

# Rebuild the custom React frontend components
cd tao_lab/ui/frontend
npm install
npm run build
```

### Testing & Validation
> **Note**: Run tests individually to prevent JAX/NumPyro global state leakage.
```bash
uv run python3 tests/test_final_mvp.py          # Frequentist A/B
uv run python3 tests/test_phase2_bayesian.py    # Bayesian MCMC
uv run python3 tests/test_phase2_timeseries.py  # Interrupted Time-Series
uv run python3 tests/test_phase3_causal.py      # Causal Inference
uv run python3 tests/test_causal_hte.py         # Heterogeneous Treatment Effects
uv run python3 tests/test_bandit_replay.py      # MAB Regret Simulator
```

## 🧘 Architecture & Conventions

### 1. The Method Interface
Every statistical analysis is a "plugin" inheriting from `tao_lab.methods.base.Method`.
-   `fit(data, config)`: Core algorithm execution.
-   `diagnostics()`: Method-specific health checks (e.g., convergence, overlap).
-   `visualize()`: Standardized Plotly figure generation.

### 2. Data Handling (Polars First)
-   **Rule**: Use `polars` for ingestion and internal transformations.
-   **Rule**: Convert to `pandas` ONLY at the boundary of external library calls (e.g., EconML, Statsmodels).
-   **Mandatory**: Cast columns to explicit types in Polars *before* `.to_pandas()` to avoid PyArrow-backed extension type issues.

### 3. Performance & Imports
-   **Lazy Imports**: Heavy libraries (NumPyro, JAX, CausalPy, DoWhy) **MUST** be imported inside `fit()` or `visualize()` to keep the UI responsive.

### 4. UI & Communication
-   **Dual-Audience**: The app serves "Plain" (business) and "Technical" (DS) registers.
-   **Voice Threading**: Use `CopyPair` and `GlossaryEntry` from `tao_lab/ui/strings.py`. Never hard-code English strings for UI labels.
-   **Forced Light Mode**: Aesthetics are locked to a high-contrast light mode (see `tao_lab/ui/static/style.css`).

### 5. Mandatory Checks
-   **SRM**: Every `Method` runner (except observational ones) must execute `tao_lab.checks.srm` (threshold p < 0.001).
-   **Pydantic**: Always use the structured models in `base.py` (`ExperimentConfig`, `AnalysisResult`, `MetricResult`) to enforce the UI-Engine contract.

## 📁 Key File Map

-   `tao_lab/methods/`: Core statistical implementations.
-   `tao_lab/diagnose/engine.py`: Heuristic data inspection and method recommendation.
-   `tao_lab/ui/steps/`: Implementation of the 5-step wizard flow.
-   `tao_lab/ui/frontend/`: React components (Stepper, Verdict Banner, Prescription Card).
-   `tao_lab/ui/strings.py`: The "Brain" for dual-audience copy and the statistical glossary.
-   `tao_lab/interpret/narrator.py`: Logic for translating results into human-readable prescriptions.

## ⚠️ Known Limitations
-   **Time-Series**: Currently a stub; ITS logic needs real CausalPy integration.
-   **Ratio Metrics**: No guard for denominator-zero cases in `FrequentistABTest`.
-   **Causal Mean**: `control_mean` and `treatment_mean` are currently placeholders (0.0) in Causal results.
