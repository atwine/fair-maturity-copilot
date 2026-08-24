"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingState } from "@/components/loading-state";
import { PrincipleChip } from "@/components/fair-spectrum";
import { api, ApiError } from "@/lib/api-client";
import type { Finding, Report } from "@/lib/types";

const SEVERITY_LABEL: Record<Finding["severity"], string> = {
  pass: "Looks good",
  minor_gap: "Minor gap",
  major_gap: "Needs attention",
  unknown: "Worth finding out",
};

// Own severity chip, not shadcn's Badge variants -- this app has 4 distinct
// states (not shadcn's default/secondary/destructive/outline), so it needs
// its own semantic color set rather than being squeezed into a generic one.
const SEVERITY_STYLE: Record<Finding["severity"], string> = {
  pass: "bg-severity-pass-soft text-severity-pass",
  minor_gap: "bg-severity-minor-soft text-severity-minor",
  major_gap: "bg-severity-major-soft text-severity-major",
  unknown: "bg-severity-unknown-soft text-severity-unknown",
};

function SeverityBadge({ severity }: { severity: Finding["severity"] }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${SEVERITY_STYLE[severity]}`}
    >
      {SEVERITY_LABEL[severity]}
    </span>
  );
}

function scoreTone(score: number): string {
  if (score >= 80) return "text-severity-pass";
  if (score >= 50) return "text-severity-minor";
  return "text-severity-major";
}

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const runId = params.id;

  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [regenerating, setRegenerating] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getReport(runId)
      .then((r) => {
        if (!cancelled) setReport(r);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Couldn't load the report.");
      });
    return () => {
      cancelled = true;
    };
  }, [runId]);

  async function handleRegenerate(indicatorId: string) {
    setRegenerating(indicatorId);
    try {
      const updated = await api.regenerateFinding(runId, indicatorId);
      setReport((prev) =>
        prev
          ? {
              ...prev,
              findings: prev.findings.map((f) => (f.indicator_id === indicatorId ? { ...f, ...updated } : f)),
            }
          : prev
      );
    } catch {
      // leave the previous text in place -- a failed regenerate isn't worth losing the last good one over
    } finally {
      setRegenerating(null);
    }
  }

  if (error) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
        <p className="text-muted-foreground">{error}</p>
        <Button
          variant="outline"
          nativeButton={false}
          render={<Link href={`/assessments/${runId}/review`}>Back to review</Link>}
        />
      </main>
    );
  }

  if (!report) {
    return (
      <LoadingState
        title="Generating your report…"
        subtitle="Writing plain-language guidance for each gap can take a minute."
      />
    );
  }

  const needsAttention = report.findings.filter((f) => f.severity !== "pass");
  const looksGood = report.findings.filter((f) => f.severity === "pass");

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-10">
      <Card className="border-2">
        <CardContent className="flex items-center gap-6 pt-6">
          <span className={`font-heading text-6xl leading-none font-semibold tabular-nums ${scoreTone(report.score)}`}>
            {report.score}
          </span>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">out of 100</p>
            <p className="text-sm">
              {needsAttention.length === 0
                ? "Every indicator checked out clean."
                : `${needsAttention.length} of ${report.findings.length} indicators have something worth fixing.`}
            </p>
          </div>
        </CardContent>
      </Card>

      {needsAttention.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-heading text-lg font-semibold">Needs attention</h2>
          {needsAttention.map((finding) => (
            <Card key={finding.indicator_id}>
              <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
                <div className="flex min-w-0 items-center gap-2">
                  <PrincipleChip group={finding.principle_group} />
                  <CardTitle className="truncate text-base">{finding.title}</CardTitle>
                </div>
                <SeverityBadge severity={finding.severity} />
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm">{finding.remediation_text}</p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleRegenerate(finding.indicator_id)}
                  disabled={regenerating === finding.indicator_id}
                >
                  {regenerating === finding.indicator_id ? "Regenerating…" : "Regenerate this suggestion"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {looksGood.length > 0 && (
        <div className="space-y-2">
          <h2 className="font-heading text-lg font-semibold">Looks good</h2>
          <ul className="divide-y rounded-md border bg-card">
            {looksGood.map((f) => (
              <li key={f.indicator_id} className="flex items-center gap-3 p-3 text-sm">
                <PrincipleChip group={f.principle_group} />
                <span className="truncate">{f.title}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <Button
        variant="outline"
        nativeButton={false}
        render={<Link href="/assessments/new">Start another assessment</Link>}
      />
    </main>
  );
}
