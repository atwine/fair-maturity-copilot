<div align="center">
  <img src="assets/logo.svg" alt="" width="72" height="72">
  <h1>fair-maturity-copilot</h1>
</div>

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![Postgres (Neon)](https://img.shields.io/badge/Postgres-Neon-00E599?logo=postgresql&logoColor=white)
![Status](https://img.shields.io/badge/status-v0%20in%20progress-yellow)
![License](https://img.shields.io/badge/license-unreleased-lightgrey)

</div>

A guided, plain-language FAIR data-maturity assessment tool for research organizations that don't have a data librarian on staff.

## Status

**In progress, feature-complete for v0 — merged to `main`. Backend (engine, FAIR adapter content, remediation prompt, FAIRification plan synthesis, REST API, over-the-shoulder mentor) and frontend (assessment wizard, review, report, plan, mentor chat, and about pages) are both built and tested, including live end-to-end runs in a real browser against vLLM. Not yet deployed anywhere or piloted with a real ACE user — see [`ROADMAP.md`](ROADMAP.md) for what's left (an eval harness, deployment, the actual pilot) and [`devlog/HANDOFF.md`](devlog/HANDOFF.md) for the running session log.

## The problem

The Research Data Alliance's FAIR Data Maturity Model defines 41 indicators for assessing how Findable, Accessible, Interoperable, and Reusable a dataset or research practice is. The existing automated checkers — [F-UJI](https://www.f-uji.net) and [FAIR Checker](https://fair-checker.france-bioinformatique.fr) — cover the machine-readable half of that (can a crawler resolve your metadata), and only ever talk to a computer, never a person; their output is written for data engineers, not for a research group lead trying to figure out what to actually fix. The two richer resources in this space — the [FAIR Cookbook](https://faircookbook.elixir-europe.org) (60+ detailed recipes) and [FAIR-DSM](https://fairplus.github.io/Data-Maturity/) (a 5-level enterprise maturity roadmap) — assume the reader already knows which part applies to them, or has real institutional infrastructure to build on.

This tool is a guided version, for the gap none of those fill: walk a non-technical stakeholder through a 12-indicator subset of the RDA model in plain language, score it, use an LLM to turn every weak indicator into a specific actionable next step, and synthesize the whole set of gaps into one ordered FAIRification plan. See [`docs/WHY-THIS-TOOL.md`](docs/WHY-THIS-TOOL.md) (also live in-app at `/about`) for the full writeup of how this fits alongside the rest of the FAIR-tooling landscape.

For a single self-contained document covering the project's origin story, value proposition, current state, and open questions — written for brainstorming with a fresh collaborator (human or AI) rather than for implementation — see [`docs/BRAINSTORMING-BRIEF.md`](docs/BRAINSTORMING-BRIEF.md).

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
- **LLM**: any OpenAI-compatible provider — see [LLM provider](#llm-provider) below, this is a required setup step, not optional.

## LLM provider

**This tool needs a real LLM to function** — it's what turns each answer into plain-language feedback, synthesizes the FAIRification plan, and powers the mentor chat. Without one configured, the assessment wizard works but the report, plan, and mentor screens will fail. There's no default that "just works" out of the box for a new clone of this repo, so pick one:

| Option | Cost | Setup | Good for |
|---|---|---|---|
| **[OpenRouter](https://openrouter.ai/keys)** (recommended default) | Pay-per-token, some free models | Sign up, copy an API key | Getting running in a minute, no hardware needed. Its ["auto router"](https://openrouter.ai/openrouter/auto) picks a good model per request for you — set `LLM_MODEL=openrouter/auto` instead of naming one |
| **[Ollama](https://ollama.com)** | Free | Install locally, `ollama pull llama3.1:8b` | Trying this out at zero cost, or fully offline work — nothing leaves your machine |
| **vLLM** | Your own GPU infra | Self-hosted | Teams with real GPU hardware who want to run their own model at scale — this is how ACE runs its own pilot, not something a casual clone of this repo needs |
| **Anything else OpenAI-compatible** | Varies | Provider-specific | Together AI, Groq, Azure OpenAI, the OpenAI API itself, or any other provider that speaks the same `/chat/completions` shape |

All of these are configured the exact same way — three values in `backend/.env` (`LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`), never a code change. See `backend/.env.example` for a ready-to-uncomment block for each option above.

**Why a publicly hosted provider is a reasonable default here, not just a self-hosted one:** this tool never sends a dataset itself to the LLM — only the plain-language answers and free-text notes a person types into the assessment wizard. There's no file upload, no raw data, nothing sensitive by default leaving your machine beyond what you type into the form fields.

## Getting started (backend)

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"   # Windows; drop the .exe path prefix on macOS/Linux
cp .env.example .env   # then fill in DATABASE_URL and an LLM provider block -- see "LLM provider" above
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
| GET | `/assessments/{id}/plan` | Synthesize an ordered FAIRification plan from all of a run's open findings — generated once and cached like the report, until a revisited answer marks it stale |
| POST | `/assessments/{id}/mentor/step/{step_id}/start` | Start a mentor conversation for one plan step (which can bundle several indicators, all covered in one chat), with a skill-level toggle: "new to this" / "done this before"; generates an opening greeting |
| GET | `/assessments/{id}/mentor/step/{step_id}` | Fetch an existing mentor conversation's message history |
| POST | `/assessments/{id}/mentor/step/{step_id}/messages` | Send a user message to the mentor and get a reply; if the message describes a completed fix for one of the step's indicators, the mentor updates that answer via the existing rescore path |

Answers can also be edited after an assessment is completed (`PUT /assessments/{id}/answers/{indicator_id}`) — this is how "revisiting" a finding from the report works: it re-scores that one indicator, regenerates its remediation, and refreshes the report's cached score.

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
    adapters/fair/      — FAIR-specific indicators.yaml, adapter, scoring rubric, remediation + plan + mentor prompts
    api/                — REST routes + schemas (see "API surface" above)
  fixtures/             — synthetic demo dataset profiles (no real ACE/TASO data touches an LLM)
  scripts/               — seed_indicators.py, run_demo_assessment.py
  tests/                 — engine boundary, FAIR adapter, remediation/plan grounding, fixture checks
  .env.example          — required env vars, including both LLM provider presets
frontend/
  app/                   — new, question/[indicatorId] (also used to revisit a finding), review, report, plan, mentor/[stepId], about
  lib/                   — api-client.ts + types.ts, mirroring the backend's REST contract
docs/
  PLANNING_PROMPT.md    — the Plan Mode prompt that produced the v0 build plan
  DECISIONS.md          — why this project, and not the nine other ideas we scoped first
  WHY-THIS-TOOL.md      — plain-language explainer: who this is for, and how it fits the wider FAIR-tooling landscape
  demo_reports/          — generated output from scripts/run_demo_assessment.py — what the tool actually produces
  fairification-framework-Africa/ — reference material this tool's design was checked against (see DECISIONS.md v16-v18)
  background/           — the earlier idea-scoping reports (v1-v3)
devlog/
  HANDOFF.md            — running session log, written so any agent (Claude, Devin) can resume cold
assets/
  logo.svg              — the brand mark (README); kept in sync by hand with frontend/app/icon.svg and components/logo-mark.tsx
ROADMAP.md              — what's built, what's next, what's tracked-but-parked
CHANGELOG.md            — dated record of what shipped
```

## License

Not yet decided. Repo is **private** for now — may open-source later once v0 is working.
