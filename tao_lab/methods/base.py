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
