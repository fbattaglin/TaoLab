# ☯️ Tao Lab
### *The Art of Experimental Zen.*

[![Built with Polars](https://img.shields.io/badge/Data%20Engine-Polars-CD792C?style=flat-square)](https://pola.rs/)
[![Powered by NumPyro](https://img.shields.io/badge/Bayesian-NumPyro-629232?style=flat-square)](https://num.pyro.ai/)
[![Causal with DoWhy](https://img.shields.io/badge/Causal-DoWhy-1E3A5F?style=flat-square)](https://py-why.github.io/dowhy/)

**Tao Lab** is where statistical rigour meets premium design. It’s an experimentation platform for Data Scientists who are tired of messy notebooks and "just run a t-test" scripts. We bridge the gap between simple A/B tests and advanced Causal Inference, delivering a verdict you can actually bet your business on.

---

## 🧘 The Five-Step Flow

We don’t just run numbers; we guide you through a path of enlightenment:

1.  **Data** — Feed the machine your CSV or Excel file. We love Polars, so we digest it faster than you can say "vectorized operations".
2.  **Diagnose** — Our engine sniffs your data to find the best method. Bayesian? Causal? Time-Series? We’ll tell you what fits (and warn you if your data is "fubento").
3.  **Configure** — Tweak the knobs. Define your control, your treatment, and your success metrics. We handle Ratio Metrics with the **Delta Method** because we aren't amateurs.
4.  **Run** — Watch the magic happen. We check for **SRM (Sample Ratio Mismatch)** and apply **Multiple Testing Corrections** automatically. No p-hacking allowed.
5.  **Prescription** — The hero moment. A beautiful, React-powered deliverable that tells you exactly what to do: *Ship it, Hold, or Kill it.*

---

## 🧠 Smart Under the Hood

Tao Lab isn't just a pretty face. It’s a statistical powerhouse:

-   🚀 **Polars-First**: Sub-millisecond data wrangling.
-   🎲 **Bayesian Engine**: Powered by **NumPyro (JAX)** for those who want probability statements instead of confusing p-values.
-   🔮 **Causal Inference**: Identification via **DoWhy** and estimation via **EconML (DML)**. For when you didn't randomise, but still want the truth.
-   📉 **Interrupted Time-Series**: Using **CausalPy** to see the counterfactual "what if" of your interventions.

---

## 💅 Aesthetics & DX

-   **Premium Light Mode**: A forced, high-contrast aesthetic that stays beautiful even if your OS is having a dark-mode identity crisis.
-   **React + Tailwind**: Custom-built UI components (Stepper, Verdict Banner, Prescription Card) that live in perfect harmony with Streamlit.
-   **uv Magic**: Built for the future of Python package management. Zero dependency hell.

---

## 🚀 Get Zen in 60 Seconds

### 1. Initialise the Lab
```bash
uv run scripts/fetch_datasets.py
```

### 2. Launch the Enlightenment
```bash
uv run streamlit run tao_lab/ui/app.py
```

### 3. Verify the Truth
```bash
uv run python3 tests/test_final_mvp.py
```

---

## ❓ Why "Tao"?
In philosophy, the **Tao** is the natural order of the universe. In data, the Tao is the signal hidden within the noise. **Tao Lab** is your tool for finding that balance—rigorous enough for the PhDs, but clear enough for the CEOs.

*Stay sharp. Stay smart. Ship with confidence.* 🚀☯️
