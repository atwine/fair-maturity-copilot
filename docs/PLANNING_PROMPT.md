# Planning prompt — paste this into Claude's Plan Mode

You are entering Plan Mode to design the implementation plan for **fair-maturity-copilot**, a tool that walks a research organization through a FAIR (Findable, Accessible, Interoperable, Reusable) data-maturity self-assessment in plain language, then uses an LLM to turn each weak indicator into a specific, actionable remediation step.

## Who this is for

Non-technical stakeholders — research group leads, health-data system managers — at African/LMIC research institutions, starting with ACE (the Africa Center of Excellence in Bioinformatics & Data Science, Kampala, Uganda). They need to assess and improve their data governance/FAIRness but have no realistic path to a data librarian or FAIR consultant.

## Why this, why now

- The Research Data Alliance's FAIR Data Maturity Model defines 41 indicators for assessing FAIRness (source: `datascience.codata.org/articles/10.5334/dsj-2020-041`).
- The one existing automated tool, F-UJI, covers only 16 of the 41 indicators, and its output is written for data engineers, not lab leads.
- Nobody has built a guided, plain-language layer on top of this — something a non-technical person can self-administer and walk away from with a concrete to-do list.

## Architecture requirement: build an engine, not a one-off script

This is the first of two planned applications of the same underlying pattern. A second tool — tracked in `ROADMAP.md`, not being built yet — will apply the identical pipeline to OHDSI's OMOP CDM Data Quality Dashboard output instead of FAIR indicators, once a partner organization's OMOP CDM data is actually ready. Design the core pipeline as a reusable, standard-agnostic engine with a pluggable **adapter** per standard:

1. **Intake** — structured findings in (v0: answers to a guided FAIR questionnaire; future OMOP adapter: the Data Quality Dashboard's JSON/CSV output)
2. **Scoring** — normalize findings onto a common severity/priority scale
3. **Remediation writer** — an LLM turns each weak/failing finding into a specific, plain-language "what's wrong and how to fix it" step
4. **Report** — plain-language output, grouped by priority

The FAIR-specific pieces (the 41-indicator question set, the FAIR scoring rubric) must live in a clearly separated adapter module, not mixed into core engine logic — that boundary is what makes the OMOP adapter cheap to add later.

## Constraints and preferences

- Solo developer (me) plus one MLOps engineer, part-time, aiming for a usable v0 within roughly two weeks.
- Compute available: two A100 80GB GPUs, a working local Llama 3.3 70B deployment, and working English↔Luganda MT models (the MT models aren't needed for this project directly, but the GPU capacity is). Cheap/fast dev iteration matters more than squeezing quality from the largest model — decide whether local Llama 3.3 70B or a smaller/hosted model is the right default for the remediation-writer step during development, and keep the model swappable either way.
- Default stack preference — propose, don't assume: FastAPI backend, Next.js + React + TypeScript + Tailwind + shadcn/ui frontend, Postgres (Neon for early prototyping) if persistence is needed. Push back if a simpler stack (e.g. a single FastAPI app with server-rendered forms, no separate frontend) is actually the better fit for a v0 self-assessment tool used internally by non-technical people first.
- No auth needed for v0 — the first real user is ACE self-assessing its own data practices.
- License and public/private status for the GitHub repo are undecided. Don't block the plan on this, but flag anywhere the choice would materially affect design (e.g. if it affects what indicator-content library can be reused or redistributed).
- Needs to be maintainable by a single developer without deep FAIR/data-governance expertise — favor an explicit, editable indicator/rubric definition (e.g. YAML/JSON config) over hardcoded logic, since the indicator set and scoring will need real-world correction after the first pilot.

## What the plan needs to cover

1. Repo/module structure that enforces the engine/adapter boundary described above.
2. The specific subset of roughly 10-12 RDA FAIR indicators to implement first (out of 41), with rationale for which matter most to a health-data-holding research center, and how the rest are deliberately deferred.
3. A data model for indicators, scores, and findings.
4. The guided questionnaire flow — what a non-technical user actually sees and answers.
5. LLM prompt design for the remediation-writer step, including how to keep it grounded and specific rather than generic filler.
6. A concrete tech-stack decision (confirm or adjust the proposal above, with reasoning).
7. A milestone plan for a working v0 in about two weeks, testable against ACE's own data practices as the first pilot.
8. An approach for evaluating whether the LLM's remediation output is actually good — not hallucinated or generic — before it's ever shown to a real user.
9. Guidance on what belongs in `devlog/HANDOFF.md` and how/when it should be updated, so a different agent (Devin, or a fresh Claude session with no memory of this one) can resume the work with zero prior context if I run out of usage credits mid-build.

Do not write implementation code yet — produce the plan.
