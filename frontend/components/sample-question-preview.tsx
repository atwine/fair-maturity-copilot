"use client";

import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

const ANSWER_OPTIONS = ["Yes", "Partially", "No", "I don't know"];

// Addresses the CTA-preview gap: the page asks for a commitment before
// showing what that commitment looks like. This is a static mockup, not a
// live question -- deliberately not using RadioGroup, so a screen reader
// never reports it as an interactive control that does nothing.
export function SampleQuestionPreview() {
  return (
    <Collapsible className="w-full">
      <CollapsibleTrigger className="flex w-full items-center justify-center gap-2 rounded-md bg-primary px-6 py-3 font-heading text-base font-semibold text-primary-foreground transition-colors hover:bg-primary/90">
        See what a question looks like
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-4 rounded-md border border-foreground/20 bg-card p-5 text-left">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Question 3 of 12 &middot; Findable
        </p>
        <p className="mt-2 font-medium">
          Can someone outside your team find out this dataset exists?
        </p>
        <p className="mt-2 text-sm text-muted-foreground">
          Worked example: a dataset listed in a public repository or
          institutional catalog with a title and description counts, even
          without a formal metadata record.
        </p>
        <div className="mt-4 flex flex-wrap gap-2" aria-hidden="true">
          {ANSWER_OPTIONS.map((option) => (
            <Badge key={option} variant="outline">
              {option}
            </Badge>
          ))}
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          This is a preview &mdash; your answers aren&rsquo;t recorded until
          you start the real assessment.
        </p>
      </CollapsibleContent>
    </Collapsible>
  );
}
