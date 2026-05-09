import polars as pl
import numpy as np
from tao_lab.methods.ab_test import FrequentistABTest
from tao_lab.methods.base import ExperimentConfig, RatioMetric

def test_full_ab_workflow():
    # 1. Generate Synthetic Data
    np.random.seed(42)
    n = 2000
    
    # Balanced groups
    groups = ["control"] * (n // 2) + ["treatment"] * (n // 2)
    np.random.shuffle(groups)
    
    # Continuous Metric (e.g., sessions)
    sessions = []
    # Ratio Metric Components (e.g., clicks and impressions)
    clicks = []
    impressions = []
    
    for g in groups:
        if g == "control":
            sessions.append(np.random.normal(10, 2))
            imp = np.random.poisson(100)
            clk = np.random.binomial(imp, 0.05) # 5% CTR
        else:
            sessions.append(np.random.normal(11, 2)) # +1 lift
            imp = np.random.poisson(100)
            clk = np.random.binomial(imp, 0.06) # 6% CTR (+1% abs lift)
        
        impressions.append(imp)
        clicks.append(clk)
            
    df = pl.DataFrame({
        "group": groups,
        "sessions": sessions,
        "clicks": clicks,
        "impressions": impressions
    })
    
    config = ExperimentConfig(
        assignment_col="group",
        control_val="control",
        treatment_val="treatment",
        metric_cols=["sessions"],
        ratio_metrics=[
            RatioMetric(name="CTR", numerator_col="clicks", denominator_col="impressions")
        ],
        expected_ratio={"control": 0.5, "treatment": 0.5}
    )
    
    # 2. Run Analysis
    method = FrequentistABTest()
    result = method.fit(df, config)
    
    # 3. Assertions
    print(f"SRM p-value: {result.srm_p_value}")
    assert not result.srm_detected
    
    # Continuous Metric Check
    sessions_res = [m for m in result.metrics if m.metric_name == "sessions"][0]
    print(f"Sessions Lift: {sessions_res.lift_absolute:.4f}, p: {sessions_res.p_value:.4f}")
    assert sessions_res.is_significant
    assert 0.8 < sessions_res.lift_absolute < 1.2
    
    # Ratio Metric Check (Delta Method)
    ctr_res = [m for m in result.metrics if m.metric_name == "CTR"][0]
    print(f"CTR Lift: {ctr_res.lift_absolute:.4f}, p: {ctr_res.p_value:.4f}")
    assert ctr_res.is_significant
    assert 0.005 < ctr_res.lift_absolute < 0.015
    
    # Multiple Testing Check
    # (Since both are significant and we have 2 metrics, p-values should be adjusted)
    # Both should still be significant given the large effect and sample size
    assert len(result.metrics) == 2
    
    print("✅ Full A/B Workflow with Ratio Metrics & Multiple Testing Passed")

if __name__ == "__main__":
    test_full_ab_workflow()
