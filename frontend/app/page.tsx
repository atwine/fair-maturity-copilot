import Link from "next/link";
import { Button } from "@/components/ui/button";

const PRINCIPLES = [
  { letter: "F", word: "Findable", color: "text-primary", ring: "border-primary/30" },
  { letter: "A", word: "Accessible", color: "text-gold", ring: "border-gold/40" },
  { letter: "I", word: "Interoperable", color: "text-severity-unknown", ring: "border-severity-unknown/30" },
  { letter: "R", word: "Reusable", color: "text-severity-minor", ring: "border-severity-minor/40" },
];

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center gap-10 px-6 py-16 text-center">
      <div
        className="flex gap-3 sm:gap-5"
        aria-hidden="true"
      >
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
          A guided, plain-language self-assessment against the FAIR data principles &mdash; built
          for research group leads who don&rsquo;t have a data librarian on staff.
        </p>
      </div>

      <Button
        size="lg"
        nativeButton={false}
        render={<Link href="/assessments/new">Start an assessment</Link>}
      />

      <dl className="flex flex-wrap justify-center gap-x-8 gap-y-3 text-sm text-muted-foreground">
        {PRINCIPLES.map(({ letter, word, color }) => (
          <div key={letter} className="flex items-center gap-1.5">
            <dt className={`font-heading font-semibold ${color}`}>{letter}</dt>
            <dd>{word}</dd>
          </div>
        ))}
      </dl>
    </main>
  );
}
