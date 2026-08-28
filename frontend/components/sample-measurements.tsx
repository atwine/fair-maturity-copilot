"use client";

import { useEffect, useState } from "react";

// A measurement — the Micrometer's signature device. A horizontal barrel
// scale with tick marks and a thimble (a vertical marker) at the reading
// position. Each FAIR principle is rendered as a measurement.
function Measurement({
  letter,
  word,
  blurb,
  reading,
  thimblePos,
  color,
  index,
}: {
  letter: string;
  word: string;
  blurb: string;
  reading: number | null;
  thimblePos: string;
  color: string;
  index: number;
}) {
  return (
    <div className="flex items-start gap-4 border-b border-foreground/10 py-5 last:border-b-0">
      {/* Letter + label */}
      <div className="flex w-28 shrink-0 flex-col gap-1 sm:w-32">
        <span className={`font-heading text-xl font-bold ${color}`}>{letter}</span>
        <span className="text-sm font-semibold leading-tight">{word}</span>
      </div>

      {/* The barrel scale — a horizontal line with tick marks */}
      <div className="relative flex-1 pt-2">
        <div className="relative h-10">
          {/* Scale line */}
          <div className="absolute top-5 h-px w-full bg-foreground/30" />
          {/* Tick marks */}
          <div className="absolute top-5 flex w-full justify-between">
            {Array.from({ length: 21 }).map((_, i) => (
              <span
                key={i}
                className={`w-px ${i % 5 === 0 ? "h-3 bg-foreground/50" : "h-1.5 bg-foreground/25"}`}
              />
            ))}
          </div>
          {/* Scale numbers */}
          <div className="absolute top-9 flex w-full justify-between">
            {[0, 25, 50, 75, 100].map((n) => (
              <span key={n} className="font-mono text-xs text-muted-foreground">
                {n}
              </span>
            ))}
          </div>
          {/* Thimble — the vertical marker at the reading position.
              Slides in from the left on load. */}
          <div
            className={`micro-thimble micro-thimble-${index + 1} absolute top-0`}
            style={{ left: thimblePos, ["--thimble-pos" as string]: thimblePos }}
          >
            <div className={`h-10 w-0.5 ${color} bg-current`} />
            <div className={`-ml-1 mt-0.5 h-1.5 w-2.5 ${color} bg-current`} />
          </div>
        </div>
      </div>

      {/* Reading + description */}
      <div className="flex w-28 shrink-0 flex-col items-end gap-1 sm:w-44">
        <p className={`font-mono text-base font-bold ${color}`}>
          {reading !== null ? `${reading}%` : "\u2014"}
        </p>
        <p className="hidden text-sm leading-snug text-muted-foreground sm:block">
          {blurb}
        </p>
      </div>
    </div>
  );
}

const PRINCIPLES = [
  {
    letter: "F",
    word: "Findable",
    blurb: "Can someone outside your team find out this dataset exists?",
    color: "text-primary",
  },
  {
    letter: "A",
    word: "Accessible",
    blurb: "Once found, is it clear how to actually get it?",
    color: "text-gold",
  },
  {
    letter: "I",
    word: "Interoperable",
    blurb: "Is it in a format other tools and systems can read?",
    color: "text-severity-unknown",
  },
  {
    letter: "R",
    word: "Reusable",
    blurb: "Is there enough context for someone else to use it correctly?",
    color: "text-severity-minor",
  },
];

// Generate a random reading between 20 and 90 for each principle.
// Runs on mount (client-side), so values change on every page load / refresh.
export function SampleMeasurements() {
  const [readings, setReadings] = useState<number[] | null>(null);

  useEffect(() => {
    setReadings(
      PRINCIPLES.map(() => Math.floor(Math.random() * 71) + 20)
    );
  }, []);

  return (
    <div className="mt-5 border border-foreground/20 bg-card px-6 py-3">
      {PRINCIPLES.map((p, i) => {
        const reading = readings ? readings[i] : null;
        const thimblePos = reading !== null ? `${reading}%` : "0%";
        return (
          <Measurement
            key={p.letter}
            letter={p.letter}
            word={p.word}
            blurb={p.blurb}
            reading={reading}
            thimblePos={thimblePos}
            color={p.color}
            index={i}
          />
        );
      })}
    </div>
  );
}
