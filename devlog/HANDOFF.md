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

---

## 2026-08-24 — Plan Mode run, backend engine scaffolded and tested, branching fixed

**What exists now:**
- The v0 implementation plan was produced via Plan Mode from `docs/PLANNING_PROMPT.md` and approved. It is not duplicated in this repo — find it wherever this session's Claude Code plan files live (referenced as `let-s-open-plan-mode-silly-lynx.md` at plan-approval time); `ROADMAP.md`'s checkpoints are the living summary of it.
- Backend engine scaffold exists and is tested: `backend/app/engine/` (data model, `Adapter` Protocol, scoring, remediation-writer with grounding checks, LLM client), `backend/app/main.py` (FastAPI + CORS), `backend/tests/engine/test_boundary.py` (passes — proves the engine/adapter boundary against a fake adapter, before any FAIR content exists).
- **Nothing in `backend/app/adapters/fair/` yet** — that's Checkpoint 2, next.
- No frontend yet (Next.js confirmed as the choice, not scaffolded).
- No database provisioned yet — `DATABASE_URL` in `.env` is still a placeholder; Neon project needs creating before any DB-touching code can run.

**What was decided, and why:**
- **LLM serving**: dual on-prem OpenAI-compatible providers, both verified live during planning — local Ollama (`http://localhost:11434/v1`, models `llama3.1:8b`/`gemma3:4b`) for dev, vLLM (`http://10.35.50.41:8000/v1`, `ibnzterrell/Meta-Llama-3.3-70B-Instruct-AWQ-INT4`, 131k context) for pilot. No third-party hosted API involved at all — simpler than the plan's original draft, and nothing leaves the local network.
- **Frontend**: Next.js from the start (not the plan's own recommendation of server-rendered Jinja2+htmx) — explicit user call, matches their default stack. Realistic v0 timeline estimate moved from ~2 weeks to ~3 weeks of *developer-days* accordingly — see the next point for why that day-based estimate itself was replaced.
- **Timelines**: the plan's day-based milestones assumed unassisted solo development. Actual pace with Claude doing the implementation is much faster — Checkpoint 1 (all of "Days 1-2" in the original plan) took a fraction of one session. `ROADMAP.md` now tracks **checkpoints**, not calendar days.
- **Branching**: caught mid-session that work was being committed straight to a shared branch (`master`), against the user's standing CLAUDE.md convention. Fixed: renamed `master` → `main`, moved the in-progress backend work to `feature/v0-backend-scaffold`, ran a self-review pass (`code-review` skill, low effort) on the diff before merge — found and fixed one real bug (a regex missing a word-boundary, in the jargon filter in `remediation.py`) — then merged to `main`. **Going forward: every unit of work gets its own feature branch, gets self-reviewed before merging to `main`, and nothing is ever pushed to the GitHub remote without asking first, even after a local merge is approved.**
- **GitHub repo**: did not exist yet as of this session's start; created as **private** during this session (see repo settings — not duplicated here since it can change).

**What's next:** Checkpoint 2 — author `backend/app/adapters/fair/indicators.yaml` (the 12 selected RDA indicators from the plan), implement `adapter.py`'s `score()`, wire the seed script. This is the highest-leverage single artifact in the whole build per the plan — get the questions and rubric right here before anything downstream depends on them. Then Checkpoint 3 (new, added mid-session): build a small library of synthetic demo datasets (varied sizes/formats) — see `ROADMAP.md` for why this was moved early rather than left until the end. The underlying concern: real ACE/TASO data, especially anything OMOP/health-record-shaped, likely needs a cleared data-governance path before it can touch any LLM at all, on-prem or not — synthetic data sidesteps that question entirely for demo/dev purposes.

**Open questions carried forward:**
- Neon Postgres project still needs provisioning — nothing DB-backed can be tested until `DATABASE_URL` is real.
- The 12th indicator (the "flex slot" between F3-01M and I3-01M in the plan) is still undecided — deferred to post-pilot feedback per the plan.
- License for the repo is still undecided (repo itself is now created, but private — see README).

---

## 2026-08-24 — branching corrected to the full three-tier structure

**Correction to the previous entry's "Branching" note above:** that entry described feature-branch-to-`main` as the fixed process. It wasn't the full fix — the user's CLAUDE.md specifies a **three-tier** promotion path (isolated feature branch → shared/staging → production), and merging straight into `main` skipped the staging tier and the PR-gated production step entirely. Caught when the user asked directly why the branch split hadn't happened.

**What was decided:**
- Real structure, per explicit instruction, matching the user's CLAUDE.md literally: `feature/<name>` → `development` → `staging` → `main`, one direction only. Feature branches never commit to any of the three shared branches directly. `development`→`staging` and `staging`→`main` each get a review pass; pushing `development` or `staging` to GitHub is never automatic, always confirmed first; `main` is reachable **only** via a PR from `staging`, preceded by a second independent review (Open Code Review delegate mode), merged only on explicit go-ahead. See `README.md`'s "Branching convention" for the canonical description — that's the source of truth, not this log.
- **One-time exception, explicitly approved by the user:** the backend scaffold that had already been merged straight into `main` (previous entry) stays there rather than being fixed via a history rewrite/force-push, since nothing is deployed yet and the user gave blanket approval for that specific batch. Every commit from this point forward goes through the real structure — no further exceptions.
- Attempted to add GitHub branch-protection rules on `main` (block direct pushes, require a PR) as a platform-enforced backstop, not just a remembered process. **Not available**: GitHub blocks branch protection on private repos below the Pro tier. Flagged to the user as an option (GitHub Pro, ~$4/mo) if a hard guarantee is ever wanted — for now this is enforced by process discipline only, not tooling.
- `staging` and `development` branches created (currently identical to `main` — no divergent content yet).

**What's next:** this branching correction itself lands via the new structure (feature branch → development, confirm before pushing development — not yet promoted to staging/main). After that, Checkpoint 2 resumes on a fresh feature branch off `development`.

**Open question for the user:** promotion cadence from `development` → `staging` → `main` isn't specified yet — i.e., after every feature merge, or batched at real checkpoints/releases? Defaulting to "propose promotion at meaningful checkpoints, not after every small change" unless told otherwise.

---

## 2026-08-24 — Checkpoint 2: FAIR adapter content

**What exists now:** `backend/app/adapters/fair/` is populated — `indicators.yaml` (12 indicators), `content.py` (YAML loader, cached + deep-copied), `adapter.py` (`FairAdapter`, implements `engine.ports.Adapter`), `scoring_rubric.py`. `scripts/seed_indicators.py` loads it all into a DB, idempotently. `backend/tests/adapters/fair/test_adapter.py` covers question-set shape, content completeness, and scoring. Full suite: `pytest tests/` → 5 passed.

**What was decided:** the 12th "flex slot" indicator resolved to F3-01M (completes Findable coverage) over I3-01M (cross-dataset linking, judged premature — same reasoning already used to defer I3's other sub-indicators in the original plan). See `docs/DECISIONS.md` v7 for the full rationale.

**Bugs found and fixed this session** (worth reading if picking this up cold — these are exactly the kind of thing that would silently corrupt scoring):
1. PyYAML's "Norway problem" — unquoted `yes`/`no` in `indicators.yaml` were silently parsed as Python `True`/`False`, breaking every rubric lookup. Caught by running the tests, not by reading the code. Fixed by quoting them; comment left in the YAML explaining why.
2. `seed_indicators.py` raised `DetachedInstanceError` reading `adapter.id` in a log message after the DB session that owned it had closed. Fixed by capturing the value before the session closes.
3. (Self-review, after the above) `indicators.yaml`'s `&anchor`/`*alias` reuse meant every indicator sharing the default rubric/options pointed at the literal same Python object, not a copy — a latent shared-mutable-state bug if any future code customizes one indicator's rubric. Fixed with `copy.deepcopy` in `content.py`.
4. (Same pass) the YAML file was being parsed from disk three separate times per `FairAdapter` construction. Fixed with a single `@lru_cache`d loader.

**What's next:** Checkpoint 3 (synthetic demo datasets) or Checkpoint 4 (backend REST API) — see `ROADMAP.md`. This work is sitting on `feature/fair-indicators`, not yet merged into `development` — needs a self-review confirmation and a "push development" go-ahead like last time before it lands there.

**Open questions carried forward:** Neon Postgres still not provisioned (seed script only smoke-tested against SQLite so far — Postgres-specific behavior, e.g. the JSON column type, isn't proven yet). Promotion cadence for development→staging→main still unconfirmed by the user.

---

## 2026-08-24 — Checkpoint 3: synthetic demo datasets, LLM default switched to vLLM

**What exists now:** `backend/fixtures/synthetic_datasets.py` (4 fake dataset profiles), `backend/app/adapters/fair/prompt.py` + `prompts/remediation.jinja` (pulled forward from a later checkpoint — a real demo needed real remediation text), `scripts/run_demo_assessment.py` (runs every fixture through the full engine + a live LLM, writes `docs/demo_reports/<slug>.md`). Full suite: `pytest tests/` → 14 passed. Generated reports for all 4 datasets are committed at `docs/demo_reports/`.

**What was decided — read this one, it reverses something the approved plan assumed:**
- The plan's dev-LLM choice (local Ollama, for fast iteration without tying up the shared A100s) was tested against reality and was wrong: the first demo run against Ollama didn't finish one dataset in 5 minutes. The user pointed out vLLM is faster in practice on this hardware and is the only endpoint that matters once this actually runs at ACE. **LLM default is now vLLM everywhere** (`app/config.py`, `.env.example`, `README.md`) — Ollama is an offline fallback only, not the routine dev path. Re-run against vLLM: all 4 datasets, ~150 seconds total, no failures.
- `app/config.py`'s `database_url` was made optional (defaults to a local SQLite file) — it was a required field with no default, which meant even scripts that never touch the database (like the demo runner) couldn't import `app.config` without a Postgres/Neon URL configured. Real environments still set `DATABASE_URL` in `.env`.

**Bugs found this session** (the first two matter for anyone touching remediation quality later):
1. The remediation grounding check rejected a correct, appropriate response for a `dont_know` answer with a thin note ("This has never come up") — flagged as "no overlap with the user's actual answer/note" even though the prompt design deliberately asks for generic "who to ask" guidance in that case, which naturally won't share words with a near-empty note. Found live against real vLLM output, not by review. Fixed: `dont_know` answers now bypass the overlap check; regression test in `tests/engine/test_remediation.py`.
2. (Self-review) `scripts/run_demo_assessment.py`'s docstring still said the tool defaults to Ollama, written before the switch above. Fixed to match.

**What's next:** Checkpoint 4 (backend REST API) — see `ROADMAP.md`. This work is sitting on `feature/synthetic-demo-datasets`, not yet merged into `development`.

**Open questions carried forward:** Neon Postgres still not provisioned. Promotion cadence for development→staging→main still unconfirmed. Worth reading a couple of the generated `docs/demo_reports/*.md` files directly if picking this up cold — they're the clearest evidence of what the pipeline actually produces right now.

---

## 2026-08-24 — Checkpoint 4: backend REST API

**What exists now:** `backend/app/api/` — `routes_questions.py`, `routes_assessment.py`, `routes_answers.py`, `routes_report.py`, `schemas.py` — all wired into `main.py`. `backend/app/adapters/registry.py` added (`adapter_id` → concrete adapter lookup). `engine/ports.py`'s `Adapter` Protocol extended with `render_remediation_prompt` and `prompt_version`, implemented by `FairAdapter`; `scripts/run_demo_assessment.py` updated to go through the adapter methods instead of importing FAIR's prompt module directly, for consistency. Full suite: `pytest tests/` → 32 passed, including a live suite (`tests/api/test_report_live.py`) that calls the real vLLM endpoint for report generation, cache-hit verification, and the regenerate endpoint.

**What was decided:** report generation is cached — one `Report` DB row per run, generated on first `GET /report`, every later call returns it without touching the LLM again. This was a deliberate design choice, not a default: report generation calls the LLM once per weak/unknown finding, so re-generating on every page view would be both slow and wasteful. `POST .../findings/{id}/regenerate` exists for the one case you do want to redo — a single finding whose remediation didn't land well.

**Infrastructure note, not a bug in this repo:** partway through writing the live report tests, the vLLM endpoint stopped responding entirely (even `GET /v1/models` timed out — a server-side outage, not a slow-generation issue). Verified the new route logic was correct in the meantime by pointing at Ollama instead of blocking on it. vLLM came back during the same session; the full live suite was then run against it and passed cleanly. If a future session hits LLM timeouts on `tests/api/test_report_live.py`, check `curl http://10.35.50.41:8000/v1/models` first — it's very possibly this again, not a code regression.

**Bug found in self-review:** `_generate_report` in `routes_report.py` did an unguarded dict lookup for each answer's `Indicator` row, which raised a raw `KeyError` (opaque 500) if `scripts/seed_indicators.py` hadn't been run against that database yet — a genuinely likely setup-order mistake, since answering and completing a run don't touch the DB's `Indicator` table at all (they validate against the adapter's in-memory question set), so the failure only surfaces at report-generation time. Fixed with a clear error message; regression test added using a deliberately unseeded database.

**What's next:** Checkpoint 5 (Next.js frontend) — see `ROADMAP.md`. This work is sitting on `feature/backend-rest-api`, not yet merged into `development`.

**Open questions carried forward:** Neon Postgres still not provisioned (all testing so far is against throwaway SQLite files). Promotion cadence for development→staging→main still unconfirmed.
