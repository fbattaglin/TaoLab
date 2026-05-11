import polars as pl
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
from tao_lab.methods.base import Method, AnalysisResult, MetricResult, ExperimentConfig

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

        return AnalysisResult(
            method_name="Causal Inference (DML/EconML)",
            metrics=[metric_res],
            srm_p_value=1.0,
            srm_detected=False,
            diagnostics=overlap_data,
            config_snapshot=config
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
