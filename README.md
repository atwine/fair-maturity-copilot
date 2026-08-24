# fair-maturity-copilot

A guided, plain-language FAIR data-maturity assessment tool for research organizations that don't have a data librarian on staff.

## Status

**In progress.** The backend engine is scaffolded and its core boundary is tested; the FAIR-specific content (indicators, prompts, API routes) and the Next.js frontend are next. See [`ROADMAP.md`](ROADMAP.md) for current checkpoint status and [`devlog/HANDOFF.md`](devlog/HANDOFF.md) for the running session log.

## The problem

The Research Data Alliance's FAIR Data Maturity Model defines 41 indicators for assessing how Findable, Accessible, Interoperable, and Reusable a dataset or research practice is. The one existing automated checker, [F-UJI](https://www.f-uji.net), covers 16 of the 41 — and its output is written for data engineers, not for a research group lead trying to figure out what to actually fix.

This tool is a guided version: walk a non-technical stakeholder through the assessment in plain language, score it, and use an LLM to turn every weak indicator into a specific, actionable next step.

## Architecture

Built as a reusable **engine + adapter** pattern, not a one-off script:

```
intake (structured findings) → scoring → LLM remediation writer → plain-language report
```

The FAIR indicator set and scoring rubric live in their own adapter module (`backend/app/adapters/fair/`). Nothing in `backend/app/engine/` may reference "FAIR" by name — that boundary is what lets a second adapter, applying the same engine to OHDSI's OMOP CDM Data Quality Dashboard output, plug in later without a rewrite. See [`ROADMAP.md`](ROADMAP.md).

## Why this exists

Built by [ACE](https://ace.ac.ug) (Africa Center of Excellence in Bioinformatics & Data Science, Kampala, Uganda) — first pilot user is ACE itself, self-assessing its own data governance practices.

## Tech stack

- **Backend**: FastAPI + SQLModel + Alembic, Postgres (Neon)
- **Frontend**: Next.js + React + TypeScript + Tailwind + shadcn/ui (not yet scaffolded)
- **LLM**: OpenAI-compatible client against two on-prem endpoints — local Ollama for dev iteration, a vLLM-hosted Llama 3.3 70B (AWQ INT4) for pilot-facing generations. Provider is a config swap (`backend/.env`), never a code change.

## Getting started (backend)

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"   # Windows; drop the .exe path prefix on macOS/Linux
cp .env.example .env   # then fill in DATABASE_URL (see the file for a free Neon setup)
./.venv/Scripts/python.exe -m pytest tests/engine -v
```

The engine boundary test (`tests/engine/test_boundary.py`) runs against a fake adapter and needs no database or LLM connection — it's the fastest way to confirm the setup works.

## Branching convention

`main` is the stable branch. All work happens on a feature branch (`feature/<short-name>`), gets a self-review pass before merging, and merges into `main` locally. **Nothing is ever pushed to the GitHub remote without asking first** — an approved local merge is not the same as permission to push. See the user's global Claude Code conventions for the full policy this follows.

## Repo layout

```
backend/
  app/
    engine/            — standard-agnostic core (models, scoring, remediation, LLM client)
    adapters/fair/      — FAIR-specific indicators/prompts (content, not yet populated)
    api/                — REST routes (not yet built)
  tests/engine/         — proves the engine/adapter boundary against a fake adapter
  .env.example          — required env vars, including both LLM provider presets
docs/
  PLANNING_PROMPT.md    — the Plan Mode prompt that produced the v0 build plan
  DECISIONS.md          — why this project, and not the nine other ideas we scoped first
  background/           — the earlier idea-scoping reports (v1-v3)
devlog/
  HANDOFF.md            — running session log, written so any agent (Claude, Devin) can resume cold
ROADMAP.md              — what's built, what's next, what's tracked-but-parked
CHANGELOG.md            — dated record of what shipped
```

## License

Not yet decided. Repo is **private** for now — may open-source later once v0 is working.
