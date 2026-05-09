# Tao Lab Architectural Standards

## Core Philosophy
Tao Lab is a modular platform where every analysis type is a "plugin" implementing a strict interface.

## Module Interfaces

### Method Interface (`tao_lab.methods.base.Method`)
Every statistical method must inherit from this class.

```python
class Method(ABC):
    @abstractmethod
    def fit(self, data: pl.DataFrame, config: Dict) -> AnalysisResult:
        """Execute the statistical analysis."""
        pass

    @abstractmethod
    def diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic metrics (e.g., convergence, SRM)."""
        pass

    @abstractmethod
    def visualize(self, result: AnalysisResult) -> List[go.Figure]:
        """Return a list of plotly figures for the UI."""
        pass
```

## Implementation Rules

1. **Polars First**: Data ingestion and internal cleaning must use `polars`. Convert to `pandas` ONLY at the boundary of external libraries (e.g., statsmodels, econml).
2. **Lazy Imports**: Heavy libraries (NumPyro, PyMC, Jax, CausalPy) MUST be imported inside the `fit` or `visualize` methods of their respective modules to keep the Streamlit UI snappy.
3. **Structured Results**: Use Pydantic models for all result objects to ensure the LLM narration and UI can rely on a stable schema.
4. **Mandatory SRM**: The `Method` runner must execute `tao_lab.checks.srm` before returning results.

## UI Standards
- **Semaphore Colors**: 
    - Success/Safe: `#059669` (Success Green)
    - Warning/Marginal: `#D97706` (Warning Amber)
    - Danger/Invalid: `#DC2626` (Danger Red)
- **Precision**: 3 significant figures by default.
- **Theming**: **Forced Light Mode Only**. All CSS variables are defined in `tao_lab/ui/static/style.css` with `!important` to prevent OS-level overrides.
