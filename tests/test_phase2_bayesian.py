import polars as pl
import numpy as np
from tao_lab.methods.bayesian_ab import BayesianABTest
from tao_lab.methods.base import ExperimentConfig

def test_bayesian_ab():
    np.random.seed(42)
    n = 500 # Smaller N for faster test
    
    groups = ["control"] * (n // 2) + ["treatment"] * (n // 2)
    np.random.shuffle(groups)
    
    metrics = []
    for g in groups:
        if g == "control":
            metrics.append(np.random.normal(10, 1))
        else:
            metrics.append(np.random.normal(11, 1)) # +1 lift
            
    df = pl.DataFrame({
        "group": groups,
        "revenue": metrics
    })
    
    config = ExperimentConfig(
        assignment_col="group",
        control_val="control",
        treatment_val="treatment",
        metric_cols=["revenue"],
        method_params={"rope_threshold": 0.01}
    )
    
    method = BayesianABTest()
    result = method.fit(df, config)
    
    print(f"Method: {result.method_name}")
    for m in result.metrics:
        print(f"Metric: {m.metric_name}, Lift Rel: {m.lift_relative:.4f}, Significant: {m.is_significant}")
        print(f"Diagnostics: {m.warning_message}")
        
    assert result.metrics[0].lift_relative > 0.05
    assert result.metrics[0].is_significant
    print("✅ Bayesian A/B Test (NumPyro) Passed")

if __name__ == "__main__":
    test_bayesian_ab()
