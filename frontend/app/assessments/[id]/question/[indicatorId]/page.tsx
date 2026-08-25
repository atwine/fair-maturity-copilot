"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { LoadingState } from "@/components/loading-state";
import { FairSpectrum } from "@/components/fair-spectrum";
import { api, ApiError } from "@/lib/api-client";
import type { Assessment, AnswerOut, AnswerValue, Question } from "@/lib/types";

const ADAPTER_ID = "fair-v0";

export default function QuestionPage() {
  const router = useRouter();
  const params = useParams<{ id: string; indicatorId: string }>();
  const { id: runId, indicatorId } = params;

  const [questions, setQuestions] = useState<Question[] | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [q, a] = await Promise.all([api.getQuestions(ADAPTER_ID), api.getAssessment(runId)]);
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
    return <ErrorState message={loadError} />;
  }
  if (!questions || !assessment) {
    return <LoadingState title="Loading this assessment…" />;
  }

  const currentIndex = questions.findIndex((q) => q.indicator_id === indicatorId);
  if (currentIndex === -1) {
    return <ErrorState message="That question doesn't exist for this assessment." />;
  }

  return (
    <QuestionForm
      // Remounts the form (and resets all its local state) whenever the
      // indicator changes -- the idiomatic React way to reset state on a
      // prop change, instead of syncing it via a useEffect.
      key={indicatorId}
      runId={runId}
      questions={questions}
      currentIndex={currentIndex}
      subjectLabel={assessment.subject_label}
      existingAnswer={assessment.answers.find((a) => a.indicator_id === indicatorId)}
      onAnswered={(updatedAnswer) =>
        setAssessment((prev) =>
          prev
            ? {
                ...prev,
                answers: [...prev.answers.filter((a) => a.indicator_id !== indicatorId), updatedAnswer],
                answered_indicator_ids: prev.answered_indicator_ids.includes(indicatorId)
                  ? prev.answered_indicator_ids
                  : [...prev.answered_indicator_ids, indicatorId],
              }
            : prev
        )
      }
    />
  );
}

function QuestionForm({
  runId,
  questions,
  currentIndex,
  subjectLabel,
  existingAnswer,
  onAnswered,
}: {
  runId: string;
  questions: Question[];
  currentIndex: number;
  subjectLabel: string;
  existingAnswer: AnswerOut | undefined;
  onAnswered: (answer: AnswerOut) => void;
}) {
  const router = useRouter();
  const question = questions[currentIndex];
  const isLast = currentIndex === questions.length - 1;

  const [value, setValue] = useState<AnswerValue | "">(existingAnswer?.value ?? "");
  const [note, setNote] = useState(existingAnswer?.note ?? "");
  const [showHelp, setShowHelp] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleNext() {
    if (!value) return;
    setSubmitting(true);
    setSubmitError(null);
    const selected = question.options.find((o) => o.value === value)!;
    try {
      const answer = await api.upsertAnswer(runId, question.indicator_id, {
        value: value as AnswerValue,
        label: selected.label,
        note: note.trim() || null,
      });
      onAnswered(answer);
      if (isLast) {
        router.push(`/assessments/${runId}/review`);
      } else {
        router.push(`/assessments/${runId}/question/${questions[currentIndex + 1].indicator_id}`);
      }
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : "Couldn't save that answer.");
      setSubmitting(false);
    }
  }

  function handleBack() {
    if (currentIndex === 0) return;
    router.push(`/assessments/${runId}/question/${questions[currentIndex - 1].indicator_id}`);
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-10">
      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Question {currentIndex + 1} of {questions.length}
          </span>
          <span className="truncate">{subjectLabel}</span>
        </div>
        <FairSpectrum
          principleGroups={questions.map((q) => q.principle_group)}
          completedThrough={currentIndex}
        />
      </div>

      <div className="space-y-3">
        <h1 className="font-heading text-2xl font-semibold text-balance">{question.plain_language_question}</h1>
        <div className="rounded-md border border-primary/20 bg-accent p-3 text-sm text-accent-foreground">
          <span className="font-semibold">For example: </span>
          {question.example}
        </div>
        <button
          type="button"
          onClick={() => setShowHelp((s) => !s)}
          className="text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground"
        >
          {showHelp ? "Hide" : "Why this matters"}
        </button>
        {showHelp && (
          <p className="rounded-md bg-muted p-3 text-sm text-muted-foreground">{question.help_text}</p>
        )}
      </div>

      <RadioGroup value={value} onValueChange={(v) => setValue(v as AnswerValue)} className="gap-3">
        {question.options.map((option) => (
          <Label
            key={option.value}
            htmlFor={option.value}
            className="flex cursor-pointer items-center gap-3 rounded-md border-2 border-border p-3 text-sm transition-colors has-[[data-checked]]:border-primary has-[[data-checked]]:bg-primary/5 has-[[data-checked]]:font-medium"
          >
            <RadioGroupItem value={option.value} id={option.value} />
            {option.label}
          </Label>
        ))}
      </RadioGroup>

      <div className="space-y-2">
        <Label htmlFor="note">Anything you want to add? (optional)</Label>
        <Textarea id="note" value={note} onChange={(e) => setNote(e.target.value)} rows={3} />
      </div>

      {submitError && <p className="text-sm text-destructive">{submitError}</p>}

      <div className="flex items-center justify-between pt-2">
        <Button type="button" variant="outline" onClick={handleBack} disabled={currentIndex === 0 || submitting}>
          Back
        </Button>
        <Button type="button" onClick={handleNext} disabled={!value || submitting}>
          {submitting ? "Saving…" : isLast ? "Review answers" : "Next"}
        </Button>
      </div>
    </main>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
      <Badge variant="destructive">Error</Badge>
      <p className="text-muted-foreground">{message}</p>
    </main>
  );
}
