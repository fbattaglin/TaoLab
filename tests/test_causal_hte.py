"""Test Heterogeneous Treatment Effects (CausalForestDML).

Uses a known DGP where true_cate = 5000 + 2000*(age > 45),
so age should be the top feature and upper quartiles should
have higher CATE than lower quartiles.
"""
import numpy as np
import polars as pl
from tao_lab.methods.causal_inference import CausalInference
from tao_lab.methods.base import ExperimentConfig


def test_causal_hte():
    # 1. Generate synthetic data with known heterogeneous effects
    np.random.seed(42)
    n = 3000
    age = np.random.uniform(25, 65, n)
    income = np.random.lognormal(10.5, 0.6, n)
    educ = np.random.randint(8, 18, n).astype(float)

    # Treatment: higher income → more likely to participate
    logit_p = -2 + 0.8 * np.log(income / 30000) + 0.02 * age
    T = np.random.binomial(1, 1 / (1 + np.exp(-logit_p)))

    # Outcome with HETEROGENEOUS effect: effect = 5000 + 2000*(age > 45)
    true_cate = 5000 + 2000 * (age > 45).astype(float)
    Y = 0.08 * income + 300 * age + true_cate * T + np.random.normal(0, 5000, n)

    df = pl.DataFrame({
        "treatment": T,
        "outcome": Y,
        "age": age,
        "income": income,
        "educ": educ,
    })

    config = ExperimentConfig(
        assignment_col="treatment",
        control_val="",
        treatment_val="",
        metric_cols=["outcome"],
        covariate_cols=["age", "income", "educ"],
        method_params={
            "hte_enabled": True,
            "hte_features": ["age", "income", "educ"],
        },
    )

    # 2. Run analysis
    method = CausalInference()
    result = method.fit(df, config)

    print(f"Method: {result.method_name}")
    print(f"ATE (LinearDML): {result.metrics[0].lift_absolute:.0f}")
    print(f"ATE CI: [{result.metrics[0].ci_lower:.0f}, {result.metrics[0].ci_upper:.0f}]")

    # 3. ATE should be reasonable (true ATE ≈ 5000 + 1000 = 6000 average)
    ate = result.metrics[0].lift_absolute
    assert 3000 < ate < 9000, f"ATE {ate:.0f} outside expected range"

    # 4. HTE should exist
    assert result.hte is not None, "HTE result is None"
    hte = result.hte

    print(f"\nHTE: ATE from forest = {hte.ate_from_forest:.0f}")
    print(f"HTE: forest CI = [{hte.ate_forest_ci[0]:.0f}, {hte.ate_forest_ci[1]:.0f}]")
    print(f"HTE: CATE range = [{min(hte.cate_values):.0f}, {max(hte.cate_values):.0f}]")
    print(f"HTE: feature importances = {hte.feature_importances}")

    # 5. Age should be the top feature (it drives the heterogeneity)
    assert hte.feature_importances["age"] > hte.feature_importances["educ"], \
        "Age should be more important than education for heterogeneity"

    # 6. Subgroups should exist
    assert len(hte.subgroups) > 0, "No subgroup effects computed"
    age_subgroups = [s for s in hte.subgroups if s.feature == "age"]
    assert len(age_subgroups) >= 3, f"Expected ≥3 age subgroups, got {len(age_subgroups)}"

    # 7. Older quartiles should have higher CATE (true effect +2000 for age>45)
    q1_cate = age_subgroups[0].mean_cate
    q4_cate = age_subgroups[-1].mean_cate
    print(f"\nAge Q1 CATE: {q1_cate:.0f} (true ≈ 5000)")
    print(f"Age Q4 CATE: {q4_cate:.0f} (true ≈ 7000)")
    assert q4_cate > q1_cate, \
        f"Older group should benefit more: Q4={q4_cate:.0f} vs Q1={q1_cate:.0f}"

    # 8. CATE values should have correct length
    assert len(hte.cate_values) == n, \
        f"Expected {n} CATE values, got {len(hte.cate_values)}"
    assert len(hte.cate_ci_lower) == n
    assert len(hte.cate_ci_upper) == n

    print("\n✅ Causal HTE Passed")


def test_causal_without_hte():
    """Verify that disabling HTE produces no HTE result (backward compat)."""
    np.random.seed(42)
    n = 1000
    W = np.random.normal(0, 1, n)
    T = np.random.binomial(1, 0.5, n)
    Y = 2.0 * T + 0.5 * W + np.random.normal(0, 0.5, n)

    df = pl.DataFrame({"treatment": T, "confounder": W, "outcome": Y})
    config = ExperimentConfig(
        assignment_col="treatment",
        control_val="",
        treatment_val="",
        metric_cols=["outcome"],
        covariate_cols=["confounder"],
    )

    method = CausalInference()
    result = method.fit(df, config)

    assert result.hte is None, "HTE should be None when not enabled"
    assert 1.5 < result.metrics[0].lift_absolute < 2.5

    print("✅ Causal without HTE — backward compat OK")


if __name__ == "__main__":
    test_causal_hte()
    test_causal_without_hte()
