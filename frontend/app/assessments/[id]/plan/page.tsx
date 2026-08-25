"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { LoadingState } from "@/components/loading-state";
import { PrincipleChip } from "@/components/fair-spectrum";
import { api, ApiError } from "@/lib/api-client";
import type { Plan } from "@/lib/types";

export default function PlanPage() {
  const params = useParams<{ id: string }>();
  const runId = params.id;

  const [plan, setPlan] = useState<Plan | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getPlan(runId)
      .then((p) => {
        if (!cancelled) setPlan(p);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Couldn't build a plan.");
      });
    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (error) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
        <p className="text-muted-foreground">{error}</p>
        <Button
          variant="outline"
          nativeButton={false}
          render={<Link href={`/assessments/${runId}/report`}>Back to report</Link>}
        />
      </main>
    );
  }

  if (!plan) {
    return (
      <LoadingState
        title="Building your plan…"
        subtitle="Sequencing your gaps into an order that actually makes sense can take a moment."
      />
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-10">
      <div className="space-y-2">
        <p className="text-sm font-medium text-muted-foreground">Your FAIRification plan</p>
        <h1 className="font-heading text-3xl font-semibold text-balance">{plan.goal}</h1>
      </div>

      {plan.steps.length === 0 ? (
        <Card className="border-2 border-severity-pass/30">
          <CardContent className="pt-6 text-base">
            Nothing left to plan for — every indicator already checked out clean.
          </CardContent>
        </Card>
      ) : (
        <ol className="space-y-5">
          {plan.steps.map((step, i) => (
            <li key={step.id}>
              <Card>
                <CardContent className="space-y-3 pt-6">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <span className="font-heading text-2xl leading-none font-semibold text-primary tabular-nums">
                        {i + 1}
                      </span>
                      <div className="space-y-1.5">
                        <h2 className="font-heading text-lg font-semibold">{step.title}</h2>
                        <p className="text-base leading-relaxed">{step.detail}</p>
                      </div>
                    </div>
                    <Link
                      href={`/assessments/${runId}/mentor/${step.id}`}
                      title="Talk this whole step through with the mentor"
                      aria-label={`Talk through "${step.title}" with the mentor`}
                      className="flex size-8 shrink-0 items-center justify-center rounded-full border bg-card text-muted-foreground hover:border-primary hover:text-primary"
                    >
                      <MessageCircle className="size-4" />
                    </Link>
                  </div>
                  <ul className="flex flex-wrap gap-2 pl-9">
                    {step.indicators.map((indicator) => (
                      <li key={indicator.indicator_id}>
                        <Link
                          href={`/assessments/${runId}/question/${indicator.indicator_id}?from=plan`}
                          className="flex items-center gap-1.5 rounded-full border bg-card px-2.5 py-1 text-xs hover:border-primary"
                        >
                          <PrincipleChip group={indicator.principle_group} />
                          {indicator.title}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </li>
          ))}
        </ol>
      )}

      <div className="flex items-center justify-between pt-2">
        <Button
          variant="outline"
          nativeButton={false}
          render={<Link href={`/assessments/${runId}/report`}>Back to report</Link>}
        />
        <Button
          variant="outline"
          nativeButton={false}
          render={<Link href="/assessments/new">Start another assessment</Link>}
        />
      </div>
    </main>
  );
}
