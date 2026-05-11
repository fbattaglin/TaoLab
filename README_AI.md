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
- **Frequentist A/B**: Welch's T-Test + **Delta Method** for ratios.
- **Bayesian A/B**: **NumPyro (JAX)** MCMC. Posteriors, 95% HDI, and ROPE.
- **Time-Series Intervention**: **CausalPy** counterfactual estimation.
- **Observational Causal Inference**: **DoWhy** + **EconML (Double ML)**.

### 4. Statistical Guardrails (Non-negotiables)
- **SRM Check**: Chi-square (p < 0.001) is mandatory.
- **FDR Correction**: Benjamini-Hochberg applied automatically to multiple KPIs.

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
