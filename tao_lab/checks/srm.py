import polars as pl
from scipy.stats import chisquare
from typing import Dict, Tuple

def check_srm(
    data: pl.DataFrame, 
    assignment_col: str, 
    expected_ratio: Dict[str, float]
) -> Tuple[float, bool]:
    """
    Perform a Chi-square test to detect Sample Ratio Mismatch (SRM).
    
    Args:
        data: The input polars DataFrame.
        assignment_col: Column name indicating the group (e.g., 'group' or 'variant').
        expected_ratio: Dictionary mapping group names to their expected proportions 
                        (e.g., {'control': 0.5, 'treatment': 0.5}).
                        
    Returns:
        A tuple of (p_value, srm_detected).
    """
    counts = data.group_by(assignment_col).count()
    
    # Ensure all expected groups are present
    observed_counts = []
    expected_counts = []
    total_count = data.height
    
    for group, ratio in expected_ratio.items():
        # Get count for the group, default to 0 if not found
        count_row = counts.filter(pl.col(assignment_col) == group)
        observed = count_row.select("count").to_series().to_list()[0] if not count_row.is_empty() else 0
        
        observed_counts.append(observed)
        expected_counts.append(ratio * total_count)
        
    # Chi-square goodness of fit
    _, p_val = chisquare(observed_counts, f_exp=expected_counts)
    
    # Convention: SRM detected if p-value < 0.001
    return p_val, p_val < 0.001
