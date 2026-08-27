"use client";

import { useState } from "react";
import Link from "next/link";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// A branching guide that turns the flat list of FAIR tools on /about
// into an actual answer: which one fits this person, at their current stage.
// Issue #18 — pure client-side, no backend, no extensible quiz engine.
//
// Each destination is a mini-roadmap: what the tool does, why it fits,
// how to use it, what to do after, and a newbie/experienced split.

type DestinationId =
  | "this-tool"
  | "fair-aware"
  | "f-uji"
  | "cookbook"
  | "ontology-tools"
  | "level-2"
  | "coretrustseal";

type Destination = {
  id: DestinationId;
  name: string;
  tagline: string;
  whatItDoes: string;
  whyItFits: string;
  howToUse: string;
  whatsNext: string;
  externalUrl?: string;
  externalLabel?: string;
  externalUrl2?: string;
  externalLabel2?: string;
  internalHref?: string;
  internalLabel?: string;
  newbie: string;
  experienced: string;
};

const DESTINATIONS: Record<DestinationId, Destination> = {
  "this-tool": {
    id: "this-tool",
    name: "FAIR Maturity Copilot",
    tagline: "This tool — a guided, plain-language self-assessment",
    whatItDoes:
      "Asks you 12 plain-language questions about your own data practices — each with a worked example so you never need to know a term before answering about it. You get a score, a plain-language report of what's working and what isn't, and a single ordered remediation plan: identifiers, then documentation, then formats, then hosting, then sharing — generated specifically from your own gaps.",
    whyItFits:
      "You said you're figuring out where you stand with your own group's data. That's exactly what this tool is built for — finding out, in plain language, whether your practices are actually okay, without needing a data science background or prior knowledge of FAIR jargon.",
    howToUse:
      "Click 'Start an assessment' below. You'll answer 12 questions about your dataset — things like 'does your dataset have a persistent identifier (like a DOI)?' with a plain-language example for each. It takes about 10-15 minutes. At the end you get a score, a report, and a prioritized plan.",
    whatsNext:
      "Once you've completed the assessment and worked through your remediation plan, come back and re-assess to see your progress. If you later publish your dataset online, you can also run F-UJI or FAIR Checker to double-check the machine-readable side — this tool covers the human practices those tools can't see.",
    internalHref: "/",
    internalLabel: "Start an assessment",
    newbie:
      "Start here. Every question has a worked example and plain-language explanation — you won't need to know what 'persistent identifier' or 'controlled vocabulary' means before answering. The report uses plain language too.",
    experienced:
      "If you already know FAIR concepts well, the 12 questions will go fast (~5 minutes). The value is in the prioritized remediation plan — it sequences your gaps into one walkthrough rather than leaving you to figure out what to fix first.",
  },
  "fair-aware": {
    id: "fair-aware",
    name: "FAIR-Aware",
    tagline: "A self-assessment of your knowledge of FAIR — not your data",
    whatItDoes:
      "FAIR-Aware (built by DANS, the Dutch national data archive) asks 10 questions about your awareness of the FAIR principles — not about your specific dataset. For each question, it provides rich guidance text explaining what the principle means and why it matters. It takes 10-30 minutes and produces an overview of your awareness level plus tips for improvement. It also has a trainer mode for running group sessions.",
    whyItFits:
      "You said you're new to FAIR and still learning what it means. FAIR-Aware is the pedagogical first step — it teaches you the concepts before you try to assess your data against them. Jumping straight into a dataset assessment without understanding what 'Findable' or 'Interoperable' actually ask for would be frustrating.",
    howToUse:
      "Go to fairaware.dans.knaw.nl. You don't need an account. Answer the 10 awareness questions — each one has guidance text you can expand if a term is unfamiliar. At the end you'll see your awareness score across F, A, I, and R, with links to learn more about each gap.",
    whatsNext:
      "Once you understand the FAIR principles, come back here and run our 12-question assessment on your actual dataset. You'll be equipped to answer meaningfully, and the remediation plan will make sense because you'll know what each step is for.",
    externalUrl: "https://fairaware.dans.knaw.nl/",
    externalLabel: "Go to FAIR-Aware",
    newbie:
      "This is the right starting point for you. The guidance text for each question explains the concept in plain language. Take your time — the point is learning, not speed.",
    experienced:
      "If you already know FAIR well, skip this and go straight to our 12-question assessment. FAIR-Aware is pedagogical, not evaluative — it won't tell you anything you don't already know.",
  },
  "f-uji": {
    id: "f-uji",
    name: "F-UJI or FAIR Checker",
    tagline: "Automated tools that scan your published dataset's metadata",
    whatItDoes:
      "F-UJI (built by FAIRsFAIR/PANGAEA) and FAIR Checker (built by the French Institute for Bioinformatics) are automated web tools. You give them a dataset identifier (typically a DOI or URL), and they fetch the metadata from the public page and run automated checks: can a computer find the ID, read the metadata format, see the license, resolve the landing page? They produce a numeric FAIR score and a detailed report. They never ask a human anything — they check the machine-readable wrapping around your data, not the data practices themselves.",
    whyItFits:
      "You said your dataset is already published online and you want to double-check whether a computer can automatically read its metadata. That's exactly what these tools do — they fetch your dataset's public page and test it against the RDA FAIR indicators that can be checked automatically.",
    howToUse:
      "Go to f-uji.net (or fair-checker.france-bioinformatique.fr). Paste your dataset's DOI or URL. The tool fetches the metadata and runs the checks in seconds. You get a score per FAIR principle and a detailed breakdown of what passed and what failed. No account needed for either tool.",
    whatsNext:
      "If F-UJI/FAIR Checker flags issues (missing license, missing metadata format, dead links), fix those at the repository level. Then come back here and run our 12-question assessment — it covers the human practices (data dictionary, access process, provenance) that automated tools structurally cannot see. The two together give you the full picture.",
    externalUrl: "https://www.f-uji.net/",
    externalLabel: "Go to F-UJI",
    newbie:
      "Don't worry — these tools are fully automated. You just paste a URL and read the results. The report uses some technical terms (like 'metadata schema' or 'content negotiation'), but each check has a plain-language explanation of what it tested and what it found.",
    experienced:
      "F-UJI is the most-used automated checker and aligns with the FAIRsFAIR metrics. FAIR Checker uses knowledge graphs and SHACL constraints, and also has an 'Inspect' module that helps you improve metadata quality, not just score it. If you work in life sciences or bioinformatics, FAIR Checker's Bioschemas profiling may be more relevant.",
  },
  cookbook: {
    id: "cookbook",
    name: "The FAIR Cookbook",
    tagline: "A library of 60+ step-by-step recipes for specific FAIR topics",
    whatItDoes:
      "The FAIR Cookbook (built by ELIXIR and FAIRplus) is an online, open resource with 60+ detailed 'recipes' — one per FAIR topic. Each recipe is a hands-on, technical walkthrough: how to write a data dictionary, how to set up persistent identifiers, how to choose a metadata schema, how to use the FAIRplus Data Maturity Model. Recipes are organized by FAIR element, audience type, reading time, and difficulty level. It's an ELIXIR Recommended Interoperability Resource.",
    whyItFits:
      "You said you already know which specific FAIR topic you need help with. The Cookbook is most useful when you can search for what you need — 'I need to write a data dictionary' or 'I need to set up persistent identifiers' — and follow the recipe step by step. It's overwhelming as a starting point, but exactly right when you know your topic.",
    howToUse:
      "Go to faircookbook.elixir-europe.org. Browse the recipe index or search for your topic. Each recipe tells you the difficulty level, reading time, and audience. Follow the steps — they include concrete examples, tools, and standards to use.",
    whatsNext:
      "Once you've applied the recipe to your dataset, come back here and run our 12-question assessment to check where you stand across all FAIR dimensions — not just the one you fixed. The Cookbook solves one topic at a time; this tool gives you the overall picture and prioritizes what to fix next.",
    externalUrl: "https://faircookbook.elixir-europe.org/",
    externalLabel: "Go to the FAIR Cookbook",
    newbie:
      "Filter by 'difficulty level: beginner' and 'reading time: short' to find recipes that won't overwhelm you. The 'FAIRification framework' and 'maturity model' recipes are good starting points — they explain the landscape before diving into specifics.",
    experienced:
      "The Cookbook is technical and assumes domain knowledge. Use it as a reference — search for the specific recipe you need. The FAIRplus DSM model recipe (faircookbook.elixir-europe.org/content/recipes/maturity.html) is particularly useful if you're working on dataset maturity across levels.",
  },
  "ontology-tools": {
    id: "ontology-tools",
    name: "O'FAIRe and FOOPS!",
    tagline: "FAIRness assessment for ontologies and semantic artefacts",
    whatItDoes:
      "O'FAIRe (built by the AgroPortal team) and FOOPS! (built by the Ontology Engineering Group at UPM) are automated tools that assess the FAIRness of ontologies, vocabularies, and semantic artefacts — not datasets. O'FAIRe runs 61 checks (80% based on metadata) and produces a FAIRness wheel visualization. FOOPS! runs 24 checks across the four FAIR dimensions and provides explanations for failures plus suggestions to fix them. Both work on OWL and SKOS vocabularies.",
    whyItFits:
      "You said you're working with ontologies or semantic artefacts, not datasets. Dataset-focused tools like F-UJI or this tool's 12 questions don't apply to ontologies — they check different things. O'FAIRe and FOOPS! are purpose-built for the semantic artefact world.",
    howToUse:
      "For O'FAIRe: go to agroportal.eu, search for your ontology (e.g. AGRO), and view the FAIRness score on its summary page — O'FAIRe is built directly into AgroPortal. For FOOPS!: go to w3id.org/foops and enter your ontology URI. Both produce scores and detailed breakdowns. No account needed for either.",
    whatsNext:
      "Once your ontology passes O'FAIRe/FOOPS! checks, it's FAIR as a semantic artefact. If you're also using this ontology to make datasets FAIR, you can then run our 12-question assessment on the datasets that use it — the ontology being FAIR is a prerequisite for the datasets being Interoperable.",
    externalUrl: "https://w3id.org/foops/",
    externalLabel: "Go to FOOPS!",
    externalUrl2: "https://agroportal.eu/",
    externalLabel2: "Go to AgroPortal (O'FAIRe)",
    newbie:
      "If you're not sure whether you're working with an 'ontology' vs a 'dataset' — an ontology is a structured vocabulary that defines concepts and relationships (like a formal data dictionary with terms and their meanings). If that's what you have, these tools are for you. Start with FOOPS! — its error messages are more beginner-friendly.",
    experienced:
      "O'FAIRe is integrated into AgroPortal, EcoPortal, and other OntoPortal instances — if your ontology is already deposited there, the assessment is automatic. FOOPS! also has a REST API if you want to integrate it into a CI pipeline. Both are open source.",
  },
  "level-2": {
    id: "level-2",
    name: "This tool's Level 2 + FAIR-DSM",
    tagline: "For coordinating data across multiple sites or organizations",
    whatItDoes:
      "When you're coordinating data across multiple sites, the single-group 12 questions aren't enough. This tool's planned Level 2 content covers field-level consistency and shared data dictionaries across sites — the harmonization readiness that has to happen before any common data model conversion. FAIR-DSM (the FAIRplus Dataset Maturity Model) covers the same ground from the institutional-infrastructure side: it defines 5 maturity levels across content, representation, and hosting environment capabilities, with indicators at dataset, field, and value-set granularity.",
    whyItFits:
      "You said you're coordinating data across multiple sites or organizations. That's a fundamentally different problem from a single group checking their own practices — it requires harmonization across data sources, shared metadata standards, and infrastructure that can support cross-site querying. No single tool solves this; it's a combination of this tool's Level 2 assessment plus the FAIR-DSM framework.",
    howToUse:
      "First, run our 12-question assessment on each site's data independently to establish a baseline. Then review the FAIR-DSM model (fairplus.github.io/Data-Maturity) to understand what Level 2 requires across content, representation, and hosting. The gap between your baseline and DSM Level 2 is your work plan.",
    whatsNext:
      "Once each site passes the 12-question baseline and you've closed the Level 2 gaps, the next step is FAIR-DSM Level 3 — semantic databases and shared query infrastructure. That's typically where institutional IT and data governance teams take over. If your repository needs external trustworthiness certification, look at CoreTrustSeal.",
    internalHref: "/about",
    internalLabel: "Read more about the landscape",
    newbie:
      "Start by understanding what 'harmonization' means in practice: it's making sure that when Site A says 'patient_age' and Site B says 'age_years', a computer can tell they're the same thing. That requires shared data dictionaries and agreed-upon field definitions. Run our 12 questions first to see where each site stands individually.",
    experienced:
      "The FAIR-DSM model's three granularity levels (dataset, field, value-set) map well to a phased rollout: harmonize dataset-level metadata first, then field-level definitions, then controlled value sets. The DSM indicators are the concrete checklist. If you're building shared infrastructure, also look at FAIR Implementation Profiles (FIPs) — the emerging standard for declaring a community's specific FAIR choices.",
  },
  coretrustseal: {
    id: "coretrustseal",
    name: "CoreTrustSeal",
    tagline: "Certification that your repository is trustworthy — not just FAIR",
    whatItDoes:
      "CoreTrustSeal is an external certification for data repositories, not datasets. It requires a substantive application documenting governance, sustainability, technical infrastructure, data quality, and discoverability, followed by external peer review. It's more rigorous than FAIR self-assessment because it's audited. By 2026 most major institutional and disciplinary repositories are CoreTrustSeal-certified, and it's increasingly required in funder data-management requirements. There's an administrative fee of EUR 3,000 (waivers available for LMIC repositories).",
    whyItFits:
      "You said you're evaluating whether your repository is trustworthy as a place to deposit data. CoreTrustSeal asks 'is this repository a trustworthy place to deposit data?' — which is complementary to FAIR assessment asking 'are the datasets in this repository FAIR?' An institution should be able to answer yes to both.",
    howToUse:
      "Go to coretrustseal.org/apply. Create an account in the Application Management Tool (AMT). The application is a structured self-assessment against the CoreTrustSeal Requirements, followed by external review. The process takes several months. Training resources are available at coretrustseal.org/why-certification/training.",
    whatsNext:
      "CoreTrustSeal certification is about the repository, not individual datasets. Once your repository is certified, run F-UJI periodically against a sample of your holdings to check dataset-level FAIRness, and use our 12-question tool with research groups depositing data to improve their deposit quality.",
    externalUrl: "https://www.coretrustseal.org/apply/",
    externalLabel: "Go to CoreTrustSeal",
    newbie:
      "If you're a single research group, this is probably not for you yet — CoreTrustSeal is for repositories, not individual datasets. But if you're depositing data somewhere, check whether that repository has CoreTrustSeal certification. If it does, that's a good sign your data is in a trustworthy home.",
    experienced:
      "If you're running an institutional repository, CoreTrustSeal is worth pursuing — it's increasingly required by funders. The LMIC waiver (for repositories in low and middle income countries) is worth knowing about if budget is a barrier. The application is substantial but the requirements document is clear and the reviewer community is supportive.",
  },
};

type Choice = {
  label: string;
  next?: string;
  destination?: DestinationId;
};

type Question = {
  id: string;
  prompt: string;
  help?: string;
  choices: Choice[];
};

// One fixed, short sequence — not an extensible engine (issue #18 scope).
// Max 5 questions on any path.
const QUESTIONS: Record<string, Question> = {
  q1: {
    id: "q1",
    prompt: "Are you working with datasets, or with ontologies and semantic artefacts?",
    help:
      "Datasets are collections of data (spreadsheet rows, sensor readings, clinical records). Ontologies and semantic artefacts are structured vocabularies that define concepts and relationships — a formal data dictionary with terms and their meanings.",
    choices: [
      { label: "Datasets", next: "q2" },
      { label: "Ontologies or semantic artefacts", destination: "ontology-tools" },
    ],
  },
  q2: {
    id: "q2",
    prompt: "How familiar are you with the FAIR principles?",
    help:
      "FAIR stands for Findable, Accessible, Interoperable, Reusable. If you've never heard of these or only vaguely know the term, that's fine — there's a tool for learning the basics first.",
    choices: [
      { label: "I'm new to FAIR or still learning", destination: "fair-aware" },
      { label: "I know the principles — let's assess my data", next: "q3" },
    ],
  },
  q3: {
    id: "q3",
    prompt: "Is your dataset already published somewhere with a public web page?",
    help:
      "For example on Zenodo, a university repository, Figshare, or any other site where someone could find it via a URL. Not just on your own computer or a shared drive.",
    choices: [
      { label: "Yes, it's already online", next: "q4" },
      { label: "No, not yet (or not sure)", next: "q5" },
    ],
  },
  q4: {
    id: "q4",
    prompt: "Do you want to double-check whether a computer can automatically read its metadata?",
    help:
      "This is about the machine-readable wrapping — can a program find your dataset's ID, read its metadata format, see its license. Not about the data practices themselves. Automated tools can check this in seconds.",
    choices: [
      { label: "Yes, check the machine-readable side", destination: "f-uji" },
      { label: "No, I'm set on that — I want to check my practices", next: "q5" },
    ],
  },
  q5: {
    id: "q5",
    prompt: "Are you looking at your own group's data, or coordinating data across multiple sites?",
    help:
      "A single research group figuring out their own practices is a different problem from making data line up across organizations. The tools and approach are different.",
    choices: [
      { label: "Just my own group's data", next: "q6" },
      { label: "Multiple sites or organizations", destination: "level-2" },
    ],
  },
  q6: {
    id: "q6",
    prompt: "Do you already know which specific FAIR topic you need help with?",
    help:
      "For example 'I need to write a data dictionary' or 'I need to set up persistent identifiers.' Or are you still figuring out where you stand across the board?",
    choices: [
      { label: "I know the topic — take me to a recipe", destination: "cookbook" },
      { label: "I'm figuring out where I stand", destination: "this-tool" },
    ],
  },
};

export function Navigator() {
  const [currentId, setCurrentId] = useState<string>("q1");
  const [destination, setDestination] = useState<DestinationId | null>(null);
  const [path, setPath] = useState<string[]>([]);

  function choose(choice: Choice) {
    if (choice.destination) {
      setDestination(choice.destination);
    } else if (choice.next) {
      setPath((p) => [...p, currentId]);
      setCurrentId(choice.next);
    }
  }

  function restart() {
    setCurrentId("q1");
    setDestination(null);
    setPath([]);
  }

  function back() {
    if (path.length === 0) return;
    const prev = path[path.length - 1];
    setPath((p) => p.slice(0, -1));
    setCurrentId(prev);
    setDestination(null);
  }

  if (destination) {
    const dest = DESTINATIONS[destination];
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="space-y-6 pt-6">
            <div className="space-y-1">
              <p className="text-sm font-semibold tracking-wide text-primary uppercase">
                Your recommendation
              </p>
              <h3 className="font-heading text-2xl font-semibold text-balance">{dest.name}</h3>
              <p className="text-base text-muted-foreground">{dest.tagline}</p>
            </div>

            <div className="space-y-4">
              <div>
                <p className="font-heading text-sm font-semibold uppercase tracking-wide text-primary">
                  What it does
                </p>
                <p className="mt-1 text-base leading-relaxed">{dest.whatItDoes}</p>
              </div>

              <div>
                <p className="font-heading text-sm font-semibold uppercase tracking-wide text-primary">
                  Why it fits your situation
                </p>
                <p className="mt-1 text-base leading-relaxed">{dest.whyItFits}</p>
              </div>

              <div>
                <p className="font-heading text-sm font-semibold uppercase tracking-wide text-primary">
                  How to use it
                </p>
                <p className="mt-1 text-base leading-relaxed">{dest.howToUse}</p>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="rounded-md border bg-muted/30 p-4">
                  <p className="font-heading text-sm font-semibold text-foreground">
                    If you&rsquo;re new to this
                  </p>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{dest.newbie}</p>
                </div>
                <div className="rounded-md border bg-muted/30 p-4">
                  <p className="font-heading text-sm font-semibold text-foreground">
                    If you&rsquo;ve done this before
                  </p>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                    {dest.experienced}
                  </p>
                </div>
              </div>

              <div>
                <p className="font-heading text-sm font-semibold uppercase tracking-wide text-primary">
                  What to do after
                </p>
                <p className="mt-1 text-base leading-relaxed">{dest.whatsNext}</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 pt-2">
              {dest.externalUrl && (
                <a
                  href={dest.externalUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(buttonVariants())}
                >
                  {dest.externalLabel ?? "Visit tool"} &rarr;
                </a>
              )}
              {dest.externalUrl2 && (
                <a
                  href={dest.externalUrl2}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(buttonVariants({ variant: "outline" }))}
                >
                  {dest.externalLabel2 ?? "Visit tool"} &rarr;
                </a>
              )}
              {dest.internalHref && (
                <Link href={dest.internalHref} className={cn(buttonVariants())}>
                  {dest.internalLabel ?? "Go"}
                </Link>
              )}
              <Button variant="outline" onClick={restart}>
                Start over
              </Button>
            </div>
          </CardContent>
        </Card>
        <p className="text-sm text-muted-foreground">
          Want to see the full landscape these tools sit in?{" "}
          <Link href="/about" className="underline underline-offset-4 hover:text-foreground">
            Read the About page
          </Link>
          .
        </p>
      </div>
    );
  }

  const q = QUESTIONS[currentId];
  const stepNum = path.length + 1;

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="space-y-5 pt-6">
          <div className="flex items-center gap-2">
            <span className="inline-flex size-6 items-center justify-center rounded-full bg-primary/10 font-heading text-sm font-semibold text-primary">
              {stepNum}
            </span>
            <span className="text-sm text-muted-foreground">Question {stepNum}</span>
          </div>
          <h3 className="font-heading text-xl font-semibold text-balance">{q.prompt}</h3>
          {q.help && <p className="text-sm leading-relaxed text-muted-foreground">{q.help}</p>}
          <div className="flex flex-col gap-3 pt-1">
            {q.choices.map((choice) => (
              <Button
                key={choice.label}
                variant="outline"
                size="lg"
                className="justify-start text-left"
                onClick={() => choose(choice)}
              >
                {choice.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
      <div className="flex items-center justify-between">
        {path.length > 0 ? (
          <Button variant="ghost" size="sm" onClick={back}>
            Back
          </Button>
        ) : (
          <span />
        )}
        <p className="text-xs text-muted-foreground">
          {path.length + 1} of {Object.keys(QUESTIONS).length}
        </p>
      </div>
    </div>
  );
}
