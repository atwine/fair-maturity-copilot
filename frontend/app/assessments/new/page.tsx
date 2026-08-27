"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api-client";

// Issue #16: which check to start is read from how this page was reached
// (a link's ?adapter= param), not an upfront chooser screen shown to
// everyone -- the project owner explicitly wanted the harmonization check
// offered as a next step (from the report page, and from "Which tool fits?"),
// not a fork added to the front of the common, single-dataset path. An
// unrecognized or missing param falls back to today's default so every
// existing link into this page keeps working unchanged.
const ADAPTER_COPY: Record<string, { heading: string; description: string; label: string; placeholder: string }> = {
  "fair-v0": {
    heading: "What are we assessing?",
    description:
      "Give the dataset or collection a short, recognizable name — you'll see it on every screen and in the final report.",
    label: "Dataset or collection name",
    placeholder: "e.g. ACE Genomics Data Holdings — TB WGS dataset",
  },
  "harmonization-v0": {
    heading: "What initiative are we checking?",
    description:
      "Give the multi-site initiative or consortium a short, recognizable name — you'll see it on every screen and in the final report.",
    label: "Initiative or consortium name",
    placeholder: "e.g. 11-Center HIV Data Consortium",
  },
};
const DEFAULT_ADAPTER_ID = "fair-v0";

export default function NewAssessmentPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const adapterId = ADAPTER_COPY[searchParams.get("adapter") ?? ""] ? searchParams.get("adapter")! : DEFAULT_ADAPTER_ID;
  const copy = ADAPTER_COPY[adapterId];
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
      const run = await api.createAssessment(adapterId, subjectLabel.trim());
      const questions = await api.getQuestions(adapterId);
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
          <CardTitle className="font-heading text-2xl">{copy.heading}</CardTitle>
          <CardDescription>{copy.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="subject-label">{copy.label}</Label>
              <Input
                id="subject-label"
                value={subjectLabel}
                onChange={(e) => setSubjectLabel(e.target.value)}
                placeholder={copy.placeholder}
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
