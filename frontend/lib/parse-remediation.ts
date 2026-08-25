export interface ParsedRemediation {
  summary: string;
  steps: string[];
}

// Mirrors the SUMMARY:/STEPS: contract in
// backend/app/adapters/fair/prompts/remediation.jinja. Written defensively --
// an LLM won't always follow a format instruction to the letter, so this
// degrades to "whole text as summary, no steps" rather than showing nothing
// if STEPS: is missing or a step line doesn't match "1. ...".
export function parseRemediation(text: string): ParsedRemediation {
  // Anchored to the start of a line -- the prompt template always puts
  // STEPS: on its own line, so this won't misfire on a SUMMARY sentence
  // that happens to contain the word "steps:" mid-sentence.
  const stepsMatch = text.match(/^\s*STEPS:/im);
  if (!stepsMatch || stepsMatch.index === undefined) {
    return { summary: stripLabel(text, "SUMMARY:"), steps: [] };
  }

  const stepsIndex = stepsMatch.index;
  const summary = stripLabel(text.slice(0, stepsIndex), "SUMMARY:");
  const stepsBlock = text.slice(stepsIndex).replace(/^\s*STEPS:/im, "");
  const steps = stepsBlock
    .split(/\n+/)
    .map((line) => line.replace(/^\s*\d+[.)]\s*/, "").trim())
    .filter(Boolean);

  return { summary, steps };
}

function stripLabel(text: string, label: string): string {
  return text.replace(new RegExp(`^\\s*${label}`, "i"), "").trim();
}
