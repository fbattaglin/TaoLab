# ☯️ Tao Lab — SOTA Experimentation Platform
### *Statistical Rigour at Scale.*

## 🏛️ Architecture & Engineering Standards

### 1. Data Layer: Polars-First
- **Core Engine:** All internal data transformations use `polars` for memory efficiency and execution speed.
- **Library Boundaries:** Conversion to `pandas` is deferred to the latest possible moment (`statsmodels`, `econml`, `causalpy`).
- **Type Safety:** Enforced via Pydantic models (`ExperimentConfig`, `AnalysisResult`). No raw dicts allowed in the core flow.

### 2. Modular Plugin System
Analysis methods implement the `tao_lab.methods.base.Method` interface. Total decoupling between UI and stats engines:
- **`fit()`**: Algorithm execution.
- **`diagnostics()`**: Convergence & health checks.
- **`visualize()`**: Plotly-native visualisations.

### 3. Statistical Engines
- **Frequentist A/B**: Welch's T-Test + **Delta Method** (Taylor expansion) for ratio metrics.
- **Bayesian A/B**: **NumPyro (JAX)** MCMC. Full posterior extraction with 95% HDI and ROPE analysis.
- **Time-Series Intervention**: **CausalPy** counterfactual estimation for longitudinal data.
- **Observational Causal Inference**: **DoWhy** (Identification) + **EconML** (Estimation via Double Machine Learning / LinearDML).
- **HTE (Heterogeneous Treatment Effects)**: Individual-level effect estimation using **CausalForestDML** (CATE). Includes feature importance analysis and subgroup discovery.

### 4. Decision Intelligence (Phase E)
- **Bayesian Risk**: Calculation of **Expected Loss** (the monetary risk of choosing the wrong variant).
- **Monetary Impact**: Automatic projection of absolute lift to business value using `business_unit_value` and `audience_size` parameters.
- **MAB Simulation**: Post-hoc Thompson Sampling replay on A/B data to quantify **Cumulative Regret** and optimal allocation trajectory.

### 5. Intelligent Diagnosis (Phase D)
- **Heuristic Scoring**: Multi-axis evaluation (cardinality, balance, variance stability, outlier risk) to recommend the optimal statistical method.
- **Data Health Score**: Composite metric (0-100) based on sample size, group balance, missingness, and variance (CV).

### 6. Statistical Guardrails (Non-negotiables)
- **SRM Check**: Chi-square (p < 0.001) validation of randomisation.
- **FDR Correction**: Benjamini-Hochberg (BH) adjustment for multiple testing across primary and secondary KPIs.

## 🛠️ Infrastructure & DX

### Modern Python with `uv`
Managed execution via `uv run`. 100% reproducible environments via `uv.lock`.

### Custom React Frontend
High-fidelity UI components built with **Vite + React + Tailwind**. 
- **Stepper**: Visual progress through the 5-step flow.
- **Verdict Banner**: Hero outcome state.
- **Prescription Card**: Structured summary of findings.
- **Theming**: **Forced Light Mode** via high-specificity CSS to ensure aesthetic stability across OS settings.

## 🚀 Operational Guide

```bash
# Data generation
uv run scripts/fetch_datasets.py

# Launch
uv run streamlit run tao_lab/ui/app.py

# Statistical Validation
uv run python3 tests/test_final_mvp.py
uv run python3 tests/test_phase2_bayesian.py
uv run python3 tests/test_phase3_causal.py
```

## 📂 Project Anatomy
```text
tao_lab/
  ├── ui/          # Streamlit shell + theme injection
  ├── components/  # React wrappers & Py-native visual components
  ├── diagnose/    # Heuristic scoring engine (Phase D)
  ├── methods/     # Statistical engines (Frequentist, Bayesian, Causal, TS)
  ├── checks/      # Guardrails (SRM, BH Correction)
  └── interpret/   # Narration layer (Technical vs Plain)
```

---
*Developed with SOTA 2026 Engineering Standards for Tao Lab.*
