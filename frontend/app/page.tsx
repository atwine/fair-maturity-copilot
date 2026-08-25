import Link from "next/link";
import { Button } from "@/components/ui/button";

const PRINCIPLES = [
  {
    letter: "F",
    word: "Findable",
    blurb: "Can someone outside your team find out this dataset exists?",
    color: "text-primary",
    ring: "border-primary/30",
  },
  {
    letter: "A",
    word: "Accessible",
    blurb: "Once found, is it clear how to actually get it?",
    color: "text-gold",
    ring: "border-gold/40",
  },
  {
    letter: "I",
    word: "Interoperable",
    blurb: "Is it in a format other tools and systems can read?",
    color: "text-severity-unknown",
    ring: "border-severity-unknown/30",
  },
  {
    letter: "R",
    word: "Reusable",
    blurb: "Is there enough context for someone else to use it correctly?",
    color: "text-severity-minor",
    ring: "border-severity-minor/40",
  },
];

const STEPS = [
  {
    title: "Answer 12 plain-language questions",
    body: "About 10 minutes. Each one comes with a worked example, and \"I don't know\" is a perfectly fine answer.",
  },
  {
    title: "Get a score and a report",
    body: "See exactly which indicators are strong, which need work, and why — no jargon, nothing assumed.",
  },
  {
    title: "Follow concrete next steps",
    body: "Every gap comes with specific, doable actions — not \"follow best practices.\"",
  },
];

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center gap-16 px-6 py-16">
      <div className="flex flex-col items-center gap-10 text-center">
        <div className="flex gap-3 sm:gap-5" aria-hidden="true">
          {PRINCIPLES.map(({ letter, color, ring }) => (
            <span
              key={letter}
              className={`flex size-14 items-center justify-center rounded-full border-2 bg-card font-heading text-2xl font-semibold sm:size-16 sm:text-3xl ${color} ${ring}`}
            >
              {letter}
            </span>
          ))}
        </div>

        <div className="max-w-xl space-y-4">
          <h1 className="font-heading text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
            Is your data actually FAIR?
          </h1>
          <p className="text-lg text-muted-foreground text-balance">
            A guided, plain-language self-assessment for research group leads who don&rsquo;t
            have a data librarian on staff — no prior knowledge of data management assumed.
          </p>
        </div>

        <Button size="lg" nativeButton={false} render={<Link href="/assessments/new">Start an assessment</Link>} />
      </div>

      <dl className="grid w-full grid-cols-1 gap-4 sm:grid-cols-2">
        {PRINCIPLES.map(({ letter, word, blurb, color }) => (
          <div key={letter} className="flex items-start gap-3 rounded-md border bg-card p-4">
            <dt className={`font-heading text-xl font-semibold ${color}`}>{letter}</dt>
            <dd>
              <p className="font-medium">{word}</p>
              <p className="text-sm text-muted-foreground">{blurb}</p>
            </dd>
          </div>
        ))}
      </dl>

      <div className="w-full space-y-6">
        <h2 className="text-center font-heading text-xl font-semibold">How this works</h2>
        <ol className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          {STEPS.map((step, i) => (
            <li key={step.title} className="space-y-1.5">
              <span className="font-heading text-sm font-semibold text-primary">{i + 1}</span>
              <p className="font-medium">{step.title}</p>
              <p className="text-sm text-muted-foreground">{step.body}</p>
            </li>
          ))}
        </ol>
      </div>

      <p className="max-w-xl text-center text-sm text-muted-foreground">
        Based on the Research Data Alliance&rsquo;s FAIR Data Maturity Model — the closest
        thing to a standard way of measuring this. It defines 41 checks in total; this tool
        asks the 12 a research lead can actually answer without specialist data-management
        knowledge.
      </p>
    </main>
  );
}
