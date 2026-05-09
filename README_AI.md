# ☯️ Tao Lab — SOTA Experimentation Platform

## Executive Summary
Tao Lab is a lightweight, statistically rigorous experimentation platform designed for Data Scientists. It bridges the gap between simple A/B testing scripts and complex, specialized causal inference libraries by providing a unified, modular interface for analysis, diagnosis, and interpretation.

## 🏗️ Architecture & Engineering Standards

### 1. Data Layer: Polars-First
- **Core Engine:** All internal data transformations use `polars` for memory efficiency and execution speed.
- **Library Boundaries:** Conversion to `pandas` is deferred to the latest possible moment, occurring only at the boundary of external statistical libraries (`statsmodels`, `econml`, `causalpy`).
- **Type Safety:** Strictly enforced via Pydantic models (`ExperimentConfig`, `AnalysisResult`). Contracts are polymorphic, supporting `Union[str, int, float]` for variant identification.

### 2. Modular Plugin System
Every analysis method implements the `tao_lab.methods.base.Method` interface, ensuring total decoupling between the UI and the statistical engines:
- **`fit()`**: Core algorithm execution.
- **`diagnostics()`**: Method-specific health checks (e.g., MCMC convergence, propensity overlap).
- **`visualize()`**: Standardized Plotly output.

### 3. Statistical Engines (SOTA 2026)
- **Frequentist A/B:** Implements Welch's T-Test and the **Delta Method** for ratio metrics (e.g., CTR), handling variance of ratios correctly.
- **Bayesian A/B:** Powered by **NumPyro (JAX)** for high-performance MCMC sampling. Computes Posteriors, 95% HDI, and ROPE (Region of Practical Equivalence).
- **Time-Series Intervention:** Utilizes **CausalPy** for quasi-experimental "Interrupted Time Series" analysis with counterfactual estimation.
- **Observational Causal Inference:** Integrates **DoWhy** (Identification) and **EconML** (Estimation via Double Machine Learning - DML).

### 4. Statistical Guardrails (Non-negotiables)
- **SRM Check:** Automated Chi-square test (p < 0.001) to detect Sample Ratio Mismatch before analysis.
- **Multiple Testing Correction:** Automatic application of **Benjamini-Hochberg (FDR)** when evaluating multiple KPIs.
- **Propensity Overlap:** Mandatory diagnostic for causal inference to validate the "positivity" assumption.

## 🛠️ Infrastructure & DX

### Modern Environment Management (`uv`)
The project has been migrated from legacy `pip/venv` to **`uv`**, providing:
- **Speed:** 10x-100x faster dependency resolution and installation.
- **Reproducibility:** A single `uv.lock` file ensures bit-for-bit identical environments across all machines.
- **Simplicity:** Managed execution via `uv run`.

### Intelligent UI (`streamlit`)
- **Wizard vs. Expert:** Progressive disclosure UX. Wizard mode provides heuristic-based methodology recommendations.
- **AI Interpretation:** Optional integration with Anthropic's Claude to narrate statistical results into business language, with a robust template-based fallback.
- **Reproducibility:** Every run generates a downloadable YAML configuration for auditability.

## 🚀 How to Run

### 1. Generate Test Datasets
```bash
uv run scripts/fetch_datasets.py
```

### 2. Launch Platform
```bash
uv run streamlit run tao_lab/ui/app.py
```

### 3. Validate Statistics
```bash
uv run python3 tests/test_final_mvp.py
uv run python3 tests/test_phase2_bayesian.py
uv run python3 tests/test_phase3_causal.py
```

## 📂 Project Structure
```text
tao_lab/
  ├── ui/          # Streamlit frontend & UX logic
  ├── diagnose/    # Heuristic & schema inference engine
  ├── methods/     # Statistical plugins (Frequentist, Bayesian, Causal, TS)
  ├── checks/      # Statistical guardrails (SRM, BH Correction)
  ├── interpret/   # LLM & Template narration layer
  ├── report/      # Markdown generation logic
  └── variance/    # Variance reduction (CUPED/CUPAC) - WIP
datasets/          # Canonical test data
scripts/           # Infrastructure & data fetching utilities
tests/             # Statistical validation suite
```

---
*Developed with Principal Engineering standards for Tao Lab.*
