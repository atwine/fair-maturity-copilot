# fair-maturity-copilot

A guided, plain-language FAIR data-maturity assessment tool for research organizations that don't have a data librarian on staff.

## Status

**In progress.** The backend engine is scaffolded and tested, and the FAIR adapter's content (12 indicators, scoring, seed script) is built and tested. Synthetic demo data, the remediation-writer prompt, the REST API, and the Next.js frontend are next. See [`ROADMAP.md`](ROADMAP.md) for current checkpoint status and [`devlog/HANDOFF.md`](devlog/HANDOFF.md) for the running session log.

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
./.venv/Scripts/python.exe -m pytest tests/ -v
./.venv/Scripts/python.exe scripts/seed_indicators.py   # loads the 12 FAIR indicators into the DB
```

Most tests (`tests/engine/`, `tests/adapters/fair/`) need no database or LLM connection — they're the fastest way to confirm the setup works. `seed_indicators.py` does need a real `DATABASE_URL` (Postgres via Neon, or a local SQLite URL like `sqlite:///./dev.db` for quick local testing).

## Branching convention

Three long-lived branches, promotion in one direction only:

```
feature/<name>  →  development  →  staging  →  main
 (isolated)          (integration)   (pre-prod)   (production)
```

- **All new work** happens on a `feature/<short-name>` branch, cut from `development`. Never commit directly to `development`, `staging`, or `main`.
- **Feature → `development`**: gets a code-review pass on the diff first. Pushing the resulting `development` update to GitHub is never automatic — always confirmed before it happens, not reported after.
- **`development` → `staging`**: same discipline — review, then confirm before pushing.
- **`staging` → `main`**: only via a pull request, never a direct push. A second, independent review (Open Code Review delegate mode) runs on that PR before it goes up. Merging the PR requires explicit go-ahead — an open PR is not itself permission to merge.
- `main` is production. It should only ever change via a reviewed, approved PR from `staging`.

**One documented exception:** the first backend scaffold (engine + boundary test) was merged directly into `main` before this three-tier structure was set up, with explicit one-time approval to leave it as-is rather than rewrite already-pushed history. Every commit from that point forward follows the structure above. See `docs/DECISIONS.md` and `devlog/HANDOFF.md` for the full account.

## Repo layout

```
backend/
  app/
    engine/            — standard-agnostic core (models, scoring, remediation, LLM client)
    adapters/fair/      — FAIR-specific indicators.yaml, adapter, scoring rubric (populated; prompts/ next)
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
