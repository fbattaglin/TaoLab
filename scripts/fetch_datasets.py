import polars as pl
import os
import numpy as np
import datetime

def generate_datasets():
    os.makedirs("datasets", exist_ok=True)
    print("Fetching and generating canonical datasets for Tao Lab...\n")

    # 1. Observational Causal Inference: Lalonde Dataset
    print("1. Fetching Lalonde (Observational Causal Inference)...")
    try:
        url_lalonde = "https://vincentarelbundock.github.io/Rdatasets/csv/MatchIt/lalonde.csv"
        # Increase infer_schema_length to avoid float vs int detection errors
        df_lalonde = pl.read_csv(url_lalonde, infer_schema_length=10000)
        if "rownames" in df_lalonde.columns:
            df_lalonde = df_lalonde.drop("rownames")
        df_lalonde.write_csv("datasets/causal_lalonde.csv")
        print("   ✅ Saved to: datasets/causal_lalonde.csv")
        print("   💡 Config: Treatment='treat', Outcome='re78', Covariates='age', 'educ', 'race', etc.")
    except Exception as e:
        print(f"   ❌ Failed to fetch Lalonde: {e}")

    print("\n--------------------------------------------------\n")

    # 2. Time-Series Intervention: Marketing Campaign
    print("2. Generating Time-Series Intervention Data...")
    try:
        np.random.seed(42)
        start_date = datetime.date(2023, 1, 1)
        dates = [start_date + datetime.timedelta(days=i) for i in range(180)]
        n_days = len(dates)
        
        # Base trend + weekly seasonality
        trend = np.linspace(100, 150, n_days)
        seasonality = np.sin(np.arange(n_days) * (2 * np.pi / 7)) * 10 
        
        intervention_date = datetime.date(2023, 4, 15)
        intervention_idx = dates.index(intervention_date)
        
        revenue = trend + seasonality + np.random.normal(0, 5, n_days)
        revenue[intervention_idx:] += 25 # +25 absolute lift after intervention

        df_ts = pl.DataFrame({
            "date": dates,
            "daily_revenue": revenue,
            "marketing_spend": trend * 0.5 + np.random.normal(0, 2, n_days)
        })
        df_ts.write_csv("datasets/time_series_marketing.csv")
        print("   ✅ Saved to: datasets/time_series_marketing.csv")
        print("   💡 Config: Timestamp='date', Metric='daily_revenue', Intervention='2023-04-15'")
    except Exception as e:
         print(f"   ❌ Failed to generate Time-Series data: {e}")

    print("\n--------------------------------------------------\n")

    # 3. A/B Testing with Ratio Metrics
    print("3. Generating A/B Testing Data (E-commerce)...")
    try:
        np.random.seed(123)
        n_users = 10000
        groups = np.random.choice(["Control", "Treatment"], size=n_users, p=[0.5, 0.5])
        
        impressions = np.random.poisson(15, n_users)
        ctr = np.where(groups == "Control", 0.05, 0.06)
        clicks = np.random.binomial(impressions, ctr)
        
        rev_per_click = np.where(groups == "Control", 15.0, 15.5)
        revenue = clicks * rev_per_click + np.random.normal(0, 2, n_users)
        revenue = np.maximum(0, revenue)

        df_ab = pl.DataFrame({
            "user_id": np.arange(n_users),
            "variant": groups,
            "impressions": impressions,
            "clicks": clicks,
            "revenue": revenue,
            "user_tenure_days": np.random.poisson(100, n_users)
        })
        df_ab.write_csv("datasets/ab_test_ecommerce.csv")
        print("   ✅ Saved to: datasets/ab_test_ecommerce.csv")
        print("   💡 Config: Group='variant', Metrics='revenue'. Ratio Metric: 'clicks'/'impressions'")
    except Exception as e:
        print(f"   ❌ Failed to generate A/B Test data: {e}")

    print("\n🎉 All datasets are ready in the 'datasets/' directory!")

if __name__ == "__main__":
    generate_datasets()
