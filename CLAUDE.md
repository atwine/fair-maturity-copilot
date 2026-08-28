# Project context for Claude Code sessions

@AGENTS.md

## Quick orientation

This is the **FAIR Maturity Copilot** — a guided, plain-language self-assessment
tool that helps research groups check how "FAIR" their data is (Findable,
Accessible, Interoperable, Reusable) without needing a data librarian. Built for
research group leads at institutions like ACE Uganda who don't have data
management training but increasingly need to meet funder FAIR expectations.

## Current state (as of 2026-08-29)

### Design: "The Micrometer" (Direction #19)

The landing page was redesigned through an iterative exploration process (19
directions explored in git worktrees, D19 selected and merged). The aesthetic is
a **precision measuring instrument**: FAIR principles rendered as linear barrel
scales with thimble markers at reading positions.

**Design tokens** (in `frontend/app/globals.css`):
- `--primary: #3D6B7A` (steel-teal — blued steel)
- `--background: #F7F3E9` (warm ivory)
- `--foreground: #2A2520` (warm near-black)
- `--muted-foreground: #5a4d38` (darkened for readability)
- `--gold: #8A6D2F`, severity colors unchanged
- Heading font: **Hanken Grotesk** (via `next/font/google` in `layout.tsx`)
- Body font: **Geist** (unchanged)

**Key design files:**
- `frontend/app/page.tsx` — landing page
- `frontend/app/globals.css` — theme tokens
- `frontend/app/layout.tsx` — font loading + root layout
- `frontend/components/logo-mark.tsx` — logo (recolored for new palette)
- `frontend/components/sample-measurements.tsx` — client component with randomized barrel-scale readings
- `frontend/components/sample-question-preview.tsx` — collapsible sample question (trigger styled as full-width primary button)

**Design conventions established:**
- Full-width primary buttons for all CTAs, distributed across the page with divider lines
- `text-justify` on body paragraphs across all pages
- No `max-w-lg`/`max-w-xl` constraints on subtitles — let text span full content width
- Minimum text size is `text-xs` (12px) — no `text-[0.5rem]` or smaller
- FAIR principle icons: Search (F), KeyRound (A), Puzzle (I), Recycle (R) from lucide-react

### Worktrees

All design exploration worktrees have been cleaned up. Only one remains:
- `dark-landing-trial-d19` — The Micrometer (the chosen design, merged to development)

The main repo is on `development` branch. The worktree can be removed if desired
since the work is merged.

### Backend

- FastAPI + SQLModel + Alembic + Postgres (Neon)
- LLM-powered remediation text generation and mentor chat
- Two adapters: `fair-v0` (12-question single-dataset) and `harmonization-v0` (6-question multi-site)
- Backend `.env` lives at `backend/.env` (not in worktrees — copy from main repo if needed)
- Python venv at `backend/.venv` (main repo only)

## How to run locally

### Frontend (port 3000)
```bash
cd frontend
npm install   # if needed
npm run dev
```

### Backend (port 8000)
```bash
cd backend
# Activate venv from main repo:
& "..\..\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The frontend expects the backend at `http://localhost:8000` (see `frontend/lib/api-client.ts`).

## Architecture overview

```
frontend/          Next.js 16 + React 19 + Tailwind v4 + shadcn/ui
  app/
    page.tsx                          Landing page (The Micrometer)
    about/page.tsx                    "Why this tool exists" + FAIR icons
    navigator/page.tsx                "Which tool fits?" branching guide
    assessments/
      new/page.tsx                    Start a new assessment
      [id]/question/[indicatorId]/    Question wizard
      [id]/review/page.tsx            Review answers
      [id]/report/page.tsx            Score + findings report
      [id]/plan/page.tsx              Ordered remediation plan
      [id]/mentor/[stepId]/page.tsx   Chat mentor for a plan step
  components/
    site-header.tsx                   Shared header (logo + nav)
    logo-mark.tsx                     SVG logo
    fair-spectrum.tsx                 Progress tracker + PrincipleChip
    sample-measurements.tsx           Barrel-scale readings (client, randomized)
    sample-question-preview.tsx       Collapsible sample question
    navigator.tsx                     Branching tool-finder quiz
    loading-state.tsx                 Spinner + message
  lib/
    api-client.ts                     Typed FastAPI client
    types.ts                          Shared types mirroring backend schemas

backend/           FastAPI + SQLModel + Alembic + Postgres
  app/
    main.py                          FastAPI app + CORS
    config.py                        Settings (env vars)
    db.py                            Database engine
    api/                             REST routes (questions, assessment, answers, report, plan, mentor)
    adapters/                        Assessment adapters (fair-v0, harmonization-v0)
  alembic/                           Migrations
  fixtures/                          Indicator definitions (YAML)
  eval/                              Eval harness
  tests/                             pytest tests
```

## Branching

See `AGENTS.md` for the hard limits. Summary:
- All work starts on `feature/<name>` branches cut from `development`
- `feature → development → staging → main` (one direction)
- Never push to `development`/`staging`/`main` without explicit owner approval
- Never commit directly to shared branches
