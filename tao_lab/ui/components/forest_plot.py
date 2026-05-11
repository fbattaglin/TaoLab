"""Refined forest plot for the prescription step.

Differences vs the v1 plot in `methods/ab_test.py::visualize`:

* Colours come from the design system (tangerine for sig+, danger for sig-,
  slate for non-sig) instead of the v1 raw greens/greys, and we vary symbol
  + opacity so the chart reads without colour.
* Hover rows are tabular, including p-value (raw + adjusted), CI, and n.
* Layout uses inter-friendly fonts, hairline grid, and tight margins so it
  exports cleanly to PDF / screenshots.
"""

from __future__ import annotations

import plotly.graph_objects as go

from tao_lab.methods.base import AnalysisResult


_TANGERINE = "#F97316"
_DANGER = "#DC2626"
_SLATE = "#94A3B8"
_HAIRLINE = "#E2E8F0"
_INDIGO_INK = "#0F172A"


def render_forest_plot(result: AnalysisResult) -> go.Figure:
    fig = go.Figure()

    if not result.metrics:
        fig.add_annotation(text="No metrics returned.", showarrow=False)
        return fig

    for m in result.metrics:
        # Translate absolute CI bounds onto the relative-lift axis where
        # possible. When control_mean is zero (or extremely small), absolute
        # bounds become unstable — fall back to absolute lift on the x-axis
        # for that metric so the chart is never misleading.
        if m.control_mean and abs(m.control_mean) > 1e-9:
            x = m.lift_relative
            err_plus = m.ci_upper / m.control_mean - m.lift_relative
            err_minus = m.lift_relative - m.ci_lower / m.control_mean
            x_label = "Relative lift"
            x_format = ".2%"
        else:
            x = m.lift_absolute
            err_plus = m.ci_upper - m.lift_absolute
            err_minus = m.lift_absolute - m.ci_lower
            x_label = "Absolute lift"
            x_format = ".4g"

        if m.is_significant:
            color = _TANGERINE if x >= 0 else _DANGER
            symbol = "diamond"
            opacity = 1.0
            size = 14
        else:
            color = _SLATE
            symbol = "circle-open"
            opacity = 0.85
            size = 12

        hover_lines = [f"<b>{m.metric_name}</b>"]
        if m.p_value is not None:
            hover_lines.append(f"p (raw): {m.p_value:.4g}")
        if m.p_value_adjusted is not None:
            hover_lines.append(f"p (BH-adjusted): {m.p_value_adjusted:.4g}")
        hover_lines.append(f"95% CI (abs): [{m.ci_lower:.4g}, {m.ci_upper:.4g}]")
        if m.n_control is not None and m.n_treatment is not None:
            hover_lines.append(f"n: {m.n_control:,} / {m.n_treatment:,}")
        if m.effect_size is not None and m.effect_size != 0:
            hover_lines.append(f"Cohen's d: {m.effect_size:.3g}")

        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[m.metric_name],
                error_x=dict(
                    type="data",
                    symmetric=False,
                    array=[max(err_plus, 0)],
                    arrayminus=[max(err_minus, 0)],
                    color=color,
                    thickness=1.5,
                    width=8,
                ),
                mode="markers",
                marker=dict(color=color, symbol=symbol, size=size, opacity=opacity,
                            line=dict(color=color, width=1.5)),
                name=m.metric_name,
                hovertemplate="<br>".join(hover_lines) + "<extra></extra>",
            )
        )

    fig.add_vline(
        x=0,
        line_dash="dot",
        line_color=_HAIRLINE,
        line_width=2,
        annotation_text="No effect",
        annotation_position="top left",
        annotation=dict(font=dict(size=11, color=_SLATE)),
    )

    fig.update_layout(
        title=dict(
            text="Lift & 95% confidence intervals",
            font=dict(size=14),
            x=0,
            xanchor="left",
        ),
        xaxis=dict(
            title=dict(text=x_label, font=dict(size=12, color=_SLATE)),
            showgrid=True,
            gridcolor=_HAIRLINE,
            zeroline=False,
            tickformat=x_format,
            tickfont=dict(family="ui-monospace, SF Mono, Menlo, monospace", size=11),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
        ),
        showlegend=False,
        margin=dict(l=20, r=20, t=50, b=40),
        height=max(180, 60 * len(result.metrics) + 90),
    )
    return fig
