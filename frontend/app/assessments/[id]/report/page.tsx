"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingState } from "@/components/loading-state";
import { api, ApiError } from "@/lib/api-client";
import type { Finding, Report } from "@/lib/types";

const SEVERITY_LABEL: Record<Finding["severity"], string> = {
  pass: "Looks good",
  minor_gap: "Minor gap",
  major_gap: "Needs attention",
  unknown: "Worth finding out",
};

const SEVERITY_VARIANT: Record<Finding["severity"], "default" | "secondary" | "destructive" | "outline"> = {
  pass: "secondary",
  minor_gap: "outline",
  major_gap: "destructive",
  unknown: "outline",
};

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
      <Card>
        <CardHeader>
          <CardTitle className="text-3xl">{report.score}/100</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          {needsAttention.length === 0
            ? "Every indicator checked out clean."
            : `${needsAttention.length} of ${report.findings.length} indicators have something worth fixing.`}
        </CardContent>
      </Card>

      {needsAttention.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-medium text-muted-foreground">Needs attention</h2>
          {needsAttention.map((finding) => (
            <Card key={finding.indicator_id}>
              <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
                <CardTitle className="text-base">{finding.title}</CardTitle>
                <Badge variant={SEVERITY_VARIANT[finding.severity]}>{SEVERITY_LABEL[finding.severity]}</Badge>
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
          <h2 className="text-sm font-medium text-muted-foreground">Looks good</h2>
          <ul className="space-y-1 text-sm text-muted-foreground">
            {looksGood.map((f) => (
              <li key={f.indicator_id}>{f.title}</li>
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
