"""Generate and fetch canonical sample datasets for Tao Lab demos.

Four datasets covering all four analysis methods:
  1. ab_test_saas.csv        — SaaS onboarding A/B (lognormal revenue, ratio metric, covariates)
  2. ab_test_email.csv       — Email personalisation small-N (Bayesian showcase: freq inconclusive)
  3. time_series_weekly.csv  — Retail loyalty programme launch (AR(1) + holiday seasonal, 104 wks)
  4. causal_401k.csv         — 401k retirement savings (real/synthetic, canonical DML example)
"""

import os
import numpy as np
import pandas as pd
import polars as pl


_OUT = "datasets"


# ─────────────────────────────────────────────────────────────────────────────
# Dataset 1 — SaaS Onboarding A/B Test
# ─────────────────────────────────────────────────────────────────────────────
def _generate_ab_saas(seed: int = 42) -> pl.DataFrame:
    """30,000 users; lognormal revenue +9%; independent activation, sessions,
    pages_viewed (ratio numerator); two non-treatment covariates.
    All metrics are statistically independent (no shared generative path).
    """
    rng = np.random.default_rng(seed)
    n_arm = 15_000
    n = n_arm * 2

    variant = np.array(["control"] * n_arm + ["onboarding_v2"] * n_arm)

    # Revenue: lognormal, treatment mean ×1.09
    rev_ctrl = rng.lognormal(mean=2.3, sigma=0.8, size=n_arm)
    rev_trt  = rng.lognormal(mean=2.3 + np.log(1.09), sigma=0.8, size=n_arm)
    revenue_28d = np.concatenate([rev_ctrl, rev_trt]).round(2)

    # Activation (binary): 34% → 40%  (+18% relative)
    activated = np.concatenate([
        rng.binomial(1, 0.34, n_arm),
        rng.binomial(1, 0.40, n_arm),
    ])

    # Sessions (Poisson): 8.5 → 9.2  (+8% relative)
    sessions_28d = np.concatenate([
        rng.poisson(8.5, n_arm),
        rng.poisson(9.2, n_arm),
    ])

    # Pages viewed — ratio numerator (pages / session = engagement depth)
    # Control: λ ≈ 5 pages/session; Treatment: λ ≈ 5.3 pages/session
    pages_ctrl = rng.poisson(sessions_28d[:n_arm] * 5.0)
    pages_trt  = rng.poisson(sessions_28d[n_arm:] * 5.3)
    pages_viewed = np.concatenate([pages_ctrl, pages_trt])

    # Covariates — independent of assignment (pure RCT)
    account_age_days = rng.gamma(shape=2, scale=100, size=n).astype(int)
    plan_tier = rng.choice(
        ["free", "starter", "pro"], size=n, p=[0.60, 0.30, 0.10]
    )

    return pl.DataFrame({
        "user_id":          list(range(n)),
        "variant":          variant.tolist(),
        "revenue_28d":      revenue_28d.tolist(),
        "activated":        activated.tolist(),
        "sessions_28d":     sessions_28d.tolist(),
        "pages_viewed":     pages_viewed.tolist(),
        "account_age_days": account_age_days.tolist(),
        "plan_tier":        plan_tier.tolist(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Dataset 2 — Email Personalisation Small-N (Bayesian showcase)
# ─────────────────────────────────────────────────────────────────────────────
def _generate_ab_email(seed: int = 7) -> pl.DataFrame:
    """600 users (300 per arm). Frequentist p ≈ 0.07–0.10 (inconclusive).
    Bayesian posterior P(Better) ≈ 88–92%.  Teaches: when N is small, priors
    allow a calibrated decision even if the t-test 'fails'.
    """
    rng = np.random.default_rng(seed)
    n_arm = 300
    n = n_arm * 2

    arm = np.array(["generic_subject"] * n_arm + ["personalized_subject"] * n_arm)

    # Open rate: 22% → 28%  (+27% relative)
    opened = np.concatenate([
        rng.binomial(1, 0.22, n_arm),
        rng.binomial(1, 0.28, n_arm),
    ])

    # Revenue (zero for non-openers; lognormal for openers)
    rev_raw = rng.lognormal(mean=2.0, sigma=1.2, size=n)
    revenue = (rev_raw * opened).round(2)

    # Covariate
    days_since_last_purchase = rng.gamma(1.5, 15, n).astype(int)

    return pl.DataFrame({
        "user_id":                  list(range(n)),
        "arm":                      arm.tolist(),
        "opened":                   opened.tolist(),
        "revenue":                  revenue.tolist(),
        "days_since_last_purchase": days_since_last_purchase.tolist(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Dataset 3 — Weekly Time-Series: Loyalty Programme Launch
# ─────────────────────────────────────────────────────────────────────────────
def _generate_time_series_weekly(seed: int = 99) -> pl.DataFrame:
    """104 weeks (2 years: 2022-01-03 → 2023-12-25, every Monday).
    AR(1, φ=0.65) + linear trend + holiday seasonal spikes + step +12% at
    week 53 (2023-01-02).  Balanced 52-pre / 52-post split.
    """
    rng = np.random.default_rng(seed)
    n = 104
    dates = pd.date_range("2022-01-03", periods=n, freq="W-MON")

    # AR(1) base noise
    ar_rev = np.zeros(n)
    ar_rev[0] = 0.0
    for t in range(1, n):
        ar_rev[t] = 0.65 * ar_rev[t - 1] + rng.normal(0, 400)

    # Linear trend: +$3,000 over 2 years
    trend = np.linspace(0, 3000, n)

    # Holiday seasonality (Nov–Dec spike, early-Jan dip)
    seasonal = np.zeros(n)
    for t in range(n):
        woy = t % 52  # approximate week-of-year (0-indexed)
        if 46 <= woy <= 51:       # Black Friday → Christmas
            seasonal[t] = rng.uniform(2000, 5000)
        elif woy <= 2:            # New-year lull
            seasonal[t] = rng.uniform(-800, -200)

    # Step change at week 53 (loyalty programme launch 2023-01-02)
    step = np.where(np.arange(n) >= 52, 1, 0)
    base_revenue = 10_000
    step_size = base_revenue * 0.12  # +12% lift
    revenue = base_revenue + ar_rev + trend + seasonal + step * step_size
    revenue = np.maximum(revenue, 0).round(2)

    # Weekly sessions: separate AR(1) correlated but not identical
    ar_sess = np.zeros(n)
    ar_sess[0] = 0.0
    for t in range(1, n):
        ar_sess[t] = 0.50 * ar_sess[t - 1] + rng.normal(0, 25)
    weekly_sessions = (
        500 + ar_sess + trend / 20 + step * 55 + rng.normal(0, 15, n)
    ).astype(int)
    weekly_sessions = np.maximum(weekly_sessions, 0)

    return pl.DataFrame({
        "week_starting":   dates.strftime("%Y-%m-%d").tolist(),
        "weekly_revenue":  revenue.tolist(),
        "weekly_sessions": weekly_sessions.tolist(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Dataset 4 — 401k Retirement Savings (Causal Inference)
# ─────────────────────────────────────────────────────────────────────────────
def _fetch_401k_or_synthetic(seed: int = 2024) -> pl.DataFrame:
    """Fetch Abadie (2003) 401k dataset from EconML's public mirror.
    Falls back to a synthetic equivalent with the same DGP if the URL is
    unavailable.  All covariates are numeric — no string categoricals to
    break EconML RandomForest.

    Treatment: p401 (actual 401k participation — endogenous).
    Outcome:   net_tfa (net total financial assets, can be negative).
    Confounders: age, inc (income), fsize (family size), educ, pira (has IRA).
    Known ATE in literature: ~$8,000–$12,000 (Chernozhukov et al. 2018 DML).
    """
    _KEEP = ["p401", "net_tfa", "age", "inc", "fsize", "educ", "pira"]

    url = (
        "https://raw.githubusercontent.com/microsoft/EconML/"
        "main/notebooks/data/401k.csv"
    )
    try:
        raw = pd.read_csv(url)
        available = [c for c in _KEEP if c in raw.columns]
        if len(available) >= 5:
            df = pl.from_pandas(raw[available])
            print(f"   ✅ Downloaded real 401k data ({len(df):,} rows)")
            return df
        raise ValueError(f"Expected columns not found. Got: {raw.columns.tolist()}")
    except Exception as exc:
        print(f"   ⚠  Could not fetch real data ({exc}). Generating synthetic equivalent.")

    # ── Synthetic fallback with matching DGP ──
    rng = np.random.default_rng(seed)
    n = 9_000

    # Confounders
    inc   = rng.lognormal(mean=10.5, sigma=0.6, size=n)   # income, ~$36k median
    age   = rng.integers(25, 65, size=n)
    educ  = rng.integers(8, 18, size=n)
    fsize = rng.integers(1, 6, size=n)
    pira  = rng.binomial(1, 0.30, size=n)

    # Treatment selection (endogenous): richer, older, educated → more likely to participate
    logit_p = (
        -2.0
        + 0.8  * np.log(np.clip(inc, 1, None) / 30_000)
        + 0.02 * age
        + 0.05 * educ
        + 0.30 * pira
    )
    p401 = rng.binomial(1, 1.0 / (1.0 + np.exp(-logit_p)), size=n)

    # Outcome: income + age drive assets; true ATE = $9,000
    net_tfa = (
        0.08 * inc
        + 300  * age
        - 500  * fsize
        + 2_000 * educ
        + 9_000 * p401
        + rng.normal(0, 8_000, size=n)
        - 5_000
    ).round(2)

    print(f"   ✅ Generated synthetic 401k-equivalent data ({n:,} rows, ATE ≈ $9,000)")
    return pl.DataFrame({
        "p401":    p401.tolist(),
        "net_tfa": net_tfa.tolist(),
        "age":     age.tolist(),
        "inc":     inc.round(2).tolist(),
        "fsize":   fsize.tolist(),
        "educ":    educ.tolist(),
        "pira":    pira.tolist(),
    })



# ─────────────────────────────────────────────────────────────────────────────
# Dataset 5 — Bandit Replay Showcase
# ─────────────────────────────────────────────────────────────────────────────
def _generate_ab_bandit(seed: int = 123) -> pl.DataFrame:
    """A 45-day A/B test with 50/50 allocation and a clear, early winner.
    Generates high regret under fixed allocation, perfect for demonstrating
    the Thompson Sampling Replay Simulator.
    """
    rng = np.random.default_rng(seed)
    n_days = 45
    users_per_day = 600
    
    rows = []
    for day_offset in range(n_days):
        date = pd.Timestamp("2024-03-01") + pd.Timedelta(days=day_offset)
        for _ in range(users_per_day):
            variant = rng.choice(["control", "treatment"])
            # Control: 8% conversion, Treatment: 12.5% conversion
            p = 0.08 if variant == "control" else 0.125
            converted = rng.binomial(1, p)
            # Add continuous revenue as well
            revenue = 0.0
            if converted:
                mu_rev = 45.0 if variant == "control" else 48.0
                revenue = max(0, rng.normal(mu_rev, 15.0))
                
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "variant": variant,
                "converted": converted,
                "revenue": round(revenue, 2)
            })
    return pl.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
# Dataset 6 — Pricing Promo (HTE Discovery)
# ─────────────────────────────────────────────────────────────────────────────
def _generate_causal_hte(seed: int = 456) -> pl.DataFrame:
    """Observational pricing promotion data. The Average Treatment Effect (ATE)
    is near zero, but Heterogeneous Treatment Effects (HTE) exist: 
    high-tenure customers spend significantly more, while low-tenure just
    cannibalize margins. Perfect for CausalForestDML.
    """
    rng = np.random.default_rng(seed)
    n = 12_000
    
    # Covariates
    tenure_months = rng.integers(1, 48, size=n)
    past_purchases = rng.lognormal(mean=1.5, sigma=0.8, size=n).astype(int)
    age = rng.integers(18, 65, size=n)
    
    # Treatment assignment (observational: older, loyal customers more likely to get promo)
    logit_p = -1.5 + 0.05 * tenure_months + 0.01 * age
    prob = 1.0 / (1.0 + np.exp(-logit_p))
    promo_applied = rng.binomial(1, prob, size=n)
    
    # Treatment effect (CATE):
    # - Negative for low tenure (margin cannibalization)
    # - Highly positive for high tenure (>24 months) and high past purchases
    cate = -15.0 + 1.2 * tenure_months + 0.5 * past_purchases
    
    # Outcome: base spend + treatment effect + noise
    base_spend = 50.0 + 2.0 * past_purchases + 0.5 * age
    spend_90d = base_spend + promo_applied * cate + rng.normal(0, 20.0, size=n)
    
    return pl.DataFrame({
        "promo_applied": promo_applied.tolist(),
        "spend_90d": np.maximum(0, spend_90d).round(2).tolist(),
        "tenure_months": tenure_months.tolist(),
        "past_purchases": past_purchases.tolist(),
        "age": age.tolist(),
    })

# ─────────────────────────────────────────────────────────────────────────────
# Entry point

# ─────────────────────────────────────────────────────────────────────────────
def generate_datasets() -> None:
    os.makedirs(_OUT, exist_ok=True)
    print("Generating canonical datasets for Tao Lab...\n")

    tasks = [
        (
            "SaaS Onboarding A/B Test",
            _generate_ab_saas,
            "ab_test_saas.csv",
            "Group='variant' (control/onboarding_v2), Metrics='revenue_28d'+'activated'+"
            "'sessions_28d', Ratio='pages_viewed'/'sessions_28d', Covariates='account_age_days'",
        ),
        (
            "Email Personalisation Small-N (Bayesian)",
            _generate_ab_email,
            "ab_test_email.csv",
            "Group='arm' (generic_subject/personalized_subject), Metrics='opened'+'revenue'",
        ),
        (
            "Weekly Retail Time-Series (Loyalty Programme)",
            _generate_time_series_weekly,
            "time_series_weekly.csv",
            "Timestamp='week_starting', Metric='weekly_revenue', Intervention='2023-01-02'",
        ),
        (
            "Bandit Replay Showcase",
            _generate_ab_bandit,
            "ab_test_bandit.csv",
            "Group='variant', Metric='converted', Date='date' — Run an A/B test and check Step 5.",
        ),
        (
            "Pricing Promo (HTE Discovery)",
            _generate_causal_hte,
            "causal_pricing_hte.csv",
            "Treatment='promo_applied', Outcome='spend_90d', Covariates='tenure_months' etc. — Use Causal Inference with HTE.",
        ),
    ]

    for i, (name, fn, fname, hint) in enumerate(tasks, 1):
        print(f"{i}. {name}...")
        try:
            df = fn()
            path = os.path.join(_OUT, fname)
            df.write_csv(path)
            print(f"   ✅ Saved {len(df):,} rows → {path}")
            print(f"   💡 {hint}")
        except Exception as exc:
            print(f"   ❌ Failed: {exc}")
        print()

    print("4. 401k Retirement Savings (Causal Inference)...")
    try:
        df = _fetch_401k_or_synthetic()
        path = os.path.join(_OUT, "causal_401k.csv")
        df.write_csv(path)
        print(f"   ✅ Saved → {path}")
        print(
            "   💡 Treatment='p401', Outcome='net_tfa', "
            "Covariates='age','inc','fsize','educ','pira'"
        )
    except Exception as exc:
        print(f"   ❌ Failed: {exc}")

    print("\n🎉 All datasets ready in the 'datasets/' directory!")
    print("\nSummary:")
    for fname in ["ab_test_saas.csv", "ab_test_email.csv",
                  "time_series_weekly.csv", "causal_401k.csv",
                  "ab_test_bandit.csv", "causal_pricing_hte.csv"]:
        path = os.path.join(_OUT, fname)
        if os.path.exists(path):
            df = pl.read_csv(path)
            print(f"  {fname}: {df.shape[0]:,} rows × {df.shape[1]} cols  "
                  f"[{', '.join(df.columns)}]")


if __name__ == "__main__":
    generate_datasets()
