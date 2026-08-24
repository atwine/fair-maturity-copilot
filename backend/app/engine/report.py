"""Groups findings by priority into the plain-language report. Adapter-agnostic
template with slots — never imports adapter content directly."""

from app.engine.models import Finding, Indicator, RemediationDraft
from app.engine.scoring import composite_score, rank


def build_report_markdown(
    *,
    findings: list[Finding],
    indicators_by_id: dict[str, Indicator],
    remediations_by_finding_id: dict[str, RemediationDraft],
) -> tuple[str, float]:
    score = composite_score(findings)
    lines = [f"## Overall score: {score}/100", ""]

    for f in rank(findings):
        if f.severity == "pass":
            continue
        indicator = indicators_by_id[f.indicator_id]
        remediation = remediations_by_finding_id.get(str(f.id))
        lines.append(f"### {indicator.title} ({f.severity.replace('_', ' ')})")
        if remediation:
            lines.append(remediation.remediation_text)
        lines.append("")

    return "\n".join(lines), score
