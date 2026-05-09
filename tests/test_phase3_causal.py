import polars as pl
import numpy as np
from tao_lab.methods.causal_inference import CausalInference
from tao_lab.methods.base import ExperimentConfig

def test_causal_inference():
    # 1. Generate Synthetic Observational Data
    # Y = 2*T + 0.5*W + noise
    # T = sigmoid(0.8*W) + noise (Treatment selection bias)
    np.random.seed(42)
    n = 1000
    W = np.random.normal(0, 1, n)
    T_prob = 1 / (1 + np.exp(-0.8 * W))
    T = np.random.binomial(1, T_prob)
    Y = 2.0 * T + 0.5 * W + np.random.normal(0, 0.5, n)
    
    df = pl.DataFrame({
        "treatment": T,
        "confounder": W,
        "outcome": Y
    })
    
    config = ExperimentConfig(
        assignment_col="treatment",
        control_val="", treatment_val="",
        metric_cols=["outcome"],
        covariate_cols=["confounder"]
    )
    
    # 2. Run Analysis
    method = CausalInference()
    result = method.fit(df, config)
    
    print(f"Method: {result.method_name}")
    print(f"ATE Estimate: {result.metrics[0].lift_absolute:.4f}")
    print(f"95% CI: [{result.metrics[0].ci_lower:.4f}, {result.metrics[0].ci_upper:.4f}]")
    
    # Expected ATE is 2.0
    assert 1.8 < result.metrics[0].lift_absolute < 2.2
    assert result.metrics[0].is_significant
    assert "propensity_scores" in result.diagnostics
    
    print("✅ Causal Inference (DML/EconML) Passed")

if __name__ == "__main__":
    test_causal_inference()
