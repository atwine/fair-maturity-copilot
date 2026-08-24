# Handoff log

Running context for any agent (Claude, Devin, or a fresh session of either) picking this project up with no prior memory of it. Append a new dated entry each session — don't rewrite history, add to it.

---

## 2026-08-24 — repo scaffolded, planning prompt drafted

**What exists:** Nothing implemented yet. This is a planning-stage scaffold only.

**What was decided, and why:**
- Project is `fair-maturity-copilot`: a guided, plain-language FAIR data-maturity self-assessment tool, built as a reusable engine (`intake → scoring → LLM remediation writer → report`) with a FAIR-specific adapter as v0.
- A second adapter, applying the same engine to OHDSI's OMOP CDM Data Quality Dashboard output, is planned but explicitly **not started** — see `../ROADMAP.md` for why (blocked on external data access) and `docs/DECISIONS.md` for the full reasoning trail.
- Full scoping history (why this idea over nine others) is in `docs/background/` and `docs/DECISIONS.md`.

**What's next:**
1. Run `docs/PLANNING_PROMPT.md` through Claude's Plan Mode to produce the actual v0 implementation plan (architecture, indicator subset, data model, tech stack, milestones).
2. Once that plan exists, start implementation against it.
3. Decide public/private status and license for the GitHub repo — currently undecided, not blocking anything yet.

**Open questions for whoever picks this up:**
- Tech stack is proposed (FastAPI + Next.js/React/Tailwind/shadcn, Postgres via Neon) but not confirmed — Plan Mode was asked to push back if a simpler stack fits better.
- Which ~10-12 of the RDA's 41 FAIR indicators to implement first is still an open call for Plan Mode to make.
- Whether the remediation-writer LLM step should default to the local Llama 3.3 70B or a smaller/hosted model during development is still open.

**How to update this file:** append a new `## YYYY-MM-DD — short summary` section at the bottom each session. Include: what changed, what was decided and why, what's next, and any open question a fresh agent would otherwise have to rediscover by reading the whole codebase.
