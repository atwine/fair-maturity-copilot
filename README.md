# fair-maturity-copilot

A guided, plain-language FAIR data-maturity assessment tool for research organizations that don't have a data librarian on staff.

## Status

**In progress, feature-complete for v0.** Backend (engine, FAIR adapter content, remediation prompt, REST API) and frontend (the full 4-screen wizard) are both built and tested, including a live end-to-end run in a real browser against vLLM. Not yet deployed anywhere or piloted with a real ACE user — see [`ROADMAP.md`](ROADMAP.md) for what's left (an eval harness, deployment, the actual pilot) and [`devlog/HANDOFF.md`](devlog/HANDOFF.md) for the running session log.

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
- **Frontend**: Next.js 16 + React 19 + TypeScript + Tailwind v4 + shadcn/ui (built on Base UI, not Radix — its polymorphic components use a `render` prop, not `asChild`)
- **LLM**: OpenAI-compatible client against on-prem vLLM (Llama 3.3 70B, AWQ INT4) — the default for both dev and pilot, since it's dedicated A100 infra and the actual production target. Local Ollama is kept as an offline fallback only, not routine dev — it was tried first but is slower in practice on this hardware. Provider is a config swap (`backend/.env`), never a code change.

## Getting started (backend)

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"   # Windows; drop the .exe path prefix on macOS/Linux
cp .env.example .env   # then fill in DATABASE_URL (see the file for a free Neon setup)
./.venv/Scripts/python.exe -m pytest tests/ -v
./.venv/Scripts/python.exe scripts/seed_indicators.py   # loads the 12 FAIR indicators into the DB
```

Most tests (`tests/engine/`, `tests/adapters/fair/`) need no database or LLM connection — they're the fastest way to confirm the setup works. `tests/api/` needs no external DB either (each test gets its own throwaway SQLite file), but `tests/api/test_report_live.py` does call the real LLM configured in `.env`. `seed_indicators.py` needs a real `DATABASE_URL` (Postgres via Neon, or a local SQLite URL like `sqlite:///./dev.db` for quick local testing) — run it before starting the API, or report generation will fail with a clear error telling you to.

```bash
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload   # http://localhost:8000/docs for interactive API docs
```

### API surface

| Method | Path | What it does |
|---|---|---|
| GET | `/adapters/{adapter_id}/questions` | The ordered question set for an adapter (currently just `fair-v0`) |
| POST | `/assessments` | Start a new assessment run |
| GET | `/assessments/{id}` | Run status + which indicators are answered so far |
| PUT | `/assessments/{id}/answers/{indicator_id}` | Submit or update one answer |
| POST | `/assessments/{id}/complete` | Mark a run complete — fails if any indicator is unanswered |
| GET | `/assessments/{id}/report` | Generate (once) or fetch the cached report — plain-language findings + score |
| POST | `/assessments/{id}/findings/{indicator_id}/regenerate` | Force one finding's remediation to be redone |

## Getting started (frontend)

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000 — needs the backend running at :8000 (see above)
```

Defaults to calling the backend at `http://localhost:8000`; override with `NEXT_PUBLIC_API_BASE_URL` in a `.env.local` (see `.env.local.example`) if it's running elsewhere.

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
    adapters/registry.py — maps adapter_id -> concrete adapter; the only file allowed to know FAIR exists
    adapters/fair/      — FAIR-specific indicators.yaml, adapter, scoring rubric, remediation prompt
    api/                — REST routes + schemas (see "API surface" above)
  fixtures/             — synthetic demo dataset profiles (no real ACE/TASO data touches an LLM)
  scripts/               — seed_indicators.py, run_demo_assessment.py
  tests/                 — engine boundary, FAIR adapter, remediation grounding, fixture checks
  .env.example          — required env vars, including both LLM provider presets
frontend/
  app/                   — the 4-screen wizard (new, question/[indicatorId], review, report)
  lib/                   — api-client.ts + types.ts, mirroring the backend's REST contract
docs/
  PLANNING_PROMPT.md    — the Plan Mode prompt that produced the v0 build plan
  DECISIONS.md          — why this project, and not the nine other ideas we scoped first
  demo_reports/          — generated output from scripts/run_demo_assessment.py — what the tool actually produces
  background/           — the earlier idea-scoping reports (v1-v3)
devlog/
  HANDOFF.md            — running session log, written so any agent (Claude, Devin) can resume cold
ROADMAP.md              — what's built, what's next, what's tracked-but-parked
CHANGELOG.md            — dated record of what shipped
```

## License

Not yet decided. Repo is **private** for now — may open-source later once v0 is working.
