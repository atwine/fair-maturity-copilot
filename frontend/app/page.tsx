import Link from "next/link";
import { Button } from "@/components/ui/button";
import { SampleQuestionPreview } from "@/components/sample-question-preview";
import { SampleMeasurements } from "@/components/sample-measurements";

const STEPS = [
  {
    title: "Answer 12 plain-language questions",
    body: "About 10 minutes. Each one comes with a worked example, and \u201cI don\u2019t know\u201d is a perfectly fine answer.",
  },
  {
    title: "Get a score and a report",
    body: "See exactly which indicators are strong, which need work, and why \u2014 no jargon, nothing assumed.",
  },
  {
    title: "Follow concrete next steps",
    body: "Every gap comes with specific, doable actions \u2014 not \u201cfollow best practices.\u201d",
  },
];

export default function Home() {
  return (
    <main
      id="main-content"
      className="mx-auto w-full max-w-3xl flex-1 flex-col px-6 py-16 sm:py-20"
    >
      {/* ── Instrument header ─────────────────────────────────────── */}
      <section className="micro-fade border-b-2 border-foreground/20 pb-8">
        <div className="flex items-center gap-2 font-mono text-sm uppercase tracking-[0.15em] text-primary">
          <span className="size-2 rounded-full bg-primary" />
          <span>Calibrated &amp; ready</span>
        </div>
        <h1 className="mt-4 font-heading text-4xl font-semibold leading-[1.05] tracking-tight sm:text-5xl">
          Is your data actually FAIR?
        </h1>
        <p className="mt-4 text-base leading-relaxed text-justify text-muted-foreground">
          A guided, plain-language self-assessment for research group leads
          who don&rsquo;t have a data librarian on staff. No prior knowledge
          of data management assumed.
        </p>
      </section>

      {/* ── Sample measurements: the four principles as barrel readings */}
      <section className="mt-12">
        <div className="flex items-baseline justify-between">
          <h2 className="font-heading text-base font-semibold uppercase tracking-wider">
            Sample Measurements
          </h2>
          <span className="font-mono text-sm uppercase tracking-wider text-muted-foreground">
            4 readings &middot; illustrative
          </span>
        </div>

        {/* The instrument body — all four scales in one bordered box.
            Values randomize on each page load (client component). */}
        <SampleMeasurements />

        {/* Mobile descriptions */}
        <div className="mt-5 grid grid-cols-1 gap-3 sm:hidden">
          {[
            { letter: "F", color: "text-primary", blurb: "Can someone outside your team find out this dataset exists?" },
            { letter: "A", color: "text-gold", blurb: "Once found, is it clear how to actually get it?" },
            { letter: "I", color: "text-severity-unknown", blurb: "Is it in a format other tools and systems can read?" },
            { letter: "R", color: "text-severity-minor", blurb: "Is there enough context for someone else to use it correctly?" },
          ].map((m) => (
            <div key={m.letter} className="flex items-start gap-3">
              <span className={`font-heading text-base font-bold ${m.color}`}>
                {m.letter}
              </span>
              <p className="text-sm leading-snug text-muted-foreground">
                {m.blurb}
              </p>
            </div>
          ))}
        </div>

        {/* CTA — full-width, below the instrument body */}
        <div className="mt-6 border-t border-foreground/15 pt-6">
          <Button
            size="lg"
            nativeButton={false}
            className="w-full font-heading font-semibold"
            render={<Link href="/assessments/new">Take your own measurement</Link>}
          />
        </div>

        <p className="mt-6 border-t border-foreground/15 pt-6 text-sm leading-relaxed text-muted-foreground">
          These are sample measurements showing how each principle is scored.
          Your assessment will produce real readings based on your answers.
        </p>
      </section>

      {/* ── Full-width secondary action: see a sample question ────── */}
      <div className="mt-8 border-t border-foreground/15 pt-8">
        <SampleQuestionPreview />
      </div>

      {/* ── Measurement procedure: how-it-works ───────────────────── */}
      <section className="mt-12">
        <h2 className="font-heading text-base font-semibold uppercase tracking-wider">
          Measurement Procedure
        </h2>
        <div className="mt-2 h-px bg-foreground/20" />
        <div className="mt-6 flex flex-col">
          {STEPS.map((step, i) => (
            <div
              key={step.title}
              className={`micro-fade micro-fade-${i + 1} flex items-start gap-4 border-b border-foreground/10 py-5 ${i === 0 ? "border-t border-foreground/10" : ""}`}
            >
              <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center border border-foreground/25 font-mono text-sm font-bold text-primary">
                {i + 1}
              </span>
              <div>
                <p className="text-base font-semibold leading-snug">
                  {step.title}
                </p>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                  {step.body}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Full-width secondary action: find the right tool ──────── */}
      <div className="mt-8 border-t border-foreground/15 pt-8">
        <Button
          size="lg"
          nativeButton={false}
          className="w-full font-heading font-semibold"
          render={<Link href="/navigator">Find out which FAIR tool fits your situation &rarr;</Link>}
        />
      </div>

      {/* ── Footer: compact colophon ──────────────────────────────── */}
      <footer className="mt-10 border-t border-foreground/15 pt-5">
        <p className="text-sm leading-relaxed text-muted-foreground">
          Calibrated against the Research Data Alliance&rsquo;s FAIR Data
          Maturity Model &mdash; the closest thing to a standard way of
          measuring this. It defines{" "}
          <span className="font-semibold text-foreground">41 checks</span> in
          total; this tool asks the{" "}
          <span className="font-semibold text-foreground">12</span> a research
          lead can actually answer without specialist data-management
          knowledge.
        </p>
        <p className="mt-3 font-mono text-xs uppercase tracking-[0.15em] text-muted-foreground">
          FAIR Maturity Copilot &mdash; Micrometer &mdash; 2026
        </p>
      </footer>
    </main>
  );
}
