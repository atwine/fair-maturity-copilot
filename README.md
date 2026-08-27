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
![License](https://img.shields.io/badge/license-MIT-green)

</div>

A guided, plain-language tool that helps research organizations assess how
"FAIR" their data is — Findable, Accessible, Interoperable, and Reusable —
without needing a data librarian on staff. You answer plain-language questions
about your dataset, get a score, and the tool turns every weak spot into a
specific, actionable next step.

## What it does

**For a single dataset** — 12 plain-language questions based on the RDA FAIR
Data Maturity Model. You answer each one (with worked examples shown
alongside), get a score out of 100, and a plain-language report explaining
what's working and what to fix — with concrete steps for each gap. It also
generates an ordered action plan and offers a chat-based mentor to coach you
through fixing things one step at a time.

**For multiple sites in one initiative** (e.g. a multi-center consortium) —
6 questions about whether your sites describe their data consistently enough
to combine and compare: shared field names, a common data dictionary,
standardized categories, a way to link records across sites. A "we haven't
started this yet" answer is a real option here — it doesn't count against
your score, because being early is normal, not a failure.

See the in-app `/about` page (or [`docs/WHY-THIS-TOOL.md`](docs/WHY-THIS-TOOL.md))
for how this tool fits alongside other FAIR resources like F-UJI, the FAIR
Cookbook, and FAIR-DSM.

## Quick start

You'll need **Python 3.12+**, **Node.js 18+**, and an **LLM provider** (see
below). The app runs as two servers: a Python backend and a Next.js frontend.

### 1. Set up the backend

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"   # Windows; on macOS/Linux use .venv/bin/python
cp .env.example .env
```

Now edit `backend/.env` and fill in two things:

- **`DATABASE_URL`** — a Postgres connection string. The easiest option is a
  free [Neon](https://neon.tech) database (takes 2 minutes to set up). For
  quick local testing you can also use `sqlite:///./dev.db`.
- **`LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`** — see below.

Then load the question content into the database and start the server:

```bash
./.venv/Scripts/python.exe scripts/seed_indicators.py
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --reload-dir app
```

The backend is now running at `http://localhost:8000`.

### 2. Pick an LLM provider

This tool needs an LLM to generate reports, plans, and mentor chat. Without
one, the assessment wizard works but the report/plan/mentor screens will fail.

The quickest way to get started:

| Option | Cost | How to set up |
|---|---|---|
| **[OpenRouter](https://openrouter.ai/keys)** (easiest) | Pay-per-token (~$0.002 per assessment) | Sign up, copy an API key, **pick a specific model** (not `openrouter/auto`) |
| **[Ollama](https://ollama.com)** (free, local) | Free | Install, `ollama pull llama3.1:8b`. Works for trying things out, but small local models struggle with the larger prompts. |
| **Your own vLLM server** | $0 marginal | Point `LLM_BASE_URL` at your server. This is how ACE runs it in production. |

All three are configured the same way — just fill in the three values in
`backend/.env`. Ready-to-uncomment blocks for each option are in
`backend/.env.example`.

> **Important:** if using OpenRouter, pick a specific model (e.g.
> `meta-llama/llama-3.3-70b-instruct`). Don't use `openrouter/auto` — it
> picks a different model each time, which can silently break things.

### 3. Set up the frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend is now running at `http://localhost:3000`. Open it in your
browser and start an assessment.

> If your backend isn't on port 8000, create `frontend/.env.local` with
> `NEXT_PUBLIC_API_BASE_URL=http://localhost:YOURPORT` (see `.env.local.example`).

### 4. Run the tests (optional, confirms everything works)

```bash
# Backend — most tests need no database or LLM
cd backend
./.venv/Scripts/python.exe -m pytest tests/ -v
```

## Who built this

Built by [ACE](https://ace.ac.ug) — the Africa Center of Excellence in
Bioinformatics & Data Science, Kampala, Uganda. The first pilot user is ACE
itself, self-assessing its own data governance practices.

## For developers

If you're forking this repo or want to understand the architecture in depth —
the engine/adapter pattern, the full API surface, branching conventions, repo
layout, LLM cost analysis, and testing strategy — see
[`docs/TECHNICAL.md`](docs/TECHNICAL.md).

Other useful docs:
- [`ROADMAP.md`](ROADMAP.md) — what's built, what's next, what's parked
- [`CHANGELOG.md`](CHANGELOG.md) — dated record of what shipped
- [`docs/WHY-THIS-TOOL.md`](docs/WHY-THIS-TOOL.md) — how this fits the FAIR-tooling landscape
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — why this project, and the design decisions along the way

## Citation

If you use this tool in published research, please cite it. See
[`CITATION.cff`](CITATION.cff) for the preferred citation format (GitHub also
surfaces this as a "Cite this repository" button on the repo page).

## License

[MIT](LICENSE) — the repo is public. Built by
[ACE](https://ace.ac.ug) (Africa Center of Excellence in Bioinformatics &
Data Science, Kampala, Uganda).
