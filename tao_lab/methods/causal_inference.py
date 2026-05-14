import polars as pl
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
from tao_lab.methods.base import Method, AnalysisResult, MetricResult, ExperimentConfig, HTEResult, SubgroupEffect

class CausalInference(Method):
    """
    Observational Causal Inference using DoWhy (Identification) and EconML (Estimation).
    Uses Double Machine Learning (DML) for ATE estimation.
    """
    def fit(self, data: pl.DataFrame, config: ExperimentConfig) -> AnalysisResult:
        # Lazy imports
        from dowhy import CausalModel
        from econml.dml import LinearDML
        from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
        
        df_pd = data.to_pandas()
        treatment = config.assignment_col
        outcome = config.metric_cols[0] if config.metric_cols else None
        common_causes = config.covariate_cols
        
        if not outcome:
            raise ValueError("No outcome metric specified for Causal Inference.")

        # 1. DoWhy Identification
        model = CausalModel(
            data=df_pd,
            treatment=treatment,
            outcome=outcome,
            common_causes=common_causes
        )
        identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)
        
        # 2. EconML Estimation (DML)
        is_binary = df_pd[treatment].nunique() == 2
        
        est = LinearDML(
            model_y=RandomForestRegressor(n_estimators=100, max_depth=5),
            model_t=RandomForestClassifier(n_estimators=100, max_depth=5) if is_binary else RandomForestRegressor(),
            discrete_treatment=is_binary,
            cv=3
        )
        
        Y = df_pd[outcome]
        T = df_pd[treatment]
        X = df_pd[common_causes] if common_causes else None
        
        # Fit DML
        est.fit(Y, T, X=X, W=None)
        
        # Estimate Average Treatment Effect (ATE)
        ate = est.ate(X)
        ate_interval = est.ate_interval(X)
        
        # 3. Diagnostics - Propensity Overlap (Positivity Assumption)
        overlap_data = {}
        if is_binary and common_causes:
            prop_model = RandomForestClassifier(n_estimators=100, max_depth=5).fit(df_pd[common_causes], df_pd[treatment])
            prop_scores = prop_model.predict_proba(df_pd[common_causes])[:, 1]
            overlap_data = {
                "propensity_scores": prop_scores.tolist(),
                "treatment_values": df_pd[treatment].tolist()
            }

        metric_res = MetricResult(
            metric_name=outcome,
            control_mean=0.0,
            treatment_mean=0.0,
            lift_absolute=float(ate),
            lift_relative=0.0,
            p_value=None,
            ci_lower=float(ate_interval[0]),
            ci_upper=float(ate_interval[1]),
            is_significant=not (ate_interval[0] < 0 < ate_interval[1])
        )

        # Phase E: Decision Intelligence (Expected Loss / Impact)
        expected_loss_money = None
        expected_impact_money = None
        if config.business_unit_value is not None:
            multiplier = config.business_unit_value * (config.audience_size or 1)
            import scipy.stats as stats
            z_val = stats.norm.ppf(1 - config.alpha / 2)
            se = (ate_interval[1] - ate_interval[0]) / (2 * z_val) if z_val > 0 else 0
            
            if se > 0:
                ratio = -float(ate) / se
                exp_loss_abs = -float(ate) * stats.norm.cdf(ratio) + se * stats.norm.pdf(ratio)
            else:
                exp_loss_abs = max(0, -float(ate))
            
            expected_loss_money = float(exp_loss_abs * multiplier)
            expected_impact_money = float(float(ate) * multiplier)
            
            metric_res.expected_loss = expected_loss_money
            metric_res.expected_impact = expected_impact_money

        # ── HTE (optional — CausalForestDML) ──
        hte_result = None
        if config.method_params.get("hte_enabled") and common_causes:
            hte_result = self._fit_hte(
                df_pd, Y, T, common_causes, is_binary, config
            )

        return AnalysisResult(
            method_name="Causal Inference (DML/EconML)",
            metrics=[metric_res],
            srm_p_value=1.0,
            srm_detected=False,
            diagnostics=overlap_data,
            config_snapshot=config,
            hte=hte_result,
        )

    def _fit_hte(
        self,
        df_pd: pd.DataFrame,
        Y: pd.Series,
        T: pd.Series,
        common_causes: List[str],
        is_binary: bool,
        config: ExperimentConfig,
    ) -> Optional[HTEResult]:
        """Fit CausalForestDML for heterogeneous treatment effects."""
        from econml.dml import CausalForestDML
        from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

        hte_features = config.method_params.get("hte_features", common_causes)
        X_hte = df_pd[hte_features]

        forest = CausalForestDML(
            model_y=RandomForestRegressor(n_estimators=100, max_depth=5),
            model_t=(
                RandomForestClassifier(n_estimators=100, max_depth=5)
                if is_binary
                else RandomForestRegressor(n_estimators=100, max_depth=5)
            ),
            discrete_treatment=is_binary,
            n_estimators=200,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1,
        )
        forest.fit(Y, T, X=X_hte, W=df_pd[common_causes])

        cate = forest.effect(X_hte)
        cate_interval = forest.effect_interval(X_hte, alpha=0.05)
        fi = forest.feature_importances_
        ate_forest = float(forest.ate(X_hte))
        ate_forest_interval = forest.ate_interval(X_hte)

        subgroups = _build_subgroup_table(X_hte, cate, cate_interval, hte_features)

        return HTEResult(
            feature_names=list(hte_features),
            feature_importances=dict(zip(hte_features, fi.tolist())),
            cate_values=cate.flatten().tolist(),
            cate_ci_lower=cate_interval[0].flatten().tolist(),
            cate_ci_upper=cate_interval[1].flatten().tolist(),
            subgroups=subgroups,
            ate_from_forest=ate_forest,
            ate_forest_ci=(
                float(ate_forest_interval[0]),
                float(ate_forest_interval[1]),
            ),
        )

    def diagnostics(self, data: pl.DataFrame, config: ExperimentConfig) -> Dict[str, Any]:
        return {}

    def visualize(self, result: AnalysisResult) -> List[go.Figure]:
        import plotly.express as px
        figures = []

        # Propensity Overlap Plot
        if "propensity_scores" in result.diagnostics:
            df_overlap = pd.DataFrame({
                "Propensity Score": result.diagnostics["propensity_scores"],
                "Group": result.diagnostics["treatment_values"]
            })
            fig = px.histogram(df_overlap, x="Propensity Score", color="Group",
                               marginal="box", barmode="overlay",
                               title="Propensity Score Overlap (Positivity Check)")
            figures.append(fig)

        return figures


# ── Module-level helpers ──

def _build_subgroup_table(
    X_df: pd.DataFrame,
    cate: np.ndarray,
    cate_interval: tuple,
    feature_names: List[str],
) -> List[SubgroupEffect]:
    """Build quartile-based CATE summary per feature."""
    cate_flat = cate.flatten()
    ci_lower = cate_interval[0].flatten()
    ci_upper = cate_interval[1].flatten()
    subgroups: List[SubgroupEffect] = []

    for feat in feature_names:
        col = X_df[feat]
        # Skip non-numeric or very low cardinality (binary)
        if col.nunique() <= 2:
            # For binary features, split into 0/1
            for val in sorted(col.unique()):
                mask = col == val
                if mask.sum() < 5:
                    continue
                subgroups.append(SubgroupEffect(
                    feature=feat,
                    segment_label=f"{val}",
                    segment_size=int(mask.sum()),
                    mean_cate=float(cate_flat[mask].mean()),
                    ci_lower=float(ci_lower[mask].mean()),
                    ci_upper=float(ci_upper[mask].mean()),
                ))
            continue

        try:
            quartiles = pd.qcut(
                col, 4, labels=["Q1", "Q2", "Q3", "Q4"], duplicates="drop"
            )
        except ValueError:
            continue

        for q in sorted(quartiles.dropna().unique()):
            mask = quartiles == q
            if mask.sum() < 5:
                continue
            feat_vals = col[mask]
            subgroups.append(SubgroupEffect(
                feature=feat,
                segment_label=f"{q} ({feat_vals.min():.3g}–{feat_vals.max():.3g})",
                segment_size=int(mask.sum()),
                mean_cate=float(cate_flat[mask].mean()),
                ci_lower=float(ci_lower[mask].mean()),
                ci_upper=float(ci_upper[mask].mean()),
            ))

    return subgroups
