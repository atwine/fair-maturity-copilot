# fair-maturity-copilot — brainstorming brief

**Purpose of this document:** everything a fresh collaborator (human or AI) needs to
think productively about this project *without implementing anything* — where it
came from, why it exists, what it actually does today, and the open questions
worth pressure-testing. Written to be handed to a different AI (or a colleague)
cold, as a self-contained starting point for research and brainstorming, separate
from the actual implementation work happening in this repo. If you're reading
this to *build* something, read [`README.md`](../README.md) and
[`docs/PLANNING_PROMPT.md`](PLANNING_PROMPT.md) instead — this file is for
thinking, not coding.

---

## 1. The elevator pitch

A research group lead at an African/LMIC institution — someone responsible for
their team's data, but with no data librarian or FAIR consultant on staff — answers
12 plain-language questions about their own data practices. They get a score, a
plain-language report on what's working and what isn't, one ordered plan for
fixing the gaps, and (new, proof-of-concept) an over-the-shoulder AI mentor that
coaches them through each step of that plan in a real conversation. No jargon
assumed anywhere. Built for ACE Uganda (the Africa Center of Excellence in
Bioinformatics & Data Science), as its first real pilot user.

The bet underneath it: the hard problem in FAIR data compliance isn't that good
tools don't exist — it's that **six different tools and reference documents each
cover a slice of the problem, assume different starting knowledge, and nothing
tells a newcomer which one (if any) applies to them.** That fragmentation *is* the
problem. The product is one guided path through it, not a seventh reference to add
to the pile.

---

## 2. Where this came from — the origin story

This wasn't the first idea. It emerged from a structured narrowing process, fully
preserved in [`docs/background/`](background/) (three standalone HTML documents —
open them directly in a browser for the original presentation with sourcing).

**v1 — ten ideas, broad survey.** Ten distinct AI-for-African-research-institutions
concepts were scoped, each with sourcing and a rough build plan:
1. AMR (antimicrobial resistance) prediction from whole-genome sequencing, with a plain-language clinician report
2. A clinical/health-domain Luganda translation benchmark and fine-tune
3. A federated / privacy-preserving toolkit for African genomic data sharing
4. An LLM-assisted grant and manuscript-writing copilot for African researchers
5. An AI data-quality and anomaly-detection layer for DHIS2 / OpenHIE
6. A narrowly-scoped CHW (community health worker) decision-support tool for non-communicable disease screening
7. A Luganda voice interface over crop-disease detection, linked to market prices
8. A local-first pathogen genomics surveillance dashboard for East Africa
9. Luganda evaluation splits for existing African-NLP benchmarks
10. A reproducibility and provenance tool for African bioinformatics pipelines

**v2 — narrowed to four**, refined against what the team could *actually* build
soon (existing compute, existing data-in-hand, real institutional need):
1. Health-domain Luganda translation, released as an open benchmark + fine-tuned model
2. A grant and manuscript-writing copilot, built for African funder formats
3. A guided FAIR data maturity assessment and remediation tool
4. An anomaly-detection layer for health facility reporting data (DHIS2)

**v3 — the actual decision.** Two of the four turned out to be *the same
underlying engine* aimed at two different technical standards: idea #3 (FAIR
maturity) and a newly-identified idea #4 (a plain-language translator for OHDSI's
OMOP CDM Data Quality Dashboard output). Both take a dense, expert-built technical
framework and a non-technical stakeholder who's supposed to act on it but can't
parse the raw output — and both need the same core: **structured findings in →
severity scoring → LLM remediation writer → plain-language report out.**

The FAIR maturity tool was chosen to **build first** because it's fully
self-contained (a questionnaire — no external data dependency, no waiting on a
partner organization's data access). The OMOP translator was sequenced to **build
second**, once the same core engine already exists and once TASO (The AIDS Support
Organisation, Uganda)'s OMOP CDM data access and ETL path are actually resolved —
it's parked, not abandoned (see `ROADMAP.md`'s "v1 — OMOP CDM data-quality
adapter" section).

**What got dropped, and why — worth knowing before you propose reviving them:**
- **The grant-writing copilot (v2 idea #2)** — dropped for **adoption risk**. Not
  a technical concern; a bet that people wouldn't actually change their grant-
  writing workflow to use it.
- **Luganda health-domain translation (v1 idea #2 / v2 idea #1)** — not dropped,
  **parked**. Still described as "the strongest idea on paper" (existing models,
  an existing evaluation set, a live fine-tuning plan, a team with a track record
  in exactly this area) — but the team was mid-way through finalizing ~10,000
  curated translation pairs, with only ~1,000 through third-party evaluation at
  the time. Explicitly a "revisit once that evaluation lands" item, architecturally
  unrelated to this engine, and would live in its own repo if it restarts.
- **DHIS2 anomaly detection (v2 idea #4)** — implicitly superseded by the OMOP
  direction (v3's idea #4) rather than separately pursued; the "translate a dense
  automated technical report into plain language for non-technical health-data
  staff" need was judged better served by pointing the same engine at OHDSI's
  Data Quality Dashboard, which already runs 3,300+ automated checks against an
  OMOP CDM database, rather than building new DHIS2-specific anomaly detection.

**Why this matters for brainstorming:** the "one engine, many standards" framing
was the whole point from before a line of code was written. If a brainstorming
session surfaces "what if this also covered X" (a different maturity model, a
different compliance framework, a different technical report format), the right
question isn't "should we build a new tool" — it's "does X fit the same
`structured findings → severity scoring → LLM remediation writer → plain-language
report` shape this engine already implements?" If yes, it's a new *adapter*, not a
new *product*. See §5.

---

## 3. The problem, precisely

**Who:** a research group lead at an institution like ACE Uganda — responsible for
their team's data, but never trained in data stewardship, with no data librarian
or FAIR consultant available. Funders, collaborators, and good scientific practice
increasingly expect research data to be **FAIR** (Findable, Accessible,
Interoperable, Reusable), but nobody has given this person a way to find out,
in plain language, whether their actual practices are okay — or what to do if
they're not.

**What FAIR means, compressed:** can someone find out your dataset exists
(Findable)? Once found, is it clear how to get it (Accessible)? Is it in a format
other tools can actually read (Interoperable)? Is there enough context — column
meanings, who collected it, what license applies — for someone else to use it
correctly (Reusable)? The Research Data Alliance (RDA)'s FAIR Data Maturity Model
defines 41 specific indicators across those four questions. This tool asks 12 of
them — the ones a non-technical research lead can actually answer about their own
practices without a data science background — deliberately, not as a simplified
or invented subset.

**The actual competitive landscape** (full writeup: [`docs/WHY-THIS-TOOL.md`](WHY-THIS-TOOL.md),
also live in-app at `/about`):

| Tool | What it actually is | Why it doesn't solve this |
|---|---|---|
| **RDA FAIR Data Maturity Model** | The 41-indicator standard itself | Just a yardstick — nothing walks you through it |
| **F-UJI** | Automated crawler, checks 16 of 41 indicators | Machine-readable metadata only; never talks to a human; output written for data engineers |
| **FAIR Checker** | Same category as F-UJI, different implementation | Same limitation — checks the wrapping, not what's inside |
| **FAIR-DSM** | 5-level institutional maturity roadmap | Built for large institutions with real IT infrastructure (semantic databases, master data governance) — not a single research group |
| **The FAIR Cookbook** | 60+ detailed "recipes" (reference library) | Useful only once you already know which recipe you need |
| **ELIXIR's FAIRification framework** | An actual *process* (get data → model domain → identifiers → standards → vocabularies → interoperability → host → share) | The one piece of the landscape that isn't a checklist — and the one thing none of the other five actually execute *for* you |

**The synthesized value proposition:** none of the six, alone, solves the actual
problem — the automated checkers can't talk to a human, the reference resources
assume you already know what applies to you. That fragmentation (six different
things to learn before you've even started fixing your data) is itself the
barrier that makes people give up. This tool is **one guided path**: a 12-question
plain-language assessment (each question with a worked example, so nobody needs
to already know a term to answer about it), a plain-language report, and a single
ordered remediation plan generated from your own actual gaps — following the same
sequencing ELIXIR's framework describes (identifiers → documentation → standards
→ hosting → sharing), but generated specifically for you rather than requiring you
to map your own gaps onto their framework yourself.

**Anticipated pushback, already answered once** (see `WHY-THIS-TOOL.md` for the
full versions — useful to have on hand for a colleague demo):
- *"Isn't this just reinventing F-UJI/FAIR Checker?"* No — those check whether a
  computer can read your published metadata; this checks your actual practices
  (do you have a license stated, a data dictionary, a documented access process)
  — the human side those tools structurally can't see.
- *"Why not just point people at the FAIR Cookbook?"* Because using it well
  requires already knowing what you're looking for — which is exactly the
  knowledge gap this tool exists to close.
- *"Did you pick an easy/invented standard?"* No — the same 41-indicator RDA model
  referenced by F-UJI, FAIR-DSM, and eLwazi's own guidance to researchers. A
  deliberately chosen 12-indicator subset, not a simplified one.
- *"Does this replace FAIR-DSM?"* No — FAIR-DSM is for an institution building
  shared infrastructure across many datasets; this is for a single research group
  figuring out where they stand today.

---

## 4. What's actually built and working today

**Status as of this writing: v0 feature-complete, merged to `main`, not yet
deployed or piloted with a real (non-developer) user.** Everything below has been
built, tested (including live end-to-end runs against a real LLM, not mocked),
and self-reviewed — but "works in development" and "survived a real pilot user"
are different claims, and only the first one is true yet.

**The core flow, live end to end:**
1. **Guided assessment** — a 4-screen wizard (new assessment → 12 questions, one
   at a time, each with a worked example → review → report), plain-language
   throughout, no jargon assumed.
2. **Scoring + report** — every one of the 12 indicators gets real LLM-generated
   content, not just the failing ones: gaps get a `SUMMARY` + numbered `STEPS`,
   passing indicators get a short "why this is fine" explanation. Generated once
   per assessment run and cached (not re-generated on every page view).
3. **FAIRification plan** — all open findings synthesized into a single ordered
   plan (3-6 steps, following the natural identifiers → documentation → standards
   → hosting → sharing sequence), each step naming exactly which findings it
   addresses. Generated once and saved (not redrafted on every visit).
4. **Revisit-and-update** — any answered finding can be reopened, re-answered, and
   re-scored on its own (one LLM call, not a full 12-call re-run), with the
   report's cached score refreshed in place.
5. **Over-the-shoulder mentor (proof-of-concept, the most ambitious piece built so
   far)** — a real chat conversation, scoped to one plan step (which can bundle
   several related indicators), grounded in this tool's own synthesis of the FAIR
   landscape (not RAG, not external verification — a deliberate POC-scoping
   choice, see §6). The mentor can act: if a user describes having completed a
   real fix, the conversation itself updates the answer and triggers a re-score,
   live, without leaving the chat. Supports full markdown formatting (as of the
   most recent work) so it can use a numbered list or a code span when that
   genuinely clarifies something, not just bold/italics.
6. **`/about` page** — a plain-language explainer of what FAIR means and how this
   tool fits into the wider landscape (the content in §3 above), reachable from
   every screen.

**Under the hood, worth knowing for scope conversations:**
- **Standard-agnostic engine + adapter pattern** — the core pipeline (intake →
  scoring → LLM remediation writer → report) has zero FAIR-specific logic in it.
  All FAIR content (the 12 indicators, their scoring rubric, prompt templates)
  lives in one adapter module. This is the load-bearing architectural decision
  for §5 below.
- **LLM-provider-agnostic by design** — the LLM client is a plain OpenAI-compatible
  wrapper; switching between OpenRouter, Ollama, vLLM, or any other
  OpenAI-compatible endpoint is three environment variables, never a code change.
  Currently defaults to OpenRouter (tested, comparable-or-faster than the team's
  own vLLM box, and free-tier friendly for anyone trying this out without
  ACE-internal infrastructure).
- **No user data ever reaches the LLM** — only the plain-language answers and
  free-text notes a person types into the assessment. No file upload, no raw
  dataset content leaves anyone's machine. This is *why* a publicly hosted LLM
  provider is a reasonable default at all, and is worth having ready as an answer
  if data governance comes up in a colleague demo.
- **Real Postgres (Neon)** in place of the original SQLite-only setup, with a
  proper `development → staging → main` branching and review discipline (every
  promotion self-reviewed, code-reviewed, and independently re-reviewed before
  merge).

**Explicitly not yet done — don't let a brainstorm assume these exist:**
- **Not deployed anywhere.** Everything above runs locally. Checkpoint 7 (deploy
  to Railway) is the next infrastructure step, entirely separate from feature work.
- **No real pilot user yet.** ACE self-assessing its own data practices is the
  planned first pilot (Checkpoint 8) — hasn't happened.
- **No formal eval harness** (Checkpoint 6) — LLM output quality has been verified
  by direct live testing and manual review each time something changed, not by an
  automated golden-set + LLM-judge pipeline yet.
- **No in-app "bring your own key" settings** — provider choice today is a
  deploy-time `.env` config, not something an end user picks inside the app
  itself (tracked as [issue #12](https://github.com/atwine/fair-maturity-copilot/issues/12),
  deliberately deferred, not rejected).
- **The mentor has no RAG, no external verification, and no adjustable ambition
  level** — a deliberate proof-of-concept scoping choice (see §6), not a
  limitation nobody noticed.

---

## 5. The architecture, and why it matters for "how do we grow this"

The single most important fact for a scope-stretching brainstorm: **this is one
reusable engine, currently pointed at one standard (RDA FAIR).** The pipeline —

```
structured findings in → severity scoring → LLM remediation writer → plain-language report out
```

— has no FAIR-specific code in it. Everything that makes this *the FAIR tool*
specifically (the 12-indicator question set, the scoring rubric, the prompt
templates) lives in one clearly separated adapter module
(`backend/app/adapters/fair/`). A second, already-planned adapter
(`backend/app/adapters/omop/`, not yet started) will point the exact same engine
at OHDSI's OMOP CDM Data Quality Dashboard output — a completely different
technical framework (3,300+ automated data-quality checks against a clinical
database, vs. a 41-indicator human-answered questionnaire), reusing everything
except the input parser and severity mapping.

**This is the honest frame for "should we support other use cases":** the
question isn't whether the *product* should expand — it's whether a candidate use
case fits the same shape (a dense, expert-built technical standard, and a
non-technical stakeholder who's supposed to act on findings against it but can't
parse the raw output). If it fits, it's a new adapter — cheap, because the hard
design work (scoring model, remediation-writer grounding, report structure,
now the mentor coaching layer) is already built and proven. If it doesn't fit that
shape, it's a different product, and should probably be scoped as one, not bolted
onto this repo.

**Known candidate adapters already on the table**, useful as concrete anchors for
a "what else could this become" conversation:
- **OMOP CDM Data Quality Dashboard** (v1, parked, waiting on TASO's data access —
  see §2 and `ROADMAP.md`). The nearest, most-scoped candidate.
- Any other "dense automated technical report, non-technical audience" pairing
  the team encounters — the DHIS2 anomaly-detection idea (v2) was implicitly
  absorbed into this framing rather than built separately; a similar move could
  apply to other reporting standards ACE or partner organizations run into.

---

## 6. Explicit, deliberate scoping choices worth revisiting

Several decisions were made as "build the smaller version now, on purpose" rather
than as oversights. These are the strongest candidates for a "should we go
further now" brainstorm, because the door was left open on purpose:

- **The mentor is grounded in this tool's own synthesis, not RAG.** At the user's
  explicit call: *"I want it as a proof of concept first before I go deeper."*
  RAG (pulling from a live document corpus), external verification (actually
  checking a claimed fix against real infrastructure), and an adjustable
  "ambition level" (FAIR-DSM-style, letting a more sophisticated user ask for
  more than the 12-indicator floor) were all identified as real, considered
  directions and explicitly deferred — tracked in
  [issue #7](https://github.com/atwine/fair-maturity-copilot/issues/7). Of four
  possible mentor shapes considered (a conversational front door replacing the
  wizard entirely, an additive Q&A sidecar, adjustable ambition levels, or a
  coaching layer over the plan), the user chose the most ambitious available at
  POC scope: *"I think D is what would really be worth the effort, we might as
  well go in big."* Worth surfacing directly to colleagues in a demo: this is a
  proof of concept for an idea already validated as worth pursuing further, not
  a finished feature.
- **Provider choice is deploy-time config, not an in-app feature.** Deliberately
  scoped down from "let end users bring their own key at runtime" (a materially
  bigger feature — where does a key live, does it ever touch the backend, what's
  the no-key-yet UX) — filed as issue #12 with the open design questions written
  down, not guessed at.
- **Repository recommendations in remediation text default to naming Zenodo
  alone**, even though real comparative research exists in this repo's own
  history (`docs/DECISIONS.md` v16: a 7-repository comparison — Dataverse, Dryad,
  Figshare, Mendeley Data, OSF, Vivli, Zenodo — with a concrete decision rule
  already worked out) that was never wired into the actual prompt. A small,
  contained, already-researched improvement sitting unused.
- **Cross-assessment history/trends are explicitly out of scope for v0** — progress
  tracking is single-assessment only. Flagged as a real future need ("revisit if
  the ACE pilot asks for it"), not built speculatively ahead of that signal.
- **The OMOP adapter's ETL layer is explicitly out of scope, on purpose** — several
  existing OpenMRS→OMOP tools and a pan-African harmonization platform (INSPIRE
  datahub) already exist; this project starts downstream of an existing OMOP CDM
  database, not by building new ETL infrastructure.

---

## 7. Open questions worth actually brainstorming

These are not yet decided, and are exactly the kind of thing worth taking real
time on before the next implementation session — the point of this document.

**On value proposition and positioning:**
- The strongest current answer to "why this and not X" is fragmentation-solving
  (§3) — is that the pitch that will land best with colleagues, or does it need
  a sharper hook? (e.g., leading with the mentor's live coaching, or with the
  concrete score/plan artifact as something to *show*, not explain.)
- Is "FAIR data maturity" itself the most legible framing for a non-specialist
  colleague audience, or does the demo need a different opening frame (a concrete
  scenario: "here's what happens when a funder asks for your data management
  plan and you don't have one")?
- What's the actual cost of *not* using this today for ACE's target user — is
  there a sharper, more visceral articulation of the status quo pain than "no
  data librarian on staff"?

**On scope and stretch:**
- Which of the "known candidate adapters" (§5) is actually worth scoping next,
  independent of the OMOP/TASO timeline blocker — is there a use case reachable
  without waiting on another organization's data-access decision?
- Does the mentor's proof-of-concept validate strongly enough to justify the next
  increment (RAG, external verification, or adjustable ambition — issue #7),
  or does colleague feedback suggest a different next step entirely?
- Is there a version of this tool aimed at an individual researcher rather than a
  research-group lead — same engine, different entry point/audience — worth
  scoping as a lighter-weight adapter or mode rather than a new standard adapter?

**On go-to-market / demo readiness:**
- What does "ready to demo to colleagues" actually require beyond what's built —
  is a real deployed instance (Checkpoint 7) a hard prerequisite, or can a strong
  local demo carry the conversation?
- What objections is a colleague audience likely to raise that the existing
  anticipated-questions list (§3) doesn't cover?
- Given no real pilot has happened yet (Checkpoint 8), how much weight should
  colleague feedback at this stage carry versus waiting for ACE's own first
  real self-assessment run?

**On sustainability/ownership:**
- Given the LLM-provider-agnostic design and the explicit reasoning for defaulting
  to a hosted provider (§4), is there a clear story yet for who pays for LLM usage
  at real pilot scale, and does that change if/when in-app bring-your-own-key
  (issue #12) gets built?
- What license and public/private repo status make sense now that there's a real
  demo-ready v0 — this was explicitly left undecided at the very start
  (`docs/PLANNING_PROMPT.md`) and, as far as this brief's sources show, still is.

---

## 8. Where to go deeper

This brief compresses and synthesizes; it doesn't replace the underlying record.
For anything that needs more precision than this document gives:

- **[`README.md`](../README.md)** — current status, architecture, tech stack, setup instructions.
- **[`docs/WHY-THIS-TOOL.md`](WHY-THIS-TOOL.md)** — the full competitive-landscape writeup (§3 above is a compression of this).
- **[`docs/PLANNING_PROMPT.md`](PLANNING_PROMPT.md)** — the original planning brief that kicked off implementation, including constraints (compute, team size, timeline) not repeated here.
- **[`ROADMAP.md`](../ROADMAP.md)** — full checkpoint-by-checkpoint build history, the backlog, and the "bigger directions to evaluate later" list this brief's §6-7 draw from.
- **[`docs/DECISIONS.md`](DECISIONS.md)** — every real decision point in the project's history (v1 through the present), each with the reasoning behind it — the single deepest source of "why did we do it this way."
- **[`devlog/HANDOFF.md`](../devlog/HANDOFF.md)** — a running session-by-session log, written explicitly so a different agent (Devin, or a fresh Claude session) can resume work with zero prior context.
- **[`docs/background/`](background/)** — the original v1/v2/v3 ideation documents (open as HTML in a browser), full sourcing included.
- **The live `/about` page** (once deployed, or run locally) — the user-facing version of §3.

If a brainstorming session with this brief produces a real decision or a new
direction worth acting on, the natural next step is a new entry in
`docs/DECISIONS.md` (once implementation resumes) — that file is the project's
actual memory, and this brief will go stale the moment real work moves past it.
