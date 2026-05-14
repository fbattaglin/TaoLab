import polars as pl
import numpy as np
from scipy.stats import ttest_ind, norm
from typing import Any, Dict, List
import plotly.graph_objects as go
from tao_lab.methods.base import Method, AnalysisResult, MetricResult, ExperimentConfig
from tao_lab.checks.srm import check_srm

class FrequentistABTest(Method):
    """
    Standard Frequentist A/B testing with Welch's T-Test and Delta Method for ratios.
    """
    def fit(self, data: pl.DataFrame, config: ExperimentConfig) -> AnalysisResult:
        # 1. SRM Check (Stat Non-negotiable)
        srm_p, srm_detected = check_srm(data, config.assignment_col, config.expected_ratio)

        results = []

        # 2. Continuous Metrics
        for col in config.metric_cols:
            res = self._analyze_continuous(data, col, config)
            results.append(res)

        # 3. Ratio Metrics (Delta Method)
        for rm in config.ratio_metrics:
            res = self._analyze_ratio(data, rm, config)
            results.append(res)

        # 4. Apply Multiple Testing Correction (Benjamini-Hochberg)
        if len(results) > 1:
            from tao_lab.checks.multiple_testing import apply_fdr_correction
            results = apply_fdr_correction(results, alpha=config.alpha)

        return AnalysisResult(
            method_name="Frequentist A/B Test",
            metrics=results,
            srm_p_value=srm_p,
            srm_detected=srm_detected,
            config_snapshot=config
        )

    def _analyze_continuous(self, data: pl.DataFrame, col: str, config: ExperimentConfig) -> MetricResult:
        ctrl = data.filter(pl.col(config.assignment_col) == config.control_val).select(col).to_series().to_numpy()
        treat = data.filter(pl.col(config.assignment_col) == config.treatment_val).select(col).to_series().to_numpy()

        # Welch's T-test
        t_stat, p_val = ttest_ind(treat, ctrl, equal_var=False)

        mu_c, mu_t = np.mean(ctrl), np.mean(treat)
        var_c, var_t = np.var(ctrl, ddof=1), np.var(treat, ddof=1)
        n_c, n_t = len(ctrl), len(treat)
        lift_abs = mu_t - mu_c
        lift_rel = (mu_t / mu_c) - 1 if mu_c != 0 else 0

        # CI calculation
        se = np.sqrt((var_c / n_c) + (var_t / n_t))
        z = norm.ppf(1 - config.alpha / 2)

        # Cohen's d (pooled SD): standardised effect size, useful even when p-values are.
        pooled_sd = np.sqrt(((n_c - 1) * var_c + (n_t - 1) * var_t) / max(n_c + n_t - 2, 1))
        cohen_d = float(lift_abs / pooled_sd) if pooled_sd > 0 else 0.0

        # Phase E: Decision Intelligence (Expected Loss / Impact)
        expected_loss_money = None
        expected_impact_money = None
        if config.business_unit_value is not None:
            multiplier = config.business_unit_value * (config.audience_size or 1)
            # Expected value of max(0, -X) where X ~ N(lift_abs, se)
            if se > 0:
                ratio = -lift_abs / se
                exp_loss_abs = -lift_abs * norm.cdf(ratio) + se * norm.pdf(ratio)
            else:
                exp_loss_abs = max(0, -lift_abs)
            
            expected_loss_money = float(exp_loss_abs * multiplier)
            expected_impact_money = float(lift_abs * multiplier)

        return MetricResult(
            metric_name=col,
            control_mean=mu_c,
            treatment_mean=mu_t,
            lift_absolute=lift_abs,
            lift_relative=lift_rel,
            p_value=p_val,
            ci_lower=lift_abs - z * se,
            ci_upper=lift_abs + z * se,
            is_significant=p_val < config.alpha,
            n_control=int(n_c),
            n_treatment=int(n_t),
            test_statistic=float(t_stat),
            effect_size=cohen_d,
            expected_loss=expected_loss_money,
            expected_impact=expected_impact_money,
        )

    def _analyze_ratio(self, data: pl.DataFrame, rm: Any, config: ExperimentConfig) -> MetricResult:
        """
        Implements the Delta Method for Ratio Metrics.
        Reference: Deng et al. (2013) "Statistical Methods for Online A/B Testing".
        """
        # Separate data
        df_c = data.filter(pl.col(config.assignment_col) == config.control_val)
        df_t = data.filter(pl.col(config.assignment_col) == config.treatment_val)
        
        def calc_ratio_stats(df, num_col, den_col):
            x = df.select(num_col).to_series().to_numpy()
            y = df.select(den_col).to_series().to_numpy()
            n = len(x)
            
            mu_x, mu_y = np.mean(x), np.mean(y)
            var_x, var_y = np.var(x, ddof=1), np.var(y, ddof=1)
            cov_xy = np.cov(x, y)[0, 1]
            
            r = mu_x / mu_y
            # Delta Method Variance: Var(X/Y) approx (1/mu_y^2) * [Var(X) + r^2 Var(Y) - 2r Cov(X,Y)]
            var_r = (1 / (mu_y**2)) * (var_x + (r**2) * var_y - 2 * r * cov_xy) / n
            return r, var_r

        r_c, var_r_c = calc_ratio_stats(df_c, rm.numerator_col, rm.denominator_col)
        r_t, var_r_t = calc_ratio_stats(df_t, rm.numerator_col, rm.denominator_col)

        lift_abs = r_t - r_c
        lift_rel = (r_t / r_c) - 1 if r_c != 0 else 0

        se = np.sqrt(var_r_c + var_r_t)
        z = norm.ppf(1 - config.alpha / 2)
        z_stat = lift_abs / se if se != 0 else 0.0
        p_val = 2 * (1 - norm.cdf(abs(z_stat))) if se != 0 else 1.0

        # Phase E: Decision Intelligence (Expected Loss / Impact)
        expected_loss_money = None
        expected_impact_money = None
        if config.business_unit_value is not None:
            multiplier = config.business_unit_value * (config.audience_size or 1)
            if se > 0:
                ratio = -lift_abs / se
                exp_loss_abs = -lift_abs * norm.cdf(ratio) + se * norm.pdf(ratio)
            else:
                exp_loss_abs = max(0, -lift_abs)
            
            expected_loss_money = float(exp_loss_abs * multiplier)
            expected_impact_money = float(lift_abs * multiplier)

        return MetricResult(
            metric_name=rm.name,
            metric_type="ratio",
            control_mean=r_c,
            treatment_mean=r_t,
            lift_absolute=lift_abs,
            lift_relative=lift_rel,
            p_value=p_val,
            ci_lower=lift_abs - z * se,
            ci_upper=lift_abs + z * se,
            is_significant=p_val < config.alpha,
            n_control=int(df_c.height),
            n_treatment=int(df_t.height),
            test_statistic=float(z_stat),
            expected_loss=expected_loss_money,
            expected_impact=expected_impact_money,
        )

    def diagnostics(self, data: pl.DataFrame, config: ExperimentConfig) -> Dict[str, Any]:
        # Implementation for balance checks, outliers, etc.
        return {}

    def visualize(self, result: AnalysisResult) -> List[go.Figure]:
        # Forest Plot logic (to be expanded with interactive details)
        fig = go.Figure()
        for i, m in enumerate(result.metrics):
            fig.add_trace(go.Scatter(
                x=[m.lift_relative],
                y=[m.metric_name],
                error_x=dict(
                    type='data',
                    symmetric=False,
                    array=[m.ci_upper / m.control_mean - m.lift_relative if m.control_mean != 0 else 0],
                    arrayminus=[m.lift_relative - m.ci_lower / m.control_mean if m.control_mean != 0 else 0]
                ),
                mode='markers',
                marker=dict(color='#00C853' if m.is_significant else '#757575', size=12),
                name=m.metric_name
            ))
        
        fig.update_layout(
            title="Relative Lift & 95% Confidence Intervals",
            xaxis_title="Relative Lift",
            yaxis_title="Metric",
            showlegend=False
        )
        fig.add_vline(x=0, line_dash="dash", line_color="black")
        return [fig]
