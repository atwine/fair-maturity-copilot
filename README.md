# fair-maturity-copilot

A guided, plain-language FAIR data-maturity assessment tool for research organizations that don't have a data librarian on staff.

## Status

**Planning.** No implementation yet. See [`docs/PLANNING_PROMPT.md`](docs/PLANNING_PROMPT.md) — that prompt is meant to be run through Claude's Plan Mode to produce the actual build plan.

## The problem

The Research Data Alliance's FAIR Data Maturity Model defines 41 indicators for assessing how Findable, Accessible, Interoperable, and Reusable a dataset or research practice is. The one existing automated checker, [F-UJI](https://www.f-uji.net), covers 16 of the 41 — and its output is written for data engineers, not for a research group lead trying to figure out what to actually fix.

This tool is a guided version: walk a non-technical stakeholder through the assessment in plain language, score it, and use an LLM to turn every weak indicator into a specific, actionable next step.

## Architecture

Built as a reusable **engine + adapter** pattern, not a one-off script:

```
intake (structured findings) → scoring → LLM remediation writer → plain-language report
```

The FAIR indicator set and scoring rubric live in their own adapter module. A second adapter — applying the same engine to OHDSI's OMOP CDM Data Quality Dashboard output — is planned as a follow-on project once real OMOP CDM data is available to test against. See [`ROADMAP.md`](ROADMAP.md).

## Why this exists

Built by [ACE](https://ace.ac.ug) (Africa Center of Excellence in Bioinformatics & Data Science, Kampala, Uganda) — first pilot user is ACE itself, self-assessing its own data governance practices.

## Repo layout

```
docs/
  PLANNING_PROMPT.md   — the Plan Mode prompt that produced (or will produce) the build plan
  DECISIONS.md         — why this project, and not the nine other ideas we scoped first
  background/          — the earlier idea-scoping reports (v1-v3)
devlog/
  HANDOFF.md           — running context log, written so any agent (Claude, Devin) can resume cold
ROADMAP.md             — what's built, what's next, what's tracked-but-parked
```

## License

Not yet decided — public/private status and license are open questions, to be settled once the v0 plan exists.
