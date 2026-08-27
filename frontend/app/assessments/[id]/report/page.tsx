"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { LoadingState } from "@/components/loading-state";
import { PrincipleChip } from "@/components/fair-spectrum";
import { parseRemediation } from "@/lib/parse-remediation";
import { api, ApiError } from "@/lib/api-client";
import type { Finding, Report } from "@/lib/types";

const SEVERITY_LABEL: Record<Finding["severity"], string> = {
  pass: "Looks good",
  minor_gap: "Minor gap",
  major_gap: "Needs attention",
  unknown: "Worth finding out",
  not_started: "Not started yet",
};

// Own severity chip, not shadcn's Badge variants -- this app has 5 distinct
// states (not shadcn's default/secondary/destructive/outline), so it needs
// its own semantic color set rather than being squeezed into a generic one.
const SEVERITY_STYLE: Record<Finding["severity"], string> = {
  pass: "bg-severity-pass-soft text-severity-pass",
  minor_gap: "bg-severity-minor-soft text-severity-minor",
  major_gap: "bg-severity-major-soft text-severity-major",
  unknown: "bg-severity-unknown-soft text-severity-unknown",
  not_started: "bg-severity-not-started-soft text-severity-not-started",
};

function SeverityBadge({ severity }: { severity: Finding["severity"] }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-xs font-semibold ${SEVERITY_STYLE[severity]}`}
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
  // Only used to decide whether to show the "also check multi-site
  // harmonization" suggestion below (issue #16) -- the report itself
  // doesn't carry adapter_id, so this is a small, separate, non-blocking
  // fetch rather than a report-schema change. Not shown at all until this
  // resolves, so there's no risk of flashing the wrong suggestion.
  const [adapterId, setAdapterId] = useState<string | null>(null);

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
    api
      .getAssessment(runId)
      .then((a) => {
        if (!cancelled) setAdapterId(a.adapter_id);
      })
      .catch(() => {
        // Non-critical -- the suggestion card just stays hidden if this fails.
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

  // Three buckets, not two (issue #16): "not_started" is excluded from
  // needsAttention on purpose -- it has no score impact and isn't a
  // failure, so grouping it with real gaps would misrepresent it. It gets
  // its own section instead, between the two existing ones.
  const notStarted = report.findings.filter((f) => f.severity === "not_started");
  const needsAttention = report.findings.filter((f) => f.severity !== "pass" && f.severity !== "not_started");
  const looksGood = report.findings.filter((f) => f.severity === "pass");

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-10">
      <Card className="border-2">
        <CardContent className="flex items-center gap-6 pt-6">
          <span className={`font-heading text-6xl leading-none font-semibold tabular-nums ${scoreTone(report.score)}`}>
            {report.score}
          </span>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">out of 100</p>
            <p className="text-base">
              {needsAttention.length === 0 && notStarted.length === 0
                ? "Every indicator checked out clean."
                : needsAttention.length === 0
                  ? `${notStarted.length} indicator${notStarted.length === 1 ? "" : "s"} haven't been started yet -- that's not counted against you.`
                  : `${needsAttention.length} of ${report.findings.length} indicators have something worth fixing.`}
            </p>
          </div>
        </CardContent>
      </Card>

      {(needsAttention.length > 0 || notStarted.length > 0) && (
        <Button
          size="lg"
          nativeButton={false}
          render={<Link href={`/assessments/${runId}/plan`}>See your plan</Link>}
        />
      )}

      {adapterId === "fair-v0" && <HarmonizationSuggestionCard />}

      {needsAttention.length > 0 && (
        <div className="space-y-4">
          <h2 className="font-heading text-xl font-semibold">Needs attention</h2>
          {needsAttention.map((finding) => (
            <FindingCard
              key={finding.indicator_id}
              runId={runId}
              finding={finding}
              regenerating={regenerating === finding.indicator_id}
              onRegenerate={() => handleRegenerate(finding.indicator_id)}
            />
          ))}
        </div>
      )}

      {notStarted.length > 0 && (
        <div className="space-y-4">
          <h2 className="font-heading text-xl font-semibold">Not started yet</h2>
          <p className="text-sm text-muted-foreground">
            These haven&apos;t been counted against your score -- being early here is normal, not a failure.
          </p>
          {notStarted.map((finding) => (
            <FindingCard
              key={finding.indicator_id}
              runId={runId}
              finding={finding}
              regenerating={regenerating === finding.indicator_id}
              onRegenerate={() => handleRegenerate(finding.indicator_id)}
            />
          ))}
        </div>
      )}

      {looksGood.length > 0 && (
        <div className="space-y-4">
          <h2 className="font-heading text-xl font-semibold">Looks good</h2>
          {looksGood.map((finding) => (
            <FindingCard
              key={finding.indicator_id}
              runId={runId}
              finding={finding}
              regenerating={regenerating === finding.indicator_id}
              onRegenerate={() => handleRegenerate(finding.indicator_id)}
            />
          ))}
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

// Issue #16: offered here, on the finished report -- not as an upfront
// choice when someone starts a new assessment -- per the project owner's
// explicit call to keep the common, single-dataset path exactly as simple
// as it already is. Also reachable from the "Which tool fits?" page
// (components/navigator.tsx), per the same decision.
function HarmonizationSuggestionCard() {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-6">
        <div className="space-y-1">
          <p className="font-heading text-base font-semibold">Also coordinating data across multiple sites?</p>
          <p className="text-sm text-muted-foreground">
            Check how they fit together with a short, separate 6-question readiness check.
          </p>
        </div>
        <Button
          variant="outline"
          nativeButton={false}
          render={<Link href="/assessments/new?adapter=harmonization-v0">Check how they fit together</Link>}
        />
      </CardContent>
    </Card>
  );
}

function FindingCard({
  runId,
  finding,
  regenerating,
  onRegenerate,
}: {
  runId: string;
  finding: Finding;
  regenerating: boolean;
  onRegenerate: () => void;
}) {
  const { summary, steps } = parseRemediation(finding.remediation_text ?? "");
  const [open, setOpen] = useState(false);

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 space-y-0">
        <div className="flex min-w-0 items-center gap-2">
          <PrincipleChip group={finding.principle_group} />
          <CardTitle className="font-heading text-lg">{finding.title}</CardTitle>
        </div>
        <SeverityBadge severity={finding.severity} />
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-base leading-relaxed">{summary}</p>

        {steps.length > 0 && (
          <Collapsible open={open} onOpenChange={setOpen}>
            <CollapsibleTrigger
              className="flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
            >
              <ChevronDown className={`size-4 transition-transform ${open ? "rotate-180" : ""}`} />
              {open
                ? "Hide the steps"
                : finding.severity === "not_started"
                  ? `See ${steps.length} step${steps.length === 1 ? "" : "s"} to get started`
                  : `See ${steps.length} step${steps.length === 1 ? "" : "s"} to fix this`}
            </CollapsibleTrigger>
            <CollapsibleContent>
              <ol className="mt-3 space-y-2.5 border-l-2 border-border pl-4">
                {steps.map((step, i) => (
                  <li key={i} className="text-base leading-relaxed">
                    <span className="font-heading mr-1.5 font-semibold text-primary">{i + 1}.</span>
                    {step}
                  </li>
                ))}
              </ol>
            </CollapsibleContent>
          </Collapsible>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <Button
            size="sm"
            nativeButton={false}
            render={
              <Link href={`/assessments/${runId}/question/${finding.indicator_id}?from=report`}>
                Update your answer
              </Link>
            }
          />
          <Button size="sm" variant="outline" onClick={onRegenerate} disabled={regenerating}>
            {regenerating ? "Regenerating…" : "Regenerate this suggestion"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
