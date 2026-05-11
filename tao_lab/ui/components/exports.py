"""Prescription exports — Markdown, PDF, YAML config snapshot.

* `to_markdown(...)` returns a complete prescription document covering
  verdict, narration, caveats, next steps, and a metric table.
* `to_pdf_bytes(...)` renders the same document to a single-page A4 PDF
  using WeasyPrint. The dependency is declared as an optional extra in
  `pyproject.toml` (`pip install tao-lab[report]`); when missing, the
  function returns `None` and the caller surfaces a friendly hint.
* `to_yaml_config(...)` is a thin wrapper around the existing config snapshot
  so the side-rail copy button has a single import.
"""

from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Optional

import yaml

from tao_lab.interpret.narrator import (
    PrescriptionNarration,
    Verdict,
    render_markdown,
)
from tao_lab.methods.base import AnalysisResult

# Resolve once at import time; falls back gracefully if the file is absent.
_LOGO_PATH = Path(__file__).parent.parent / "static" / "tao_lab_logo.png"
_LOGO_B64: str = ""
if _LOGO_PATH.exists():
    _raw = _LOGO_PATH.read_bytes()
    _LOGO_B64 = base64.b64encode(_raw).decode()


_VERDICT_LABEL: dict[Verdict, str] = {
    "ship": "Ship it.",
    "hold": "Hold.",
    "dont_ship": "Don't ship.",
}

_VERDICT_COLOR = {
    "ship": "#059669",
    "hold": "#D97706",
    "dont_ship": "#DC2626",
}


# ─────────────────────────── Markdown ───────────────────────────
def to_markdown(
    result: AnalysisResult,
    narration: PrescriptionNarration,
    *,
    voice: str = "plain",
    business_question: str = "",
) -> str:
    body = render_markdown(narration, voice=voice)  # type: ignore[arg-type]

    # Prepend business question if provided
    if business_question:
        body = f"**Question:** {business_question}\n\n{body}"

    metric_rows = ["", "## Metrics", "", "| Metric | Lift | p (raw) | p (BH-adj) | 95% CI (abs) | Significant |", "|---|---|---|---|---|---|"]
    for m in result.metrics:
        p_raw = f"{m.p_value:.4g}" if m.p_value is not None else "—"
        p_adj = f"{m.p_value_adjusted:.4g}" if m.p_value_adjusted is not None else "—"
        sig = "yes" if m.is_significant else "no"
        metric_rows.append(
            f"| {m.metric_name} | {m.lift_relative * 100:+.2f}% | {p_raw} | {p_adj} | "
            f"[{m.ci_lower:.4g}, {m.ci_upper:.4g}] | {sig} |"
        )

    config_block = [
        "",
        "## Reproducibility",
        "",
        "```yaml",
        yaml.dump(result.config_snapshot.model_dump(), sort_keys=False).rstrip(),
        "```",
        "",
        f"_Method: {result.method_name}_  ",
        f"_SRM: {'detected' if result.srm_detected else 'passed'} (p = {result.srm_p_value:.4g})_",
        "",
    ]

    return body + "\n" + "\n".join(metric_rows) + "\n" + "\n".join(config_block)


# ─────────────────────────── PDF ───────────────────────────
def to_pdf_bytes(
    result: AnalysisResult,
    narration: PrescriptionNarration,
    *,
    voice: str = "plain",
    business_question: str = "",
) -> Optional[bytes]:
    """Return a single-page A4 PDF of the prescription, or None if WeasyPrint
    is not installed. Catching ImportError keeps the optional extra optional."""
    try:
        from weasyprint import HTML  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001
        return None

    html_doc = _render_html(result, narration, voice=voice, business_question=business_question)
    return HTML(string=html_doc).write_pdf()


def _render_html(
    result: AnalysisResult,
    narration: PrescriptionNarration,
    *,
    voice: str,
    business_question: str = "",
) -> str:
    pick = (lambda pair: pair.plain) if voice == "plain" else (lambda pair: pair.technical)
    next_steps = (
        narration.next_steps_plain if voice == "plain" else narration.next_steps_technical
    )

    verdict_label = _VERDICT_LABEL[narration.verdict]
    verdict_color = _VERDICT_COLOR[narration.verdict]
    headline = html.escape(pick(narration.headline))
    diagnosis = html.escape(pick(narration.diagnosis))
    recommendation = html.escape(pick(narration.recommendation))
    reasoning = html.escape(pick(narration.reasoning))

    caveat_html = ""
    for c in narration.caveats:
        body = c.body_plain if voice == "plain" else c.body_technical
        caveat_html += (
            f'<div class="caveat caveat--{c.severity}">'
            f"<div class=\"caveat__title\">{html.escape(c.title)}</div>"
            f"<div class=\"caveat__body\">{html.escape(body)}</div>"
            "</div>"
        )

    next_html = "".join(f"<li>{html.escape(s)}</li>" for s in next_steps)

    metric_rows = "".join(
        f'<tr><td>{html.escape(m.metric_name)}</td>'
        f'<td>{m.lift_relative * 100:+.2f}%</td>'
        f"<td>{(m.p_value if m.p_value is not None else float('nan')):.4g}</td>"
        f'<td>[{m.ci_lower:.4g}, {m.ci_upper:.4g}]</td>'
        f'<td>{"yes" if m.is_significant else "no"}</td></tr>'
        for m in result.metrics
    )

    css = """
    @page { size: A4; margin: 18mm 16mm; }
    body { font-family: -apple-system, "Inter", system-ui, sans-serif;
           color: #0F172A; font-size: 10.5pt; line-height: 1.45; }
    h1, h2, h3 { color: #1E3A5F; font-weight: 600; margin: 0; letter-spacing: -0.01em; }
    h1 { font-size: 22pt; }
    .eyebrow { color: #F97316; font-size: 9pt; letter-spacing: .14em;
               text-transform: uppercase; font-weight: 700; }
    .header { display: flex; justify-content: space-between; align-items: baseline;
              margin-bottom: 14pt; }
    .verdict { font-size: 18pt; font-weight: 700; }
    .headline { margin-top: 4pt; font-size: 12pt; }
    .section { margin-top: 14pt; }
    .section__label { font-size: 8.5pt; letter-spacing: .12em;
                       text-transform: uppercase; color: #475569; font-weight: 600;
                       margin-bottom: 4pt; }
    .caveat { border-left: 3px solid #94A3B8; padding: 6pt 10pt; margin: 4pt 0;
              background: #F8FAFC; }
    .caveat--warning { border-color: #D97706; background: #FFF7ED; }
    .caveat--critical { border-color: #DC2626; background: #FEF2F2; }
    .caveat__title { font-weight: 600; }
    .caveat__body { color: #0F172A; font-size: 10pt; }
    table { width: 100%; border-collapse: collapse; font-size: 9.5pt; }
    th, td { text-align: left; padding: 5pt 8pt; border-bottom: 1px solid #E2E8F0; }
    th { color: #475569; font-weight: 600; font-size: 9pt; text-transform: uppercase;
         letter-spacing: .04em; }
    td { font-variant-numeric: tabular-nums; }
    ol, ul { margin: 4pt 0 0 16pt; }
    li { margin-bottom: 2pt; }
    .footer { color: #94A3B8; font-size: 8.5pt; margin-top: 18pt; }
    """

    question_html = ""
    if business_question:
        question_html = (
            f'<div style="color:#475569;font-size:10pt;margin-bottom:8pt;">'
            f'<strong>Question:</strong> {html.escape(business_question)}</div>'
        )

    return f"""<!doctype html>
<html><head><meta charset="utf-8" /><style>{css}</style></head><body>
  <div class="header">
    <div>
      <div class="eyebrow">Prescription</div>
      <h1 style="color:{verdict_color};">{verdict_label}</h1>
      <div class="headline">{headline}</div>
      {question_html}
    </div>
    <div style="text-align:right;">
      {f'<img src="data:image/png;base64,{_LOGO_B64}" style="height:42pt;width:auto;" alt="Tao Lab" />' if _LOGO_B64 else '<div class="eyebrow">tao lab</div>'}
    </div>
  </div>

  <div class="section"><div class="section__label">Diagnosis</div><p>{diagnosis}</p></div>
  <div class="section"><div class="section__label">Recommendation</div><p>{recommendation}</p></div>
  <div class="section"><div class="section__label">Reasoning</div><p style="color:#475569;">{reasoning}</p></div>

  {f'<div class="section"><div class="section__label">Caveats</div>{caveat_html}</div>' if caveat_html else ''}
  {f'<div class="section"><div class="section__label">Next steps</div><ol>{next_html}</ol></div>' if next_html else ''}

  <div class="section">
    <div class="section__label">Metrics</div>
    <table>
      <thead><tr><th>Metric</th><th>Lift</th><th>p</th><th>95% CI</th><th>Sig?</th></tr></thead>
      <tbody>{metric_rows}</tbody>
    </table>
  </div>

  <div class="footer">
    Method: {html.escape(result.method_name)} ·
    SRM: {'detected' if result.srm_detected else 'passed'}
    (p = {result.srm_p_value:.4g})
  </div>
</body></html>"""


# ─────────────────────────── YAML ───────────────────────────
def to_yaml_config(result: AnalysisResult) -> str:
    return yaml.dump(result.config_snapshot.model_dump(), sort_keys=False)
