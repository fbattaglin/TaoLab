"""Diagnosis engine — heuristic data inspection and method recommendation.

Phase D rewrites the recommendation logic from a short-circuiting priority
chain to independent scoring of ALL eligible methods.  Every method gets a
fitness score (0–1); the user sees ranked selectable cards in Step 2.

The old ``DiagnosisReport`` shape (``suggested_method``, ``rationale``,
``config_hint``, ``warnings``) is preserved for backward compatibility —
those fields are populated from ``candidates[0]``.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import polars as pl
from pydantic import BaseModel, Field


# ───────────────────────────── Models ─────────────────────────────

class MethodCandidate(BaseModel):
    """One eligible analysis method with a fitness score and config hints."""

    method: str  # "A/B Test", "Time-Series Intervention", "Causal Inference", "Exploratory"
    score: float  # 0.0–1.0
    rationale: str
    config_hint: Dict[str, Any] = Field(default_factory=dict)
    requirements: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class DiagnosisReport(BaseModel):
    # ── Preserved (backward compat) ──
    suggested_method: str
    rationale: str
    config_hint: Dict[str, Any]
    warnings: List[str]
    # ── Phase D additions ──
    candidates: List[MethodCandidate] = Field(default_factory=list)
    detected_signals: Dict[str, Any] = Field(default_factory=dict)


class HealthDimension(BaseModel):
    """One axis of the Data Health Score (0..100, higher is better)."""

    key: str
    label: str
    score: int
    status: str  # 'pass' | 'warn' | 'fail'
    detail: str


class DataHealthReport(BaseModel):
    """Composite data-quality readout shown above the fold on the Diagnose step."""

    overall_score: int  # 0..100
    overall_status: str  # 'pass' | 'warn' | 'fail'
    dimensions: List[HealthDimension] = Field(default_factory=list)


# ───────────────────────── Column name hints ─────────────────────

_AB_GROUP_HINTS = {"variant", "group", "arm", "bucket", "ab_group", "condition", "segment"}
_CAUSAL_TREAT_HINTS = {"treat", "treatment", "intervention", "policy", "exposed", "treated"}
_ID_NAME_PATTERNS = re.compile(r"(?i)^(id|index|row_?num|row_?id)$|_id$")
_OUTCOME_NAME_HINTS = {"outcome", "revenue", "response", "y", "target", "earnings",
                       "re78", "conversion", "conversions", "sales", "profit"}

_DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
]


# ───────────────────────── Signal detection ──────────────────────

def _try_parse_date_col(series: pl.Series) -> Optional[str]:
    """Try common date formats on a Utf8 series.

    Returns the first format where ≥90 % of non-null values parse, or None.
    Only samples up to 50 rows so it's fast even on large datasets.
    """
    sample = series.drop_nulls().head(50)
    if sample.len() < 3:
        return None
    for fmt in _DATE_FORMATS:
        try:
            parsed = sample.str.to_date(fmt, strict=False)
            n_ok = parsed.len() - parsed.is_null().sum()
            if n_ok / sample.len() >= 0.9:
                return fmt
        except Exception:  # noqa: BLE001
            continue
    return None


def _is_id_column(col: str, series: pl.Series, n_rows: int) -> bool:
    """Heuristic: a column that is an identifier, not a metric.

    The cardinality check (n_unique / n_rows > 0.9) is only applied to
    *integer* types.  Float columns with high cardinality are normal
    continuous data (e.g. daily_revenue with 180 unique floats in 180 rows).
    """
    if _ID_NAME_PATTERNS.search(col):
        return True
    if series.dtype.is_integer() and n_rows > 0:
        nunique = series.n_unique()
        if nunique / n_rows > 0.9:
            return True
    return False


def _detect_column_roles(df: pl.DataFrame) -> Dict[str, Any]:
    """Classify every column into a role.  Returns a signal dict consumed by
    the per-method scorers."""

    n_rows = df.height
    group_cols: List[Dict[str, Any]] = []
    timestamp_cols: List[Dict[str, Any]] = []
    numeric_cols: List[str] = []
    id_cols: List[str] = []

    for col in df.columns:
        dtype = df.schema[col]
        series = df[col]

        # ── ID column check (before anything else) ──
        if _is_id_column(col, series, n_rows):
            id_cols.append(col)
            continue

        # ── Native date / datetime ──
        if dtype in (pl.Date, pl.Datetime):
            timestamp_cols.append({"col": col, "dtype": str(dtype), "date_format": None})
            continue

        # ── Utf8: try date parse, then check cardinality for groups ──
        if dtype == pl.Utf8:
            date_fmt = _try_parse_date_col(series)
            if date_fmt is not None:
                timestamp_cols.append({"col": col, "dtype": "String", "date_format": date_fmt})
                continue
            nunique = series.n_unique()
            if 2 <= nunique <= 10:
                vals = series.drop_nulls().unique().sort().to_list()
                group_cols.append({
                    "col": col,
                    "n_unique": nunique,
                    "dtype": "String",
                    "is_binary": nunique == 2,
                    "values": vals,
                })
            continue

        # ── Numeric ──
        if dtype.is_numeric():
            nunique = series.n_unique()
            if 2 <= nunique <= 10:
                vals = series.drop_nulls().unique().sort().to_list()
                group_cols.append({
                    "col": col,
                    "n_unique": nunique,
                    "dtype": str(dtype),
                    "is_binary": nunique == 2,
                    "values": vals,
                })
            # Always add to numeric_cols (even if also a group candidate)
            numeric_cols.append(col)

    # ── Ratio metric hints (existing logic, unchanged) ──
    ratio_hints: List[Dict[str, str]] = []
    potential_dens = {"views", "sessions", "impressions", "users", "visitors"}
    potential_nums = {"clicks", "conversions", "purchases", "orders"}
    for den in potential_dens:
        if den in numeric_cols:
            for num in potential_nums:
                if num in numeric_cols:
                    ratio_hints.append({"name": f"{num}/{den}", "num": num, "den": den})

    # ── Group balance (for the best group candidate) ──
    balance_ratio: Optional[float] = None
    if group_cols:
        best_group = group_cols[0]["col"]
        try:
            counts = df.group_by(best_group).len().sort("len", descending=True)
            sizes = counts.select("len").to_series().to_list()
            if len(sizes) >= 2 and sum(sizes) > 0:
                balance_ratio = sizes[0] / sum(sizes)
        except Exception:  # noqa: BLE001
            pass

    return {
        "group_cols": group_cols,
        "timestamp_cols": timestamp_cols,
        "numeric_cols": numeric_cols,
        "id_cols": id_cols,
        "ratio_hints": ratio_hints,
        "n_rows": n_rows,
        "balance_ratio": balance_ratio,
    }


# ───────────────────────── Per-method scorers ────────────────────

def _score_ab(signals: Dict[str, Any]) -> MethodCandidate:
    """Score the dataset's fitness for a Frequentist / Bayesian A/B test."""
    group_cols = signals["group_cols"]
    numeric_cols = signals["numeric_cols"]
    timestamp_cols = signals["timestamp_cols"]
    n_rows = signals["n_rows"]
    balance_ratio = signals["balance_ratio"]
    ratio_hints = signals["ratio_hints"]

    score = 0.0
    warnings: List[str] = []
    config_hint: Dict[str, Any] = {}

    # ── Required: a group column ──
    if not group_cols:
        return MethodCandidate(
            method="A/B Test", score=0.0,
            rationale="No group / assignment column detected.",
        )
    score += 0.4

    grp = group_cols[0]
    config_hint["assignment_col"] = grp["col"]
    vals = grp["values"]
    config_hint["control_val"] = vals[0] if len(vals) > 0 else "control"
    config_hint["treatment_val"] = vals[1] if len(vals) > 1 else "treatment"

    # ── Binary bonus ──
    if grp["is_binary"]:
        score += 0.1

    # ── Name hint bonus ──
    if grp["col"].lower() in _AB_GROUP_HINTS:
        score += 0.1

    # ── Needs at least one numeric metric ──
    metric_candidates = [c for c in numeric_cols if c != grp["col"]]
    if metric_candidates:
        score += 0.2
        config_hint["metric_cols"] = metric_candidates[:3]
    else:
        return MethodCandidate(
            method="A/B Test", score=0.0,
            rationale="No numeric metric columns found.",
        )

    config_hint["ratio_metrics"] = ratio_hints[:1]

    # ── Many covariates penalise A/B (signals observational) ──
    n_extra_numeric = len(metric_candidates)
    if n_extra_numeric >= 6:
        score -= 0.15
    elif n_extra_numeric >= 4:
        score -= 0.1

    # ── Timestamp presence is a mild negative (might be time-series) ──
    if timestamp_cols:
        score -= 0.05

    # ── Group balance ──
    if balance_ratio is not None:
        if balance_ratio <= 0.55:
            score += 0.1
        elif balance_ratio > 0.60:
            score -= 0.05
            warnings.append(
                f"Groups are imbalanced ({balance_ratio:.0%} in the largest). "
                "If assignment was randomised, investigate before trusting results."
            )

    # ── Sample size ──
    if n_rows >= 100:
        score += 0.1

    # ── Name hint for causal ──
    if grp["col"].lower() in _CAUSAL_TREAT_HINTS:
        score -= 0.05  # mild penalty — name suggests observational

    score = max(0.0, min(1.0, score))

    rationale = (
        f"Detected group column '{grp['col']}' with {grp['n_unique']} variants "
        f"and {len(metric_candidates)} numeric metric(s). "
        "Use this if assignment was randomised (e.g. an A/B test platform split users)."
    )

    return MethodCandidate(
        method="A/B Test",
        score=round(score, 3),
        rationale=rationale,
        config_hint=config_hint,
        warnings=warnings,
    )


def _score_timeseries(signals: Dict[str, Any]) -> MethodCandidate:
    """Score the dataset's fitness for interrupted time-series analysis."""
    timestamp_cols = signals["timestamp_cols"]
    numeric_cols = signals["numeric_cols"]
    group_cols = signals["group_cols"]
    n_rows = signals["n_rows"]

    score = 0.0
    config_hint: Dict[str, Any] = {}
    requirements: List[str] = []
    warnings: List[str] = []

    # ── Required: a timestamp column ──
    if not timestamp_cols:
        return MethodCandidate(
            method="Time-Series Intervention", score=0.0,
            rationale="No timestamp column detected.",
        )
    score += 0.4

    ts = timestamp_cols[0]
    config_hint["timestamp_col"] = ts["col"]
    if ts.get("date_format"):
        config_hint["date_format"] = ts["date_format"]

    # ── At least one numeric metric ──
    if numeric_cols:
        score += 0.2
        config_hint["metrics"] = numeric_cols[:2]
    else:
        return MethodCandidate(
            method="Time-Series Intervention", score=0.0,
            rationale="No numeric metric columns found.",
        )

    # ── No group column → classic single-series ITS ──
    if not group_cols:
        score += 0.2
    else:
        score += 0.05  # still possible but less canonical

    # ── Sample size (need enough time points for pre/post) ──
    if n_rows >= 30:
        score += 0.1
    else:
        warnings.append(
            f"Only {n_rows} time points. For a reliable pre/post split, "
            "30+ observations is recommended."
        )

    # ── Intervention date is always required from user ──
    requirements.append("Intervention date (the date the change went live)")

    score = max(0.0, min(1.0, score))

    rationale = (
        f"Detected timestamp column '{ts['col']}' with {n_rows} observations "
        f"and {len(numeric_cols)} numeric metric(s). "
        "Fits an interrupted time-series design — you'll need to specify the intervention date."
    )

    return MethodCandidate(
        method="Time-Series Intervention",
        score=round(score, 3),
        rationale=rationale,
        config_hint=config_hint,
        requirements=requirements,
        warnings=warnings,
    )


def _score_causal(signals: Dict[str, Any]) -> MethodCandidate:
    """Score the dataset's fitness for observational causal inference (DML)."""
    group_cols = signals["group_cols"]
    numeric_cols = signals["numeric_cols"]
    n_rows = signals["n_rows"]
    balance_ratio = signals["balance_ratio"]

    score = 0.0
    config_hint: Dict[str, Any] = {}
    requirements: List[str] = []
    warnings: List[str] = [
        "Observational analysis requires strict assumptions "
        "(no unmeasured confounding). Results are only as trustworthy as "
        "the set of confounders you specify."
    ]

    # ── Required: a group column (must be binary for treatment) ──
    binary_groups = [g for g in group_cols if g["is_binary"]]
    if not binary_groups:
        return MethodCandidate(
            method="Causal Inference", score=0.0,
            rationale="No binary treatment column detected.",
        )
    score += 0.3

    grp = binary_groups[0]
    config_hint["assignment_col"] = grp["col"]

    # ── Binary bonus ──
    score += 0.1

    # ── Name hint bonus ──
    if grp["col"].lower() in _CAUSAL_TREAT_HINTS:
        score += 0.1

    # ── At least one numeric metric ──
    metric_candidates = [c for c in numeric_cols if c != grp["col"]]
    if not metric_candidates:
        return MethodCandidate(
            method="Causal Inference", score=0.0,
            rationale="No numeric outcome columns found.",
        )
    score += 0.1

    # ── Identify outcome vs covariates ──
    # Prefer columns whose name hints at "outcome"
    outcome_col = metric_candidates[0]
    for c in metric_candidates:
        if c.lower() in _OUTCOME_NAME_HINTS:
            outcome_col = c
            break

    covariates = [c for c in metric_candidates if c != outcome_col]
    config_hint["metrics"] = [outcome_col]
    config_hint["covariates"] = covariates[:7]

    # ── Many covariates → strong causal signal ──
    n_covariates = len(covariates)
    if n_covariates >= 6:
        score += 0.15
    if n_covariates >= 4:
        score += 0.3
    elif n_covariates >= 2:
        score += 0.1

    # ── Imbalanced groups mildly favour causal ──
    if balance_ratio is not None and balance_ratio > 0.60:
        score += 0.05

    # ── Sample size ──
    if n_rows >= 100:
        score += 0.1

    # ── Requirements ──
    requirements.append("Select which columns are confounders vs. outcomes")

    score = max(0.0, min(1.0, score))

    rationale = (
        f"Detected binary treatment column '{grp['col']}' with "
        f"{n_covariates} potential covariate(s). "
        "Use this if assignment was NOT randomised and you have measured "
        "the confounders that influence both treatment and outcome."
    )

    return MethodCandidate(
        method="Causal Inference",
        score=round(score, 3),
        rationale=rationale,
        config_hint=config_hint,
        requirements=requirements,
        warnings=warnings,
    )


def _score_exploratory(signals: Dict[str, Any], max_other_score: float) -> MethodCandidate:
    """Floor option — always available."""
    numeric_cols = signals["numeric_cols"]
    score = 0.1
    if max_other_score < 0.3:
        score = 0.5  # boost when nothing else fits

    return MethodCandidate(
        method="Exploratory",
        score=round(score, 3),
        rationale=(
            "Could not determine a clear experimental structure. "
            "Explore distributions and correlations before designing a test."
        ),
        config_hint={"metrics": numeric_cols},
        warnings=["No obvious treatment/control assignment or time-series structure found."],
    )


# ──────────────────────── Main entry point ───────────────────────

def diagnose_data(df: pl.DataFrame) -> DiagnosisReport:
    """Heuristically diagnose the experiment type and suggest methods.

    Returns a :class:`DiagnosisReport` with *all* eligible methods ranked
    by fitness score.  The top-level ``suggested_method`` / ``rationale`` /
    ``config_hint`` / ``warnings`` fields are populated from ``candidates[0]``
    for backward compatibility.
    """
    signals = _detect_column_roles(df)

    # ── Score every method independently ──
    ab = _score_ab(signals)
    ts = _score_timeseries(signals)
    ci = _score_causal(signals)

    max_specific = max(ab.score, ts.score, ci.score)
    expl = _score_exploratory(signals, max_specific)

    # ── Rank by score descending, filter out score=0 (except Exploratory) ──
    all_candidates = [ab, ts, ci, expl]
    candidates = sorted(
        [c for c in all_candidates if c.score > 0],
        key=lambda c: c.score,
        reverse=True,
    )

    # Ensure at least Exploratory is present
    if not candidates:
        candidates = [expl]

    top = candidates[0]

    return DiagnosisReport(
        suggested_method=top.method,
        rationale=top.rationale,
        config_hint=top.config_hint,
        warnings=top.warnings,
        candidates=candidates,
        detected_signals=signals,
    )


# ──────────────────── Data Health Score (unchanged) ──────────────

def compute_data_health_score(
    df: pl.DataFrame, assignment_col: Optional[str] = None
) -> DataHealthReport:
    """Compute a data-quality readout for the Diagnose step.

    ``assignment_col``, when provided, enables the Group Balance dimension.
    When absent (e.g. time-series, exploratory) that axis is omitted rather
    than failed.
    """
    dims: List[HealthDimension] = []

    # ── Sample size ──
    n = df.height
    if n >= 1000:
        dims.append(HealthDimension(
            key="sample_size", label="Sample size", score=100, status="pass",
            detail=f"{n:,} rows — comfortable for most comparisons.",
        ))
    elif n >= 100:
        dims.append(HealthDimension(
            key="sample_size", label="Sample size", score=70, status="warn",
            detail=f"{n:,} rows — usable, but small effects may go undetected.",
        ))
    else:
        dims.append(HealthDimension(
            key="sample_size", label="Sample size", score=30, status="fail",
            detail=f"Only {n:,} rows — statistical power will be very limited.",
        ))

    # ── Group balance ──
    if assignment_col and assignment_col in df.columns:
        try:
            counts = (
                df.group_by(assignment_col).len().sort("len", descending=True)
            )
            sizes = counts.select("len").to_series().to_list()
            if len(sizes) >= 2 and sum(sizes) > 0:
                ratio = sizes[0] / sum(sizes)
                if ratio <= 0.55:
                    dims.append(HealthDimension(
                        key="balance", label="Group balance", score=100, status="pass",
                        detail=f"Largest group is {ratio:.0%} of total — well balanced.",
                    ))
                elif ratio <= 0.70:
                    dims.append(HealthDimension(
                        key="balance", label="Group balance", score=70, status="warn",
                        detail=f"Largest group is {ratio:.0%} of total — somewhat skewed.",
                    ))
                else:
                    dims.append(HealthDimension(
                        key="balance", label="Group balance", score=30, status="fail",
                        detail=f"Largest group is {ratio:.0%} of total — heavy imbalance.",
                    ))
        except Exception:  # noqa: BLE001
            pass

    # ── Missing data ──
    null_fracs = []
    for col in df.columns:
        try:
            null_fracs.append(df.select(pl.col(col).is_null().mean()).item())
        except Exception:  # noqa: BLE001
            null_fracs.append(0.0)
    worst_null = max(null_fracs) if null_fracs else 0.0
    if worst_null < 0.02:
        dims.append(HealthDimension(
            key="missing", label="Missing data", score=100, status="pass",
            detail="<2% missing in every column.",
        ))
    elif worst_null < 0.10:
        dims.append(HealthDimension(
            key="missing", label="Missing data", score=70, status="warn",
            detail=f"Worst column has {worst_null:.0%} missing.",
        ))
    else:
        dims.append(HealthDimension(
            key="missing", label="Missing data", score=30, status="fail",
            detail=f"Worst column has {worst_null:.0%} missing — investigate before analysis.",
        ))

    # ── Outlier risk: simple |z| > 5 share on numeric columns ──
    extreme_fracs = []
    for col in df.columns:
        if not df.schema[col].is_numeric():
            continue
        try:
            arr = df.select(pl.col(col).cast(pl.Float64)).drop_nulls().to_series()
            if arr.len() < 10:
                continue
            mean = arr.mean()
            std = arr.std()
            if std is None or std == 0:
                continue
            extreme = ((arr - mean).abs() / std > 5).mean()
            extreme_fracs.append(float(extreme or 0.0))
        except Exception:  # noqa: BLE001
            continue
    worst_extreme = max(extreme_fracs) if extreme_fracs else 0.0
    if worst_extreme < 0.005:
        dims.append(HealthDimension(
            key="outliers", label="Outlier risk", score=100, status="pass",
            detail="No column has more than 0.5% extreme values (|z|>5).",
        ))
    elif worst_extreme < 0.02:
        dims.append(HealthDimension(
            key="outliers", label="Outlier risk", score=70, status="warn",
            detail=f"Worst column has {worst_extreme:.1%} extreme values — consider winsorising.",
        ))
    else:
        dims.append(HealthDimension(
            key="outliers", label="Outlier risk", score=30, status="fail",
            detail=f"Worst column has {worst_extreme:.1%} extreme values — heavy tails.",
        ))

    overall = round(sum(d.score for d in dims) / max(len(dims), 1))
    if overall >= 85:
        status = "pass"
    elif overall >= 60:
        status = "warn"
    else:
        status = "fail"

    return DataHealthReport(
        overall_score=int(overall),
        overall_status=status,
        dimensions=dims,
    )
