"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { LoadingState } from "@/components/loading-state";
import { PrincipleChip } from "@/components/fair-spectrum";
import { api, ApiError } from "@/lib/api-client";
import type { Assessment, Question } from "@/lib/types";

export default function ReviewPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const runId = params.id;

  const [questions, setQuestions] = useState<Question[] | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [completing, setCompleting] = useState(false);
  const [completeError, setCompleteError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        // The assessment loads first -- its own adapter_id says which
        // adapter's questions to fetch (issue #16: no longer a single
        // hardcoded adapter for every run).
        const a = await api.getAssessment(runId);
        if (cancelled) return;
        const q = await api.getQuestions(a.adapter_id);
        if (cancelled) return;
        if (a.status === "completed") {
          router.replace(`/assessments/${runId}/report`);
          return;
        }
        setQuestions(q);
        setAssessment(a);
      } catch (err) {
        if (!cancelled) setLoadError(err instanceof ApiError ? err.message : "Couldn't load this assessment.");
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [runId, router]);

  if (loadError) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 text-center text-muted-foreground">
        {loadError}
      </main>
    );
  }
  if (!questions || !assessment) {
    return <LoadingState title="Loading your answers…" />;
  }

  const answersByIndicator = new Map(assessment.answers.map((a) => [a.indicator_id, a]));
  const missingCount = questions.filter((q) => !answersByIndicator.has(q.indicator_id)).length;

  async function handleComplete() {
    setCompleting(true);
    setCompleteError(null);
    try {
      await api.completeAssessment(runId);
      router.push(`/assessments/${runId}/report`);
    } catch (err) {
      setCompleteError(err instanceof ApiError ? err.message : "Couldn't complete the assessment.");
      setCompleting(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-10">
      <div className="space-y-1">
        <h1 className="font-heading text-2xl font-semibold">Review your answers</h1>
        <p className="text-sm text-muted-foreground">{assessment.subject_label}</p>
      </div>

      <ul className="divide-y rounded-md border bg-card">
        {questions.map((q) => {
          const answer = answersByIndicator.get(q.indicator_id);
          return (
            <li key={q.indicator_id} className="flex items-center justify-between gap-4 p-3">
              <div className="flex min-w-0 items-center gap-3">
                <PrincipleChip group={q.principle_group} />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{q.title}</p>
                  <p className="truncate text-sm text-muted-foreground">
                    {answer ? answer.label : "Not answered yet"}
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                nativeButton={false}
                render={
                  <Link href={`/assessments/${runId}/question/${q.indicator_id}`}>
                    {answer ? "Edit" : "Answer"}
                  </Link>
                }
              />
            </li>
          );
        })}
      </ul>

      {missingCount > 0 && (
        <p className="text-sm text-muted-foreground">
          {missingCount} question{missingCount === 1 ? "" : "s"} still need{missingCount === 1 ? "s" : ""} an answer
          before you can complete this assessment.
        </p>
      )}
      {completeError && <p className="text-sm text-destructive">{completeError}</p>}

      <Button onClick={handleComplete} disabled={missingCount > 0 || completing} className="w-full">
        {completing ? "Completing…" : "Complete assessment and generate report"}
      </Button>
    </main>
  );
}
