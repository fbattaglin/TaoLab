import numpy as np
from typing import List
from tao_lab.methods.base import MetricResult

def apply_fdr_correction(metrics: List[MetricResult], alpha: float = 0.05) -> List[MetricResult]:
    """
    Apply Benjamini-Hochberg (FDR) correction to a list of MetricResults.
    """
    if not metrics:
        return metrics

    p_values = [m.p_value for m in metrics if m.p_value is not None]
    if not p_values:
        return metrics

    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    m = len(sorted_p)
    
    # Calculate BH adjusted p-values
    # adj_p = p * m / rank
    adj_p = np.zeros(m)
    prev_adj_p = 1.0
    for i in range(m - 1, -1, -1):
        rank = i + 1
        current_adj_p = min(prev_adj_p, sorted_p[i] * m / rank)
        adj_p[i] = current_adj_p
        prev_adj_p = current_adj_p

    # Map back to original metrics
    p_idx = 0
    for i, metric in enumerate(metrics):
        if metric.p_value is not None:
            # Find the rank of this metric's p-value in the sorted list
            # Since multiple metrics could have same p-value, we map carefully
            # But for simplicity, we'll just use the sorted array mapping
            pass
    
    # Better mapping:
    final_adj_p = np.zeros(len(p_values))
    final_adj_p[sorted_indices] = adj_p
    
    p_val_ptr = 0
    for metric in metrics:
        if metric.p_value is not None:
            adj = float(final_adj_p[p_val_ptr])
            # Phase C: keep the raw p-value intact and store the adjusted value
            # in its own field. Significance is decided on the adjusted value;
            # downstream UI surfaces both side-by-side so reviewers can see
            # whether BH changed the verdict.
            metric.p_value_adjusted = adj
            metric.is_significant = adj < alpha
            p_val_ptr += 1

    return metrics
