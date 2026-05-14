import polars as pl
import numpy as np
from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
from tao_lab.methods.base import Method, AnalysisResult, MetricResult, ExperimentConfig
from tao_lab.checks.srm import check_srm

class BayesianABTest(Method):
    """
    Bayesian A/B testing using NumPyro for fast JAX-backed MCMC.
    Computes Posterior, ROPE, and Probability of Being Better.
    """
    def fit(self, data: pl.DataFrame, config: ExperimentConfig) -> AnalysisResult:
        # Lazy imports for heavy Bayesian dependencies
        import jax.numpy as jnp
        import jax.random as random
        import numpyro
        import numpyro.distributions as dist
        from numpyro.infer import MCMC, NUTS

        # 1. SRM Check
        srm_p, srm_detected = check_srm(data, config.assignment_col, config.expected_ratio)

        results = []
        diagnostics = {}

        for metric in config.metric_cols:
            ctrl = data.filter(pl.col(config.assignment_col) == config.control_val).select(metric).to_series().to_numpy()
            treat = data.filter(pl.col(config.assignment_col) == config.treatment_val).select(metric).to_series().to_numpy()

            # Define NumPyro Model (Hierarchical or Simple Gaussian for MVP)
            def model(control_obs, treatment_obs):
                # Priors
                mu_c = numpyro.sample("mu_c", dist.Normal(np.mean(control_obs), np.std(control_obs) * 2))
                mu_t = numpyro.sample("mu_t", dist.Normal(np.mean(treatment_obs), np.std(treatment_obs) * 2))
                sigma = numpyro.sample("sigma", dist.HalfNormal(np.std(control_obs) * 2))
                
                # Likelihood
                numpyro.sample("obs_c", dist.Normal(mu_c, sigma), obs=control_obs)
                numpyro.sample("obs_t", dist.Normal(mu_t, sigma), obs=treatment_obs)
                
                # Derived quantities
                numpyro.deterministic("lift_abs", mu_t - mu_c)
                numpyro.deterministic("lift_rel", (mu_t / mu_c) - 1)

            # Run MCMC
            nuts_kernel = NUTS(model)
            mcmc = MCMC(nuts_kernel, num_warmup=500, num_samples=1000, num_chains=1, progress_bar=False)
            mcmc.run(random.PRNGKey(0), ctrl, treat)
            
            samples = mcmc.get_samples()
            
            # Post-processing
            lift_rel_samples = samples["lift_rel"]
            prob_better = float(np.mean(lift_rel_samples > 0))
            
            mu_c_mean = float(np.mean(samples["mu_c"]))
            mu_t_mean = float(np.mean(samples["mu_t"]))
            lift_abs_mean = float(np.mean(samples["lift_abs"]))
            lift_rel_mean = float(np.mean(samples["lift_rel"]))
            
            hdi_lower, hdi_upper = np.percentile(samples["lift_abs"], [2.5, 97.5])
            
            # ROPE Logic (Region of Practical Equivalence)
            # Default ROPE: +/- 0.1% relative lift or user-defined
            rope_threshold = config.method_params.get("rope_threshold", 0.001)
            prob_in_rope = float(np.mean(np.abs(lift_rel_samples) < rope_threshold))

            # Phase E: Decision Intelligence (Expected Loss / Impact)
            loss_samples = np.maximum(0, samples["mu_c"] - samples["mu_t"])
            expected_loss_abs = float(np.mean(loss_samples))
            
            expected_loss_money = None
            expected_impact_money = None
            if config.business_unit_value is not None:
                multiplier = config.business_unit_value * (config.audience_size or 1)
                expected_loss_money = expected_loss_abs * multiplier
                expected_impact_money = lift_abs_mean * multiplier

            results.append(MetricResult(
                metric_name=metric,
                control_mean=mu_c_mean,
                treatment_mean=mu_t_mean,
                lift_absolute=lift_abs_mean,
                lift_relative=lift_rel_mean,
                p_value=1 - prob_better, # Proxy for 'significance' in UI
                ci_lower=float(hdi_lower),
                ci_upper=float(hdi_upper),
                is_significant=prob_better > 0.95 or prob_better < 0.05,
                warning_message=f"P(Better): {prob_better:.2%}, P(In ROPE): {prob_in_rope:.2%}",
                n_control=int(len(ctrl)),
                n_treatment=int(len(treat)),
                test_statistic=float(prob_better),
                expected_loss=expected_loss_money,
                expected_impact=expected_impact_money,
            ))
            
            diagnostics[f"{metric}_samples"] = {
                "lift_rel": lift_rel_samples.tolist(),
                "mu_c": samples["mu_c"].tolist(),
                "mu_t": samples["mu_t"].tolist()
            }

        return AnalysisResult(
            method_name="Bayesian A/B Test (NumPyro)",
            metrics=results,
            srm_p_value=srm_p,
            srm_detected=srm_detected,
            diagnostics=diagnostics,
            config_snapshot=config
        )

    def diagnostics(self, data: pl.DataFrame, config: ExperimentConfig) -> Dict[str, Any]:
        return {}

    def visualize(self, result: AnalysisResult) -> List[go.Figure]:
        import plotly.figure_factory as ff
        figures = []
        
        for metric in result.metrics:
            samples = result.diagnostics.get(f"{metric.metric_name}_samples", {}).get("lift_rel", [])
            if not samples: continue
            
            # Posterior Density Plot
            fig = ff.create_distplot([samples], [f"Posterior Lift ({metric.metric_name})"], 
                                    show_hist=False, show_rug=False)
            
            fig.add_vline(x=0, line_dash="dash", line_color="black", annotation_text="Zero Lift")
            
            # Shade HDI
            hdi_l, hdi_r = np.percentile(samples, [2.5, 97.5])
            fig.add_vrect(x0=hdi_l, x1=hdi_r, fillcolor="green", opacity=0.1, line_width=0, 
                         annotation_text="95% HDI")
            
            fig.update_layout(
                title=f"Posterior Distribution of Relative Lift: {metric.metric_name}",
                xaxis_title="Relative Lift",
                yaxis_title="Density",
                showlegend=False
            )
            figures.append(fig)
            
        return figures
