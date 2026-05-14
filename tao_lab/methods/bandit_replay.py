"""Thompson Sampling replay simulation for A/B test data.

Not a Method subclass — this is a post-hoc insight, not a primary analysis.
Compares fixed (50/50) allocation against adaptive Thompson Sampling using
the observed data from an A/B test.

Two modes:
  - Daily: when timestamps are available, aggregates by day.
  - Sequential: when no timestamps, shuffles and batches observations.

Both modes use the same core simulation loop — the preparation step produces
a uniform ``List[PeriodStats]`` structure that the loop consumes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import polars as pl
from scipy.stats import norm

from tao_lab.methods.base import BanditReplayResult


# ── Internal data structure ─────────────────────────────────────────────

@dataclass
class PeriodStats:
    """Aggregated stats for one period (day or batch) for both arms."""

    label: str  # date string or "0–100"
    n_control: int
    n_treatment: int
    sum_control: float
    sum_treatment: float
    mean_control: float
    mean_treatment: float


# ── Public entry point ──────────────────────────────────────────────────

def simulate_bandit(
    df: pl.DataFrame,
    timestamp_col: Optional[str],
    assignment_col: str,
    metric_col: str,
    control_val,
    treatment_val,
    *,
    date_format: Optional[str] = None,
    n_mc_samples: int = 1000,
    min_periods: int = 7,
    batch_size: int = 100,
    random_seed: int = 42,
) -> Optional[BanditReplayResult]:
    """Run Thompson Sampling replay on A/B test data.

    Parameters
    ----------
    timestamp_col : str or None
        Column name for timestamps.  When ``None``, uses sequential batch mode.
    min_periods : int
        Minimum number of periods (days or batches) required to run.
    batch_size : int
        Approximate observations per batch in sequential mode.

    Returns
    -------
    BanditReplayResult or None
        ``None`` when there is insufficient data.
    """
    metric_type = _detect_metric_type(df, metric_col)

    if timestamp_col is not None:
        periods = _prepare_daily_aggregates(
            df, timestamp_col, assignment_col, metric_col,
            control_val, treatment_val, date_format,
        )
        mode = "daily"
    else:
        periods = _prepare_sequential_batches(
            df, assignment_col, metric_col,
            control_val, treatment_val, batch_size, random_seed,
        )
        mode = "sequential"

    if len(periods) < min_periods:
        return None

    # ── Determine which arm is the overall winner ──
    total_sum_c = sum(p.sum_control for p in periods)
    total_sum_t = sum(p.sum_treatment for p in periods)
    total_n_c = sum(p.n_control for p in periods)
    total_n_t = sum(p.n_treatment for p in periods)
    overall_mean_c = total_sum_c / max(total_n_c, 1)
    overall_mean_t = total_sum_t / max(total_n_t, 1)
    winner_is_treatment = overall_mean_t >= overall_mean_c

    # ── Run the simulation ──
    sim = _run_thompson_sampling(
        periods, metric_type, n_mc_samples, random_seed,
        winner_is_treatment,
    )

    # ── Convergence detection ──
    convergence = _detect_convergence(sim["allocation_to_winner"])

    # ── Regret calculations ──
    cum_ab = sim["cumulative_ab"][-1]
    cum_bandit = sim["cumulative_bandit"][-1]
    cum_optimal = sim["cumulative_optimal"][-1]
    regret_ab = cum_optimal - cum_ab
    regret_bandit = cum_optimal - cum_bandit
    regret_saved = regret_ab - regret_bandit
    regret_saved_pct = regret_saved / regret_ab if abs(regret_ab) > 1e-9 else 0.0

    winner_val = str(treatment_val) if winner_is_treatment else str(control_val)

    return BanditReplayResult(
        mode=mode,
        n_periods=len(periods),
        n_observations=total_n_c + total_n_t,
        metric_name=metric_col,
        metric_type=metric_type,
        winner=winner_val,
        cumulative_reward_ab=cum_ab,
        cumulative_reward_bandit=cum_bandit,
        cumulative_reward_optimal=cum_optimal,
        regret_ab=regret_ab,
        regret_bandit=regret_bandit,
        regret_saved=regret_saved,
        regret_saved_pct=max(0.0, min(1.0, regret_saved_pct)),
        convergence_period=convergence,
        final_allocation=sim["allocation_to_winner"][-1] if sim["allocation_to_winner"] else 0.5,
        period_labels=sim["period_labels"],
        cumulative_ab=sim["cumulative_ab"],
        cumulative_bandit=sim["cumulative_bandit"],
        cumulative_optimal=sim["cumulative_optimal"],
        allocation_to_winner=sim["allocation_to_winner"],
    )


# ── Metric type detection ───────────────────────────────────────────────

def _detect_metric_type(df: pl.DataFrame, metric_col: str) -> str:
    """Return 'binary' if all values are 0 or 1, else 'continuous'."""
    unique = df.select(pl.col(metric_col).drop_nulls().unique()).to_series()
    vals = set(unique.to_list())
    if vals.issubset({0, 1, 0.0, 1.0}):
        return "binary"
    return "continuous"


# ── Period preparation ──────────────────────────────────────────────────

def _prepare_daily_aggregates(
    df: pl.DataFrame,
    timestamp_col: str,
    assignment_col: str,
    metric_col: str,
    control_val,
    treatment_val,
    date_format: Optional[str],
) -> List[PeriodStats]:
    """Parse timestamps, truncate to day, aggregate per (day, arm)."""
    # Cast timestamp to Date in Polars before grouping
    ts_dtype = df.schema[timestamp_col]
    work = df.select([timestamp_col, assignment_col, metric_col])

    if ts_dtype == pl.Utf8:
        fmt = date_format or "%Y-%m-%d"
        work = work.with_columns(
            pl.col(timestamp_col).str.to_date(fmt, strict=False).alias("_day")
        )
    elif ts_dtype == pl.Datetime:
        work = work.with_columns(
            pl.col(timestamp_col).dt.date().alias("_day")
        )
    elif ts_dtype == pl.Date:
        work = work.with_columns(pl.col(timestamp_col).alias("_day"))
    else:
        # Fallback: try casting
        work = work.with_columns(
            pl.col(timestamp_col).cast(pl.Date, strict=False).alias("_day")
        )

    # Drop rows where date parsing failed
    work = work.filter(pl.col("_day").is_not_null())

    # Aggregate per (day, arm)
    agg = (
        work.group_by(["_day", assignment_col])
        .agg([
            pl.col(metric_col).count().alias("n"),
            pl.col(metric_col).sum().alias("total"),
            pl.col(metric_col).mean().alias("mean"),
        ])
        .sort("_day")
    )

    # Pivot into PeriodStats
    days = sorted(agg.select("_day").unique().to_series().to_list())
    periods: List[PeriodStats] = []
    for day in days:
        day_data = agg.filter(pl.col("_day") == day)
        ctrl = day_data.filter(pl.col(assignment_col) == control_val)
        treat = day_data.filter(pl.col(assignment_col) == treatment_val)

        n_c = int(ctrl.select("n").item()) if ctrl.height > 0 else 0
        n_t = int(treat.select("n").item()) if treat.height > 0 else 0
        sum_c = float(ctrl.select("total").item()) if ctrl.height > 0 else 0.0
        sum_t = float(treat.select("total").item()) if treat.height > 0 else 0.0
        mean_c = float(ctrl.select("mean").item()) if ctrl.height > 0 and n_c > 0 else 0.0
        mean_t = float(treat.select("mean").item()) if treat.height > 0 and n_t > 0 else 0.0

        if n_c + n_t == 0:
            continue

        periods.append(PeriodStats(
            label=str(day),
            n_control=n_c,
            n_treatment=n_t,
            sum_control=sum_c,
            sum_treatment=sum_t,
            mean_control=mean_c,
            mean_treatment=mean_t,
        ))

    return periods


def _prepare_sequential_batches(
    df: pl.DataFrame,
    assignment_col: str,
    metric_col: str,
    control_val,
    treatment_val,
    batch_size: int,
    random_seed: int,
) -> List[PeriodStats]:
    """Shuffle the DataFrame and chunk into batches of ~batch_size observations."""
    # Shuffle for i.i.d. simulation
    n = df.height
    rng = np.random.RandomState(random_seed)
    indices = rng.permutation(n)
    shuffled = df.select([assignment_col, metric_col])[indices.tolist()]

    # Determine actual batch size: aim for ~30 periods
    actual_batch = max(batch_size, n // 30) if n > 30 * batch_size else batch_size

    periods: List[PeriodStats] = []
    for start in range(0, n, actual_batch):
        end = min(start + actual_batch, n)
        chunk = shuffled.slice(start, end - start)

        ctrl = chunk.filter(pl.col(assignment_col) == control_val)
        treat = chunk.filter(pl.col(assignment_col) == treatment_val)

        n_c = ctrl.height
        n_t = treat.height
        if n_c + n_t == 0:
            continue

        sum_c = float(ctrl.select(pl.col(metric_col).sum()).item()) if n_c > 0 else 0.0
        sum_t = float(treat.select(pl.col(metric_col).sum()).item()) if n_t > 0 else 0.0
        mean_c = float(ctrl.select(pl.col(metric_col).mean()).item()) if n_c > 0 else 0.0
        mean_t = float(treat.select(pl.col(metric_col).mean()).item()) if n_t > 0 else 0.0

        periods.append(PeriodStats(
            label=f"{start:,}–{end:,}",
            n_control=n_c,
            n_treatment=n_t,
            sum_control=sum_c,
            sum_treatment=sum_t,
            mean_control=mean_c,
            mean_treatment=mean_t,
        ))

    return periods


# ── Core Thompson Sampling loop ─────────────────────────────────────────

def _run_thompson_sampling(
    periods: List[PeriodStats],
    metric_type: str,
    n_mc_samples: int,
    random_seed: int,
    winner_is_treatment: bool,
) -> dict:
    """Run the TS simulation over prepared periods.

    Returns a dict with per-period arrays for charting.
    """
    rng = np.random.RandomState(random_seed)

    # Posterior state
    if metric_type == "binary":
        alpha_c, beta_c = 1.0, 1.0
        alpha_t, beta_t = 1.0, 1.0
    else:
        # Normal-Normal: start with weak prior based on first period
        first = periods[0]
        grand_mean = (first.sum_control + first.sum_treatment) / max(
            first.n_control + first.n_treatment, 1
        )
        # Prior: N(grand_mean, large_var) → effectively non-informative
        mu_c, mu_t = grand_mean, grand_mean
        n_obs_c, n_obs_t = 0.01, 0.01  # pseudo-count for prior weight
        sum_c, sum_t = grand_mean * n_obs_c, grand_mean * n_obs_t
        # Estimate variance from first period (pooled)
        var_est = max(
            (first.mean_control - grand_mean) ** 2
            + (first.mean_treatment - grand_mean) ** 2
            + 1.0,  # floor to prevent zero variance
            1.0,
        )

    # Accumulators
    cum_ab = 0.0
    cum_bandit = 0.0
    cum_optimal = 0.0

    result = {
        "period_labels": [],
        "cumulative_ab": [],
        "cumulative_bandit": [],
        "cumulative_optimal": [],
        "allocation_to_winner": [],
    }

    for period in periods:
        n_total = period.n_control + period.n_treatment

        # ── Compute allocation fraction (prob that treatment > control) ──
        if metric_type == "binary":
            p_treat = _allocation_fraction_beta(
                alpha_c, beta_c, alpha_t, beta_t, n_mc_samples, rng,
            )
        else:
            p_treat = _allocation_fraction_normal(mu_c, n_obs_c, mu_t, n_obs_t, var_est)

        # ── Compute rewards ──
        ab_reward = period.sum_control + period.sum_treatment
        bandit_reward = n_total * (
            p_treat * period.mean_treatment + (1 - p_treat) * period.mean_control
        )
        optimal_reward = n_total * max(period.mean_treatment, period.mean_control)

        cum_ab += ab_reward
        cum_bandit += bandit_reward
        cum_optimal += optimal_reward

        # ── Allocation to winner ──
        alloc_to_winner = p_treat if winner_is_treatment else (1 - p_treat)

        result["period_labels"].append(period.label)
        result["cumulative_ab"].append(cum_ab)
        result["cumulative_bandit"].append(cum_bandit)
        result["cumulative_optimal"].append(cum_optimal)
        result["allocation_to_winner"].append(alloc_to_winner)

        # ── Update posterior ──
        if metric_type == "binary":
            # Beta-Binomial update
            alpha_c += period.sum_control
            beta_c += period.n_control - period.sum_control
            alpha_t += period.sum_treatment
            beta_t += period.n_treatment - period.sum_treatment
        else:
            # Normal-Normal update (running sufficient statistics)
            sum_c += period.sum_control
            sum_t += period.sum_treatment
            n_obs_c += period.n_control
            n_obs_t += period.n_treatment
            mu_c = sum_c / n_obs_c
            mu_t = sum_t / n_obs_t

    return result


# ── Allocation fraction helpers ─────────────────────────────────────────

def _allocation_fraction_beta(
    alpha_c: float,
    beta_c: float,
    alpha_t: float,
    beta_t: float,
    n_samples: int,
    rng: np.random.RandomState,
) -> float:
    """Monte Carlo estimate of P(treatment > control) for Beta posteriors."""
    samples_c = rng.beta(alpha_c, beta_c, size=n_samples)
    samples_t = rng.beta(alpha_t, beta_t, size=n_samples)
    return float(np.mean(samples_t > samples_c))


def _allocation_fraction_normal(
    mu_c: float,
    n_c: float,
    mu_t: float,
    n_t: float,
    var_est: float,
) -> float:
    """Analytical P(treatment > control) for Normal posteriors.

    P(T > C) = Φ((μ_t - μ_c) / √(σ²/n_t + σ²/n_c))
    """
    se = np.sqrt(var_est / max(n_t, 0.01) + var_est / max(n_c, 0.01))
    if se < 1e-12:
        return 0.5
    z = (mu_t - mu_c) / se
    return float(norm.cdf(z))


# ── Convergence detection ───────────────────────────────────────────────

def _detect_convergence(
    allocations: List[float],
    threshold: float = 0.75,
) -> Optional[int]:
    """Return the first period index where allocation to winner >= threshold.

    Returns None if never reached.
    """
    for i, alloc in enumerate(allocations):
        if alloc >= threshold:
            return i + 1  # 1-indexed (day 1, not day 0)
    return None
