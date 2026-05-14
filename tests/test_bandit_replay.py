"""Tests for the Thompson Sampling replay simulation (MAB Regret Simulator).

Each test uses a synthetic DGP with known properties so we can assert
meaningful bounds on regret, convergence, and allocation.
"""

import numpy as np
import polars as pl
import pandas as pd

from tao_lab.methods.bandit_replay import simulate_bandit


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_daily_binary(
    n_days: int = 30,
    users_per_day: int = 200,
    p_control: float = 0.10,
    p_treatment: float = 0.15,
    seed: int = 42,
) -> pl.DataFrame:
    """Generate daily binary (0/1) A/B test data with timestamps."""
    rng = np.random.RandomState(seed)
    rows = []
    for day_offset in range(n_days):
        date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=day_offset)
        for _ in range(users_per_day):
            variant = rng.choice(["control", "treatment"])
            p = p_control if variant == "control" else p_treatment
            converted = int(rng.random() < p)
            rows.append({"date": date, "variant": variant, "converted": converted})
    return pl.DataFrame(rows)


def _make_daily_continuous(
    n_days: int = 30,
    users_per_day: int = 100,
    mu_control: float = 10.0,
    mu_treatment: float = 12.0,
    sigma: float = 3.0,
    seed: int = 42,
) -> pl.DataFrame:
    """Generate daily continuous A/B test data with timestamps."""
    rng = np.random.RandomState(seed)
    rows = []
    for day_offset in range(n_days):
        date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=day_offset)
        for _ in range(users_per_day):
            variant = rng.choice(["control", "treatment"])
            mu = mu_control if variant == "control" else mu_treatment
            revenue = max(0, rng.normal(mu, sigma))
            rows.append({"date": date, "variant": variant, "revenue": revenue})
    return pl.DataFrame(rows)


def _make_no_timestamp(
    n_users: int = 3000,
    mu_control: float = 10.0,
    mu_treatment: float = 12.0,
    sigma: float = 3.0,
    seed: int = 42,
) -> pl.DataFrame:
    """Generate A/B test data without timestamps."""
    rng = np.random.RandomState(seed)
    variants = rng.choice(["control", "treatment"], size=n_users)
    revenues = []
    for v in variants:
        mu = mu_control if v == "control" else mu_treatment
        revenues.append(max(0, rng.normal(mu, sigma)))
    return pl.DataFrame({"variant": variants.tolist(), "revenue": revenues})


# ── Tests ────────────────────────────────────────────────────────────────

def test_bandit_daily_binary():
    """Daily mode: TS should converge to winner and reduce regret (binary)."""
    df = _make_daily_binary(n_days=30, users_per_day=200, p_control=0.10, p_treatment=0.15)

    result = simulate_bandit(
        df=df,
        timestamp_col="date",
        assignment_col="variant",
        metric_col="converted",
        control_val="control",
        treatment_val="treatment",
    )

    assert result is not None, "Should return result for 30 days of data"
    assert result.mode == "daily"
    assert result.metric_type == "binary"
    assert result.winner == "treatment"
    assert result.regret_saved > 0, f"Regret saved should be positive, got {result.regret_saved}"
    assert result.final_allocation > 0.65, f"Final allocation to winner should exceed 65%, got {result.final_allocation:.2f}"
    assert result.convergence_period is not None, "Should converge within 30 days"
    assert result.convergence_period <= 25, f"Should converge before day 25, got {result.convergence_period}"
    assert result.n_periods == 30
    assert len(result.period_labels) == 30
    assert len(result.cumulative_ab) == 30

    print(f"✅ Daily binary: regret_saved={result.regret_saved:.1f} "
          f"({result.regret_saved_pct:.0%}), convergence=day {result.convergence_period}, "
          f"final_alloc={result.final_allocation:.0%}")


def test_bandit_daily_continuous():
    """Daily mode: Normal-Normal Thompson Sampling on revenue metric."""
    df = _make_daily_continuous(n_days=30, users_per_day=100, mu_control=10.0, mu_treatment=12.0)

    result = simulate_bandit(
        df=df,
        timestamp_col="date",
        assignment_col="variant",
        metric_col="revenue",
        control_val="control",
        treatment_val="treatment",
    )

    assert result is not None
    assert result.mode == "daily"
    assert result.metric_type == "continuous"
    assert result.winner == "treatment"
    assert result.regret_saved > 0, f"Regret saved should be positive, got {result.regret_saved}"
    assert result.cumulative_reward_bandit > result.cumulative_reward_ab, \
        "Bandit should accumulate more reward than AB"

    print(f"✅ Daily continuous: regret_saved={result.regret_saved:.1f} "
          f"({result.regret_saved_pct:.0%}), convergence=period {result.convergence_period}")


def test_bandit_sequential_no_timestamps():
    """Sequential mode: works without timestamps using batch aggregation."""
    df = _make_no_timestamp(n_users=3000, mu_control=10.0, mu_treatment=12.0)

    result = simulate_bandit(
        df=df,
        timestamp_col=None,  # no timestamps
        assignment_col="variant",
        metric_col="revenue",
        control_val="control",
        treatment_val="treatment",
    )

    assert result is not None, "Should return result for 3000 users without timestamps"
    assert result.mode == "sequential"
    assert result.metric_type == "continuous"
    assert result.regret_saved > 0, f"Regret saved should be positive, got {result.regret_saved}"
    assert result.n_periods >= 7, f"Should have at least 7 periods, got {result.n_periods}"
    # Labels should be ranges like "0–100"
    assert "–" in result.period_labels[0], f"Sequential labels should be ranges, got {result.period_labels[0]}"

    print(f"✅ Sequential (no timestamps): mode={result.mode}, "
          f"periods={result.n_periods}, regret_saved={result.regret_saved:.1f} "
          f"({result.regret_saved_pct:.0%})")


def test_bandit_no_winner():
    """Both arms identical → simulation stays near 50/50, minimal regret saved."""
    df = _make_daily_continuous(
        n_days=30, users_per_day=100,
        mu_control=10.0, mu_treatment=10.0,  # identical arms
        seed=42,
    )

    result = simulate_bandit(
        df=df,
        timestamp_col="date",
        assignment_col="variant",
        metric_col="revenue",
        control_val="control",
        treatment_val="treatment",
    )

    assert result is not None
    # With identical arms, allocation should stay near 50%
    assert 0.25 <= result.final_allocation <= 0.75, \
        f"With identical arms, final allocation should be near 50%, got {result.final_allocation:.2f}"
    # Regret saved should be near zero (both arms are the same)
    if result.regret_ab > 0:
        assert result.regret_saved_pct < 0.15, \
            f"With identical arms, regret_saved_pct should be small, got {result.regret_saved_pct:.2f}"

    print(f"✅ No winner: final_alloc={result.final_allocation:.0%}, "
          f"regret_saved_pct={result.regret_saved_pct:.0%}")


def test_bandit_insufficient_periods():
    """Returns None when fewer than min_periods after aggregation."""
    # Only 3 days — below the default min_periods=7
    df = _make_daily_continuous(n_days=3, users_per_day=50)

    result = simulate_bandit(
        df=df,
        timestamp_col="date",
        assignment_col="variant",
        metric_col="revenue",
        control_val="control",
        treatment_val="treatment",
    )

    assert result is None, "Should return None for only 3 days of data"
    print("✅ Insufficient periods: correctly returned None")


def test_bandit_deterministic():
    """Same seed produces identical results (reproducibility)."""
    df = _make_daily_binary(n_days=20, users_per_day=150)

    result1 = simulate_bandit(
        df=df,
        timestamp_col="date",
        assignment_col="variant",
        metric_col="converted",
        control_val="control",
        treatment_val="treatment",
        random_seed=42,
    )
    result2 = simulate_bandit(
        df=df,
        timestamp_col="date",
        assignment_col="variant",
        metric_col="converted",
        control_val="control",
        treatment_val="treatment",
        random_seed=42,
    )

    assert result1 is not None and result2 is not None
    assert result1.cumulative_reward_bandit == result2.cumulative_reward_bandit
    assert result1.regret_saved == result2.regret_saved
    assert result1.allocation_to_winner == result2.allocation_to_winner
    print("✅ Deterministic: identical results with same seed")


if __name__ == "__main__":
    test_bandit_daily_binary()
    test_bandit_daily_continuous()
    test_bandit_sequential_no_timestamps()
    test_bandit_no_winner()
    test_bandit_insufficient_periods()
    test_bandit_deterministic()
    print("\n🎯 All MAB Regret Simulator tests passed!")
