from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import polars as pl
from pydantic import BaseModel, Field
import plotly.graph_objects as go


# ── HTE (Heterogeneous Treatment Effects) models ──

class SubgroupEffect(BaseModel):
    """CATE summary for one segment (e.g., one quartile of a feature)."""
    feature: str
    segment_label: str   # "Q1 (25–35)"
    segment_size: int
    mean_cate: float
    ci_lower: float
    ci_upper: float


class HTEResult(BaseModel):
    """Heterogeneous Treatment Effect estimates from CausalForestDML."""
    feature_names: List[str]
    feature_importances: Dict[str, float]       # feature → importance (0–1)
    cate_values: List[float]                     # per-observation CATE
    cate_ci_lower: List[float]
    cate_ci_upper: List[float]
    subgroups: List[SubgroupEffect]              # quartile-based subgroup effects
    ate_from_forest: float                       # ATE from CausalForestDML (for comparison)
    ate_forest_ci: Tuple[float, float]


# ── MAB Regret Simulation models ──

class BanditReplayResult(BaseModel):
    """Results from Thompson Sampling replay simulation on A/B test data.

    Not a primary analysis — a post-hoc insight that quantifies the opportunity
    cost of fixed (50/50) allocation vs adaptive Thompson Sampling.
    """

    # Summary
    mode: str  # "daily" or "sequential"
    n_periods: int  # days (daily) or batches (sequential)
    n_observations: int
    metric_name: str
    metric_type: str  # "binary" or "continuous"
    winner: str  # the winning arm's value (e.g., "treatment")

    # Regret
    cumulative_reward_ab: float
    cumulative_reward_bandit: float
    cumulative_reward_optimal: float
    regret_ab: float  # optimal - ab
    regret_bandit: float  # optimal - bandit
    regret_saved: float  # regret_ab - regret_bandit
    regret_saved_pct: float  # regret_saved / regret_ab (0–1, 0 if regret_ab ≈ 0)

    # Convergence
    convergence_period: Optional[int] = None  # first period where allocation ≥ 0.75
    final_allocation: float  # final fraction to winner

    # Per-period series (for charts)
    period_labels: List[str]  # dates (daily) or "0–100" (sequential)
    cumulative_ab: List[float]
    cumulative_bandit: List[float]
    cumulative_optimal: List[float]
    allocation_to_winner: List[float]  # fraction allocated to winner per period


class RatioMetric(BaseModel):
    name: str
    numerator_col: str
    denominator_col: str

class ExperimentConfig(BaseModel):
    assignment_col: str
    control_val: Union[str, int, float]
    treatment_val: Union[str, int, float]
    metric_cols: List[str] = Field(default_factory=list, description="Standard continuous metrics")
    ratio_metrics: List[RatioMetric] = Field(default_factory=list, description="Metrics requiring the Delta Method")
    covariate_cols: List[str] = Field(default_factory=list, description="Pre-experiment covariates for variance reduction (CUPED)")
    expected_ratio: Dict[Union[str, int, float], float] = Field(default_factory=lambda: {"control": 0.5, "treatment": 0.5})
    alpha: float = 0.05
    method_params: Dict[str, Any] = Field(default_factory=dict, description="Method-specific hyperparams")
    
    # ── Phase E: Decision Intelligence ──
    business_unit_value: Optional[float] = Field(default=None, description="Monetary value of one unit of the primary metric")
    audience_size: Optional[int] = Field(default=None, description="Total audience size to simulate full rollout impact")

class MetricResult(BaseModel):
    metric_name: str
    metric_type: str = "continuous" # 'continuous' or 'ratio'
    control_mean: float
    treatment_mean: float
    lift_absolute: float
    lift_relative: float
    p_value: Optional[float] = None
    ci_lower: float
    ci_upper: float
    is_significant: bool
    warning_message: Optional[str] = None
    # ── Phase B additive fields. All optional, no engine is required to fill them. ──
    n_control: Optional[int] = None
    n_treatment: Optional[int] = None
    test_statistic: Optional[float] = None  # t-stat (Welch), z-proxy (ratios), P(better) (Bayesian)
    effect_size: Optional[float] = None     # Cohen's d for continuous
    p_value_adjusted: Optional[float] = None  # set by Benjamini-Hochberg correction
    
    # ── Phase E: Decision Intelligence ──
    expected_loss: Optional[float] = None    # Bayesian Expected Loss (Risk)
    expected_impact: Optional[float] = None  # Expected Lift (Reward) in absolute units

class AnalysisResult(BaseModel):
    method_name: str
    metrics: List[MetricResult]
    srm_p_value: float
    srm_detected: bool
    diagnostics: Dict[str, Any] = Field(default_factory=dict)
    config_snapshot: ExperimentConfig
    hte: Optional[HTEResult] = None  # populated when HTE is enabled

class Method(ABC):
    @abstractmethod
    def fit(self, data: pl.DataFrame, config: ExperimentConfig) -> AnalysisResult:
        """Execute the statistical analysis."""
        pass

    @abstractmethod
    def diagnostics(self, data: pl.DataFrame, config: ExperimentConfig) -> Dict[str, Any]:
        """Return method-specific diagnostic metrics."""
        pass

    @abstractmethod
    def visualize(self, result: AnalysisResult) -> List[go.Figure]:
        """Return a list of plotly figures for the UI."""
        pass
