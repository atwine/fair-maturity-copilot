import Link from "next/link";
import { Search, KeyRound, Puzzle, Recycle } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const LETTERS = [
  { letter: "F", word: "Findable", blurb: "can someone find out it exists?", color: "text-primary", icon: Search },
  { letter: "A", word: "Accessible", blurb: "is it clear how to get it?", color: "text-gold", icon: KeyRound },
  { letter: "I", word: "Interoperable", blurb: "can other tools read it?", color: "text-severity-unknown", icon: Puzzle },
  { letter: "R", word: "Reusable", blurb: "enough context to use it right?", color: "text-severity-minor", icon: Recycle },
];

const TOOLS = [
  {
    name: "RDA FAIR Data Maturity Model",
    color: "text-primary",
    bg: "bg-primary/10",
    body: "The actual 41-question yardstick. Our 12 questions are drawn directly from it — everything else on this list either automates part of it, expands on it, or teaches you how to act on it.",
  },
  {
    name: "F-UJI",
    color: "text-severity-unknown",
    bg: "bg-severity-unknown-soft",
    body: "A robot that scans a public web page for your dataset and automatically checks the machine-readable parts — can a computer find your ID, read your metadata format. Never asks a human anything.",
  },
  {
    name: "FAIR Checker",
    color: "text-severity-unknown",
    bg: "bg-severity-unknown-soft",
    body: "Does essentially the same job as F-UJI, built by a different team. Checks the wrapping around your data, not what's inside it.",
  },
  {
    name: "FAIR-DSM",
    color: "text-gold",
    bg: "bg-gold-soft",
    body: "A 5-level roadmap for large institutions with real IT infrastructure. Levels 2–5 mean semantic databases and enterprise data governance — not built for one research group.",
  },
  {
    name: "FAIR Cookbook",
    color: "text-severity-minor",
    bg: "bg-severity-minor-soft",
    body: "A library of 60+ detailed \"recipes,\" one per topic. Genuinely useful once you know which recipe you need. Overwhelming if you don't — which is most people's actual starting point.",
  },
  {
    name: "ELIXIR FAIRification framework",
    color: "text-primary",
    bg: "bg-primary/10",
    body: "The one piece that isn't a checklist or a library — an actual process: set a goal, then work through concrete steps in order. The piece none of the other five do for you.",
  },
];

const FAQ = [
  {
    q: "Isn't this just reinventing F-UJI or FAIR Checker?",
    a: "No — different job entirely. Those tools check whether a computer program can read your published metadata. This tool checks your actual practices — a stated license, a data dictionary, a documented access process — the human side those tools structurally cannot see. If the machine-readable side ever needs double-checking too, that's a job for one of those existing tools, not something worth rebuilding.",
  },
  {
    q: "Why not just send people to the FAIR Cookbook?",
    a: "Because using it well requires already knowing what you're looking for. Someone who doesn't yet know what a \"data dictionary\" is won't know to go search for that recipe. This tool asks directly, in plain language, and only surfaces detail when it's relevant to the actual answer given.",
  },
  {
    q: "Is the RDA model the \"real\" standard, or did we pick an easy one?",
    a: "It's the real one — the same 41-indicator model referenced by F-UJI, by FAIR-DSM, by eLwazi's own guidance to researchers. We use a deliberately chosen 12-question subset: the ones answerable without a data science background, not a simplified or invented version.",
  },
  {
    q: "Does this replace institutional-level FAIR planning (FAIR-DSM)?",
    a: "No, and it isn't meant to. FAIR-DSM is the right tool once an institution is building shared infrastructure across many datasets. This tool is the right one for a single research group figuring out where they stand today.",
  },
];

export default function AboutPage() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-10 px-6 py-12">
      <div className="space-y-2">
        <p className="text-sm font-semibold tracking-wide text-primary uppercase">FAIR Maturity Copilot</p>
        <h1 className="font-heading text-4xl font-semibold text-balance">Why this tool exists</h1>
        <p className="text-lg leading-relaxed text-justify text-muted-foreground">
          For the moment someone asks &ldquo;why not just use [existing thing]?&rdquo;
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="font-heading text-xl font-semibold">Who this is for</h2>
        <p className="text-base leading-relaxed text-justify">
          A research group lead at an institution like ACE Uganda — someone responsible for their team&rsquo;s data,
          but without a data manager or data librarian on staff. They know their research. They were never trained
          in data stewardship, and nobody expects them to have been. But funders, collaborators, and good scientific
          practice increasingly expect research data to be <strong>FAIR</strong>: Findable, Accessible,
          Interoperable, Reusable.
        </p>
        <p className="text-base leading-relaxed text-justify">
          This tool exists because that person needs two things nothing else in this space gives them together: a
          way to find out, in plain language, whether their data practices are actually okay — and a clear, ordered
          plan for what to do about it if they&rsquo;re not. Not a technical report. Not a library to go research.
          An answer, and a next step.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-heading text-xl font-semibold">What &ldquo;FAIR&rdquo; actually means</h2>
        <p className="text-base leading-relaxed text-justify">Four questions about a dataset:</p>
        <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {LETTERS.map(({ letter, word, blurb, color, icon: Icon }) => (
            <div key={letter} className="flex items-center gap-3 rounded-md border bg-card p-4">
              <Icon className={`size-5 shrink-0 ${color}`} aria-hidden="true" />
              <dd className="text-sm">
                <span className="font-medium">{word}</span> — {blurb}
              </dd>
            </div>
          ))}
        </dl>
        <p className="text-base leading-relaxed text-justify">
          A formal international group, the Research Data Alliance, wrote a detailed &ldquo;maturity model&rdquo;
          defining 41 specific things to check across those four questions. This tool asks 12 of those 41 — the ones
          a non-technical research lead can actually answer about their own data, without a data science background.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-heading text-xl font-semibold">The landscape: what else is already out there</h2>
        <p className="text-base leading-relaxed text-justify">
          Before building this, we looked at six things the wider FAIR community already uses. Here&rsquo;s what
          each one actually is, in plain terms — because even people who&rsquo;ve sat through official training on
          this come away unsure how they all fit together. That confusion is not a personal failing. It&rsquo;s the
          actual state of this field.
        </p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {TOOLS.map((tool, i) => (
            <Card key={tool.name}>
              <CardContent className="space-y-2 pt-5">
                <span
                  className={`inline-flex size-6 items-center justify-center rounded-full font-heading text-sm font-semibold ${tool.bg} ${tool.color}`}
                >
                  {i + 1}
                </span>
                <h3 className="font-heading text-base font-semibold">{tool.name}</h3>
                <p className="text-sm text-muted-foreground">{tool.body}</p>
              </CardContent>
            </Card>
          ))}
        </div>
        <p className="text-base leading-relaxed text-justify">
          Not sure which of these applies to you?{" "}
          <Link href="/navigator" className="underline underline-offset-4 hover:text-foreground">
            Answer a few questions
          </Link>{" "}
          and we&rsquo;ll point you at the right one.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-heading text-xl font-semibold">Why we didn&rsquo;t just point people at one of these</h2>
        <p className="text-base leading-relaxed text-justify">
          Because none of them, on its own, solves the actual problem. The two automated checkers can&rsquo;t talk
          to a human in plain language. The two reference resources assume you already know which part applies to
          you — and one of them is scaled for institutions, not individuals. That leaves six different named tools,
          covering different, overlapping ground, with nothing telling a newcomer which one — if any — to even start
          with.
        </p>
        <p className="border-l-2 border-primary py-1 pl-5 font-heading text-xl leading-snug text-primary text-balance">
          That fragmentation isn&rsquo;t a minor inconvenience. It is, itself, the problem.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-heading text-xl font-semibold">What we built instead</h2>
        <p className="text-base leading-relaxed text-justify">
          One guided path. Answer 12 plain-language questions about your own data, each with a worked example, so
          you never have to already know a term before you can answer about it. Get a score and a plain-language
          report — what&rsquo;s working, what isn&rsquo;t, and why it matters, no jargon assumed. Then get a single
          ordered plan: not twelve separate suggestions to sequence yourself, but one walkthrough — identifiers, then
          documentation, then formats, then hosting, then sharing — the same order the FAIRification framework above
          describes, generated specifically from your own gaps.
        </p>
        <p className="text-base leading-relaxed text-justify">
          You never need to know the RDA model exists, or that F-UJI and FAIR Checker are two different tools doing
          the same thing, or which of 60+ Cookbook recipes applies to you. That&rsquo;s the whole point.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-heading text-xl font-semibold">Questions people are likely to ask</h2>
        <div className="space-y-3">
          {FAQ.map((item) => (
            <Card key={item.q}>
              <CardContent className="space-y-1.5 pt-5">
                <p className="font-heading text-base font-semibold">{item.q}</p>
                <p className="text-sm leading-relaxed text-justify text-muted-foreground">{item.a}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
