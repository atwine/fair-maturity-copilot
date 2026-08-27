"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api-client";

const ADAPTER_ID = "fair-v0";

export default function NewAssessmentPage() {
  const router = useRouter();
  const [subjectLabel, setSubjectLabel] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // The database can take several seconds to wake from idle on its first
  // request (Neon's free-tier compute scales to zero) -- without this, a
  // slow-starting request looks identical to a hung one. Delayed rather
  // than shown immediately so it doesn't flicker on the common fast path.
  const [showSlowHint, setShowSlowHint] = useState(false);

  useEffect(() => {
    if (!submitting) return;
    const timer = setTimeout(() => setShowSlowHint(true), 2000);
    return () => clearTimeout(timer);
  }, [submitting]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!subjectLabel.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const run = await api.createAssessment(ADAPTER_ID, subjectLabel.trim());
      const questions = await api.getQuestions(ADAPTER_ID);
      router.push(`/assessments/${run.id}/question/${questions[0].indicator_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong starting the assessment.");
      setSubmitting(false);
    }
  }

  return (
    <main className="flex flex-1 items-center justify-center px-6 py-12">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle className="font-heading text-2xl">What are we assessing?</CardTitle>
          <CardDescription>
            Give the dataset or collection a short, recognizable name &mdash; you&rsquo;ll see it on
            every screen and in the final report.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="subject-label">Dataset or collection name</Label>
              <Input
                id="subject-label"
                value={subjectLabel}
                onChange={(e) => setSubjectLabel(e.target.value)}
                placeholder="e.g. ACE Genomics Data Holdings &mdash; TB WGS dataset"
                autoFocus
                required
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={submitting || !subjectLabel.trim()} className="w-full">
              {submitting ? "Starting..." : "Start assessment"}
            </Button>
            {submitting && showSlowHint && (
              <p className="text-center text-sm text-muted-foreground">
                Still going &mdash; this can take a few seconds the first time.
              </p>
            )}
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
