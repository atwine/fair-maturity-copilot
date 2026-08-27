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

---

## 2026-08-27 — Issue #16 (Level 2 harmonization check): plan approved, PR 1 in progress

**Why this entry exists:** the project owner asked explicitly, mid-session, to
keep this log and the plan document current at every step — there's a real
chance this work gets handed to Devin partway through if this session runs
out of budget. Treat this entry as the thing to read first if that happens:
it says exactly what's done, what's half-done, and what's next.

**The plan:** full approved implementation plan is now committed in-repo at
[`docs/PLANS/issue-16-harmonization-plan.md`](../docs/PLANS/issue-16-harmonization-plan.md)
— read that first, it has the full context (why a second adapter, what's
reused vs. new, the exact 5-PR sequence). This entry only tracks *progress*
against that plan; the plan itself is the source of truth for *what* and
*why*.

**Status as of this entry: PR 1 (engine fixes) is in progress, not yet
committed.** Working on branch `feature/engine-plan-boundary-fix` off
`development` (created this session, not yet pushed anywhere). Nothing has
been committed to git yet — all changes so far exist only as uncommitted
edits in the working tree, if any are already applied by the time this is
read. **If picking this up cold: run `git status` and `git diff` on this
branch first** to see exactly what's actually landed vs. still just planned.

**What PR 1 is, in one line:** fix `backend/app/api/routes_plan.py`'s direct
import of `app.adapters.fair.plan` (a real bug — every run's walkthrough plan
uses FAIR's own wording regardless of which adapter it belongs to, harmless
today only because there's just one adapter), move a couple of genuinely
adapter-agnostic pieces into `app/engine/` where they belong, and teach
scoring/remediation about a new non-penalized `not_started` outcome — all
with **zero visible behavior change** to today's check, proven by the full
existing test suite passing unchanged plus new tests for the new behavior.
Exact file list is in the plan doc's "PR 1" section.

**What's next, in order, per the plan doc:** finish PR 1 → PR 2
(`harmonization-v0` adapter content/backend) → PR 3 (frontend plumbing) → PR 4
(the two entry points: report-page suggestion card + navigator rework) → one
`development → staging → main` promotion pass with both required review
passes. Do not skip either review pass. Do not push anything without the
project owner's explicit go-ahead first, per standing convention.

**Open/carried-forward items specific to this feature** (flagged during
planning, not yet resolved — see the plan doc's "Risks" discussion in the
design agent's notes, not reproduced in the committed plan doc itself):
- `_SEVERITY_RANK`'s exact sort position for `not_started` (currently
  planned as "just above pass") only affects display order, not scoring —
  low-stakes, fine to leave as implemented unless it looks wrong live.
- Whether this repo runs `mypy`/`pyright` in CI was flagged as worth
  checking before PR 1, because `FakeAdapter` in `tests/engine/test_boundary.py`
  won't implement the new `build_plan` Protocol method — harmless at runtime
  (Python Protocols are structural/unenforced without a type checker) but
  worth a stub method if static type-checking turns out to be wired up.
  **Not yet checked as of this entry** — no `.github/workflows/` found in a
  first pass, so likely not CI-enforced, but confirm before assuming.

**How to update this entry going forward:** don't rewrite it — when a PR
from the plan lands, append a new dated entry below this one (same format as
every other entry in this file: what exists now, what was decided, what's
next, open questions), same as always. This entry stays as the "mid-PR-1"
snapshot.
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

---

## 2026-08-24 — Promoted development → staging (Checkpoints 2-4 + branching fix)

**What happened:** `development` merged into `staging` (`--no-ff`, 41 files, everything since the initial `main` scaffold: the three-tier branching fix, FAIR adapter content, synthetic demo datasets + LLM switch to vLLM, and the full backend REST API). No new review pass was run at this promotion step specifically — each checkpoint was already individually self-reviewed (`code-review` skill) before merging into `development`, so re-reviewing identical code here would be pure duplication. What this promotion step *did* do: ran the full test suite against the merged `staging` state (`pytest tests/` → 32 passed) to confirm nothing about the merge itself introduced a regression, before pushing.

**Not yet done:** the `staging` → `main` step, which per `README.md`'s branching convention requires a PR (not a direct push), a second independent review via Open Code Review delegate mode, and the user's explicit go-ahead to merge. That's a separate, later step — not implied by this promotion.

**What's next:** Checkpoint 5 (Next.js frontend), continuing on `development` via a fresh feature branch — promoting to `staging` doesn't change where new work branches from.

---

## 2026-08-24 — Checkpoint 5: Next.js frontend, and a real production bug found by testing it live

**What exists now:** `frontend/` — full Next.js 16 + React 19 + Tailwind v4 + shadcn/ui (Base UI) scaffold, the 4-screen wizard wired to the backend via `lib/api-client.ts`. Walked the entire flow twice in a real browser via the Claude in Chrome extension (per standing instruction to verify UI changes live, not just via automated tests) — first run surfaced a real bug (below), second run confirmed the fix. `pytest tests/` → 33 passed (backend); frontend `tsc --noEmit` and `eslint` both clean.

**The bug, and why it matters for whoever picks this up next:** the completed report showed "8 of 24 indicators have something worth fixing" on a 12-indicator assessment, with every finding duplicated, plus React "duplicate key" console warnings. Root cause: `GET /assessments/{id}/report` had no protection against being called twice concurrently for the same run — React 19 Strict Mode's double effect invocation in dev triggered it reliably, but the same failure mode is reachable in production via a double-click or a page refresh mid-generation. Two concurrent calls both saw "not generated yet" and both ran a full LLM generation pass.

**Fixed at the database level:** unique constraints added — `Answer` and `Finding` on `(run_id, indicator_id)`, `Report` on `run_id` (`engine/models.py`). The losing concurrent request now catches the constraint violation and **waits** (polls up to 90s) for the winner's row to actually commit, rather than erroring immediately — the first fix attempt got this wrong, returning an error the instant it saw the conflict, which is well before the winner (still mid-LLM-call) has finished. `routes_answers.py`'s answer-upsert had the identical unprotected pattern and got the same defensive fix pre-emptively, before it could cause the same class of bug.

**How this was actually verified, not just asserted fixed:**
1. A direct-function test firing two threads at `_generate_report` against a shared SQLite engine — passed immediately (too fast to catch the real bug, see #2).
2. A real concurrent-HTTP test via `ThreadPoolExecutor` against a running uvicorn instance — this is what actually reproduced the "loser gives up too early" failure mode before the wait-and-retry fix, and confirmed it after (`tests/api/test_report_live.py::test_concurrent_report_generation_does_not_duplicate_rows`).
3. A clean re-run of the full flow in the real browser afterward — correct "1 of 12," no duplicate findings, no console warnings, confirmed directly against the SQLite file (1 `Report` row, 12 `Finding` rows).

**Other things worth knowing if touching this area again:**
- shadcn now generates Base UI components, not Radix — `asChild` doesn't exist; use `render={<Element />}` plus `nativeButton={false}` when rendering a `Button` as something other than a real `<button>` (an anchor via `next/link`, for instance). Base UI logs a clear console warning if you get this wrong; that's how it was caught here.
- Next.js dynamic route pages now receive `params` as a `Promise` — must `await params`. `next dev` auto-generates `frontend/AGENTS.md` warning about exactly this kind of drift from older training data; worth actually reading it, not just noting it exists.
- Local component state that should reset when a route param changes (the question wizard's per-question form state) is reset by remounting via `key={indicatorId}`, not by syncing through a `useEffect` — the latter is exactly what ESLint's `react-hooks/set-state-in-effect` rule now flags.
- `_load_report_out` also got a fix in the same pass: it picked an arbitrary `RemediationDraft` per finding when more than one existed (after a regenerate call) — now explicitly ordered by `generated_at` so the latest one always wins.

**What's next:** Checkpoint 6 (eval harness) or Checkpoint 7 (deploy) — see `ROADMAP.md`. This work is sitting on `feature/nextjs-frontend`, not yet merged into `development`.

**Open questions carried forward:** Neon Postgres still not provisioned. Promotion cadence for development→staging→main still unconfirmed. Both local dev servers (backend on :8000, frontend on :3000) were left running in this session's background — a fresh session should check whether they're still up before starting new ones.

---

## 2026-08-24 — design-critique pass: a font that was never rendering, and 3 other mechanical fixes

**Why this happened now:** user asked directly which upcoming checkpoint covers visual design. Answer: none of them (6/7/8 are eval harness/deploy/pilot). Ran `design-critique` against all 4 live screens rather than let that gap ride further.

**The headline finding:** `frontend/app/globals.css` had `--font-sans: var(--font-sans)` — a circular self-reference from the shadcn scaffold that never got corrected to `var(--font-geist-sans)` (the variable `layout.tsx` actually sets via `next/font/google`). It resolved to nothing, so the whole app was silently rendering in the browser's default serif (confirmed via `getComputedStyle(document.body).fontFamily` → `"Times New Roman"`). This is exactly the kind of bug a design-critique catches that a code review doesn't — nothing errors, nothing fails a type check, it just silently isn't doing what the surrounding code clearly intends. Fixed; confirmed via computed styles afterward that Geist actually renders now.

**Other fixes from the same pass, all mechanical (an objectively correct answer, not a taste call):**
- Button sizes (`components/ui/button.tsx`) computed to ~28-36px — under the 44px WCAG touch-target minimum, with `sm` text at 12.8px. Bumped the whole size scale (`default` → 44px, `sm` → 40px, `lg` → 48px).
- All three data-fetching loading states were bare "Loading…"/"Generating…" text. Added `frontend/components/loading-state.tsx` (spinner + message) and used it consistently across the question wizard, review, and report pages.
- The selected-answer highlight in the question wizard was a single-pixel border-color change, too subtle to register — now a 2px border plus a fill tint plus bold label on the selected option.

**Deliberately not done in this pass:** the critique's other findings — no accent color anywhere (pure grayscale palette), inconsistent `Card` usage across screens, weak visual hierarchy on the report's score — are design judgment calls, not correctness fixes, and weren't decided unilaterally. User's own CLAUDE.md names `frontend-design` as the right skill for exactly this kind of call; that's the next step, not yet started.

**Verified:** `tsc --noEmit` and `eslint` both clean; re-walked all 4 screens live in the browser (Claude in Chrome extension) after the fixes, confirmed Geist font actually renders, button sizes visibly larger, selected-answer state clearly legible. Self-reviewed the diff (`code-review` skill) before merge — no findings, this was a small, mechanical, CSS/component-only change with no logic to get wrong.

**What's next:** either the `frontend-design` visual-identity pass (accent color, real type scale, layout consistency), or resume the roadmap at Checkpoint 6/7. This work is sitting on `feature/design-critique-fixes`, not yet merged into `development`.

**Open questions carried forward:** same as previous entry — Neon still not provisioned, promotion cadence unconfirmed, both dev servers still running in background from earlier in this session.

---

## 2026-08-24 — visual-identity pass (Checkpoint 5b, part 2), and a bug the pass introduced in itself

**What exists now:** all 4 screens carry a real visual identity — warm paper background, deep teal accent, muted gold, Fraunces headings over Geist body text, a persistent `SiteHeader`. The signature element is `frontend/components/fair-spectrum.tsx`'s `FairSpectrum`: a segmented tracker in the question wizard sized 4/3/1/4 by each FAIR principle's real indicator count, plus its `PrincipleChip` variant labeling rows on the review screen and findings on the report. Backend gained `principle_group` on `QuestionOut`/`FindingOut` to support this (`backend/app/api/schemas.py`, `routes_questions.py`, `routes_report.py`). Full design rationale in `docs/DECISIONS.md` v12.

**A bug found in self-review, worth knowing if touching `fair-spectrum.tsx` again:** the first implementation computed each segment's fill using a cumulative start-offset per principle group, assuming that group's questions sit in one contiguous block. They don't — the 12-question order is F,F,F,A,A,A,I,R,R,R,R,F (the flex-slot Findable indicator, F3, was added last to complete Findable's coverage, not grouped with the other three at the front — see `docs/DECISIONS.md` v7 for why). This made the Findable segment read as 100% filled after just 4 questions, then stay stuck there — wrong for the rest of the wizard. Fixed by counting each group's filled members directly by array index instead of by offset. **If this component gets touched again: never assume `principleGroups` (or any per-question array keyed by `display_order`) groups contiguously by principle — it doesn't, by design, because of the flex slot.**

**Verified:** `tsc --noEmit` and `eslint` both clean (including after the fix). 33 backend tests passing. Self-reviewed via the `code-review` skill — this is the finding that surfaced the bug above, fixed before merge. Walked the full flow live in the browser (fell back to the built-in browser this session — the Claude in Chrome extension reported "not connected" when tried first): landing page's F/A/I/R hero, the wizard's FairSpectrum tracker (confirmed via computed styles and DOM inspection that segments are sized 4/3/1/4 and fill correctly, including the contiguity-bug fix specifically at question 11), the review screen's chips, and the report's score coloring and per-finding chips, using a live vLLM-generated report (score 37.5, correctly rendered in the "major" red band). One incidental finding during this verification, unrelated to the visual-identity code itself: a stale backend process from a prior session was still bound to port 8000, serving code from before this session's `principle_group` addition — cost some time debugging an apparently-missing field before realizing it was a stale process, not a real bug. Worth checking `netstat -ano | grep :8000` (or the frontend's :3000) before assuming a fresh `uvicorn`/`next dev` invocation actually took over the port.

**Deliberately not done in this pass:** no dark-mode toggle exists yet (the `.dark` CSS block was filled in with a reasonable palette for completeness, but nothing in the app switches to it) — not a gap, just not yet relevant.

**What's next — and this is a bigger fork than the roadmap currently reflects:** right after this pass landed, the user raised a substantially bigger set of concerns than color and type: the landing page still gives no context on what the tool is or which maturity model it follows; the question wizard doesn't show a worked example per indicator; there's no real sense of "milestones" beyond the FairSpectrum bar; and what happens *after* the report is undesigned — is it just text, or something more like a fillable worksheet, or a guided multi-session experience that persists state per user? The user explicitly said the interface still feels like "the bare minimum" and asked for more innovative thinking here, not just polish. This is an information-architecture and product-depth question, not a visual one — see the next entry below, where the user answered this directly.

**Open questions carried forward:** same as previous entries — Neon still not provisioned, promotion cadence unconfirmed. Both dev servers were left running in background from this session (backend restarted once after the stale-process issue above — confirm which PID is actually current before reusing them).

---

## 2026-08-24 — guided-remediation direction chosen; report screen rebuilt (Checkpoint 5c)

**Direction chosen:** asked the user directly which of three options to build toward for "what happens after the report" — a downloadable artifact, a persistent action tracker, or full guided remediation sessions. **They chose guided remediation sessions** — the most ambitious, and the one that eventually wants some form of per-assessment persisted state, not just a static report. Nothing about that larger session flow is built yet; this entry is the first concrete step toward it, prompted by immediate feedback on the just-shipped report screen.

**What triggered this specifically:** direct feedback that the report was "just a list of cards" with small text requiring squinting, one dense unstructured paragraph per finding, passing indicators shown as a bare title with zero explanation, and unexplained acronyms ("you can say 'DOI' and assume whoever reads it knows what it means" — the user's words). All four addressed in this pass.

**What changed:** the remediation prompt (`backend/app/adapters/fair/prompts/remediation.jinja`, `PROMPT_VERSION` bumped `v1`→`v2`) now requires a fixed `SUMMARY: <sentence>` / `STEPS: 1. ... 2. ...` output format instead of free prose, plus an explicit rule that every acronym or tool name must be explained in plain words the moment it's first used. Every finding gets a remediation call now, including passing ones (`_do_generate_report` no longer skips `severity == "pass"`) — a pass gets a short "why this is fine" SUMMARY with no STEPS. This is a real Adapter Protocol change: `render_remediation_prompt` gained a required `severity` parameter (`engine/ports.py`), which any future adapter (the parked OMOP one included) will need to implement.

**Frontend:** `frontend/lib/parse-remediation.ts` parses the SUMMARY:/STEPS: contract; the report screen now renders every finding (gap or pass) through one `FindingCard` — a one-line summary always visible, numbered steps behind a click-to-expand `Collapsible` (newly added shadcn/Base UI component). Body text bumped 14px → 16px throughout the report.

**Two bugs caught in self-review before merge, both fixed, worth knowing if touching this code again:**
1. The grounding check's word-count floor (widened to 8 to accommodate short pass summaries) could still reject a genuinely good 7-word summary — loosened further to 5.
2. `parseRemediation` originally used `text.search(/STEPS:/i)`, a substring search that would misfire if the model's own SUMMARY sentence happened to contain the word "steps:" — fixed to anchor on a line-start match (`/^\s*STEPS:/im`), matching the prompt's actual one-field-per-line output shape. **If this parser is touched again: always anchor to line-start, never do a bare substring search against LLM output that might echo a field-name-like token in unpredictable places.**

**A repeated operational gotcha, worth calling out explicitly since it cost real time twice in this session:** the backend `uvicorn` process was started without `--reload` early in the session. Every subsequent backend code change (through the whole visual-identity AND guided-remediation passes) was silently NOT picked up until the process was manually killed and restarted — twice, both times discovered only by noticing live API responses didn't match the code that was just written. **Always start the dev backend with `--reload` from the very first launch of a session** (`uvicorn app.main:app --port 8000 --reload`) — this alone would have prevented both incidents.

**Verified:** `tsc --noEmit` and `eslint` clean. 34 backend tests passing (including a new pass-severity grounding-check bypass test, mirroring the existing dont_know one). Live-verified twice against real vLLM output after restarting the backend with `--reload`: confirmed the SUMMARY/STEPS format renders correctly, the Collapsible expand/collapse works, passing findings show real explanatory text, and `POST .../regenerate` now succeeds (200, not the old 400) on a passing finding. Self-reviewed via the `code-review` skill both before and after the two fixes above.

**What's next:** still open and unscoped — landing-page context (what FAIR is, which model this follows), per-question worked examples, and the actual guided-remediation-session flow itself (persisted per-finding status, revisit-and-see-progress). This pass only rebuilt the report screen's presentation/content model; the session flow will extend it, not replace it. This work landed on `feature/report-guided-remediation`, merged locally into `development` — still not pushed to GitHub, pending the user's go-ahead per standing workflow rules.

**Open questions carried forward:** Neon still not provisioned, promotion cadence unconfirmed. Both dev servers running in background — backend now correctly started with `--reload` this time (PID current as of this entry), frontend's Next dev server also still up from earlier in the session.

---

## 2026-08-25 — landing-page context + per-question worked examples (Checkpoint 5d)

**What exists now:** two of the three items left open by 5c are closed. Landing page (`frontend/app/page.tsx`) now explains what FAIR actually means (a plain-language one-liner per letter, not just the word), walks through how the tool works in 3 steps, and names the RDA FAIR Data Maturity Model plus why 12 of its 41 indicators were chosen. Every indicator now carries a required `example` field — added to `indicators.yaml`, the `Indicator` model, `content.py`, `QuestionOut`, and `scripts/seed_indicators.py`'s upsert field list — rendered directly under each question in the wizard (always visible, not behind the existing "Why this matters" toggle). All 12 examples are grounded in concrete health-data/LMIC scenarios (a TB genomics dataset on Zenodo, a REDCap-collected survey, an ethics-approval process) and deliberately explain every technical term on first use, per the user's direct complaint about assumed jargon like "DOI."

**Schema note for whoever touches `Indicator` next:** `example` is a required (non-nullable) column with no default — added by deleting and reseeding `dev.db` rather than an Alembic migration, since there's still no real Neon database and no real user data to preserve. **This will not work once a real database with real assessment data exists** — at that point, adding a new required `Indicator` column needs an actual migration (add nullable, backfill, then tighten — or just make it nullable if a missing example is acceptable). Worth flagging early since this is the second schema change handled this way (principle_group was the first, back in the visual-identity pass) — the pattern won't survive contact with production data.

**Verified:** `tsc --noEmit` and `eslint` clean. 34 backend tests passing (unchanged — this pass added a new required field but no new logic/branches, so no new test cases were needed beyond updating the one fake-Indicator constructor in `test_boundary.py`). Live-verified in the browser: landing page renders the new legend/steps/RDA-citation content, and the question wizard's "For example:" box renders the worked example directly under the question text, tinted with the accent color. Self-reviewed the diff via the `code-review` skill — no findings; every changed file was pure field-plumbing (a new field threaded through model → content loader → schema → route → frontend type → render) or static content (the YAML examples, the landing page copy), with no new conditional logic to get wrong.

**What's next:** the one remaining piece from 5c/5d's scope — the guided-remediation-session flow itself. This needs a real scoping conversation before implementation: what "resolved" means for a finding, how status persists (presumably keyed off the existing unguessable assessment UUID, no auth needed), and whether/how a later re-assessment compares against an earlier one to show improvement over time. This is the biggest remaining piece of what the user actually asked for when they chose "guided remediation sessions" as the direction in the 5c conversation.

**Open questions carried forward:** Neon still not provisioned — and now slightly more urgent than before, since the "delete and reseed dev.db" pattern used for both `principle_group` and `example` won't survive a real database with real data (see schema note above). Promotion cadence for development→staging→main still unconfirmed. This work landed on `feature/landing-context-and-examples` — caught mid-session that it had been written directly on `development` rather than its own branch (the changes were still uncommitted, so `git checkout -b` cleanly moved them without needing any cleanup on `development`) — pending merge and, after that, the user's go-ahead to push everything queued so far to GitHub. Both dev servers still running in background from this session.

---

## 2026-08-25 — guided-remediation v0: revisit and re-score a finding (Checkpoint 5e)

**Scoped before building, per the user's explicit request.** Three questions, each resolved to the smaller option (full reasoning in `docs/DECISIONS.md` v15): "mark fixed" = re-answer the question (not a new status flag — avoids two sources of truth); progress tracking is single-assessment-only for v0 (no cross-run history/dashboard yet); revisiting reuses the existing single-question screen (`QuestionForm`) rather than a new inline editor on the report cards.

**What exists now:** report finding cards have an "Update your answer" action (`/assessments/{id}/question/{indicatorId}?from=report`). The question page detects `?from=report` and renders a lighter "revisit" mode — no wizard chrome, "Save and return to report" instead of "Next," navigates straight back to the report on success. Backend: `PUT /assessments/{id}/answers/{indicator_id}` no longer blocks edits on a completed run; a new `_rescore_finding_and_refresh_report` (`routes_report.py`) runs afterward if a report already exists — re-scores the one changed `Finding`, re-writes its remediation (one LLM call), recomputes the composite score from all findings, and updates the cached `Report` row. No new tables or columns; this all runs on the existing scoring/remediation machinery, just triggered from a new event.

**Two bugs caught in self-review before merge, worth knowing if touching this code again:**
1. The remediation LLM call inside `_rescore_finding_and_refresh_report` originally had no exception handling — a network hiccup there would have propagated into a 500 on the *whole answer-save request*, even though the answer itself had already committed successfully a few lines earlier. Wrapped in a narrow try/except: severity always updates and commits (no LLM involved), only the remediation text is best-effort. **If this function is touched again: never let a step downstream of an already-committed write fail the whole request — degrade gracefully instead.**
2. Extracting a shared `_latest_remediation_by_finding_id` helper (now used by both `_load_report_out` and the new rescore path) surfaced a **pre-existing latent bug that predates this session**: `build_report_markdown` (`engine/report.py`) looks up remediation drafts by `str(finding.id)`, but `_load_report_out`'s original dict was keyed by the raw UUID object. The two only worked before because nothing had ever handed the same dict to both functions — this pass's refactor would have done exactly that, silently producing remediation-less markdown. Fixed by standardizing on string keys. **Lesson for future refactors in this file: when unifying two dicts that key by the same conceptual ID, check both consumers' actual key type before assuming they match.**

**Operational note — third time in this repo, worth actually fixing next time instead of rediscovering it again:** `uvicorn --reload` does not reliably restart on file changes in this OneDrive-synced working directory. Confirmed again this session: edited `routes_answers.py`, `--reload` never logged a restart, and a live browser test kept hitting the pre-edit code (the old "answers can no longer be edited" 400) for several minutes before this was diagnosed. **Manually kill and restart the backend after every backend code change in this environment — don't trust `--reload` here, full stop.** A cleaner long-term fix worth considering: move the repo (or at least `backend/`) outside OneDrive sync, or find an uvicorn/watchfiles flag that works around whatever OneDrive is doing to file-change notifications.

**Verified:** `tsc --noEmit`, `eslint`, and a full `next build` all clean (checked specifically that `useSearchParams()` didn't trigger Next's static-rendering/Suspense requirement — it doesn't, this route was already dynamic). 35 backend tests passing, including a new live test (`test_revisiting_an_answer_rescoes_and_refreshes_the_report`) that asserts the other 11 findings' remediation text is byte-for-byte untouched after a revisit — proving this is a targeted single-indicator update, not a disguised full regeneration hiding behind a small diff. Walked the full flow live in the browser: completed report showing a licensing gap at score 90.6, clicked "Update your answer," changed "No" to "Yes," landed back on the report automatically at score 100 with the finding correctly reclassified into "Looks good."

**What's next:** this closes the guided-remediation-session scope as currently defined — Checkpoints 6 (eval harness) and 7 (deploy + dogfood) are next on the roadmap, both previously deferred while this UX work was underway. Cross-assessment trend comparison remains explicitly out of scope until/unless the ACE pilot specifically asks for it. This work landed on `feature/revisit-and-update-findings`, not yet merged into `development` — pending merge and, after that, the user's go-ahead to push everything queued so far (5 checkpoints deep now) to GitHub.

**Open questions carried forward:** Neon still not provisioned. Promotion cadence for development→staging→main still unconfirmed. Both dev servers running in background — backend was killed and restarted (without `--reload`, per the note above) partway through this session; confirm it's still the current process before reusing it.

---

## 2026-08-25 — FAIR-tooling research synthesis, then the FAIRification plan (Checkpoint 5f)

**What triggered this:** the user pointed at three reference PDFs used at eLwazi (the DS-I Africa Open Data Science Platform, NIH-funded, UCT-hosted, same network as H3ABioNet) and asked for a synthesis: is this tool's approach actually right, and how do we make it more useful, given what's already out there. Read all three, plus web research on eLwazi's own FAIR guidance, F-UJI, and the RDA FAIR Data Maturity Model's own documentation. Full writeup in `docs/DECISIONS.md` v16.

**The headline finding:** this tool's foundation holds. eLwazi has no bespoke African FAIR framework of its own — its own guidance page points to the same global tooling (FAIRplus Dataset Maturity Model, FAIR Cookbook, ELIXIR's RDMkit) this research covered. One of the three PDFs, despite its "Africa" filename, turned out to be standard FAIRplus/ELIXIR training material delivered at the Cape Town venue, not an Africa-specific adaptation. The RDA FAIR Data Maturity Model (this tool's base) is exactly what F-UJI (the field's automated checker) also partially automates — but F-UJI only covers the *machine-readable* half of FAIRness; this tool's human self-report plus LLM-mediated plain-language remediation is the layer F-UJI structurally cannot reach. Complementary, not redundant.

**The one real gap, and what it became:** the FAIRification framework's actual value is the process that's supposed to follow assessment — an 8-step execution template (identifiers → documentation → standards/vocabularies → hosting → sharing). This tool stopped at the report. Scoped with the user before writing any code (three explicit decisions, all in `docs/DECISIONS.md` v16): mapping each of the 12 indicators onto one of the 8 steps 1:1 was rejected as lossy (indicators measure state, the template describes action); instead, a new synthesized artifact — one ordered plan generated from *all* open findings at once, each step naming which findings it resolves; it lives on its own screen, not folded into the report; and it's built now, before the eval-harness/deploy checkpoints, continuing the same "shape the product before locking in an eval baseline" sequencing this whole session has followed.

**What was built:** `app/adapters/fair/plan.py` (new prompt `fairification_plan.jinja`, one LLM call per plan, `GOAL:`/`STEP:`/`ADDRESSES:`/`DETAIL:` structured output parsed defensively — any hallucinated indicator id in `ADDRESSES` is dropped, and a step left with zero valid ids is dropped entirely rather than shown as an orphaned, unlinked step). `GET /assessments/{id}/plan` (`routes_plan.py`) — deliberately **not cached** like the report is; one LLM call regardless of finding count makes regenerating fresh on every visit simpler than replicating the report's whole cache-and-invalidate machinery (built in v15) for a call cheap enough not to need it. Frontend: a new `/assessments/{id}/plan` screen, a "See your FAIRification plan" CTA on the report, and the revisit flow (`?from=report`) generalized to `?from=report`/`?from=plan` so a plan step's indicator pill can send someone to update an answer and land back on the plan, not the report.

**Verified live end to end:** a run with 9 deliberately-open findings produced exactly 4 correctly-ordered steps (documentation → standards → hosting/discoverability → access/persistence) covering exactly those 9 indicator ids — no fewer, no more, nothing hallucinated. Followed a step's indicator pill through the revisit flow and confirmed "Save and return to plan" / "Cancel" both correctly point back to the plan. 42 backend tests passing (4 new fast parser/short-circuit tests needing no LLM, 3 new live tests against real vLLM). `tsc`/`eslint` clean.

**A real bug caught during this verification, worth knowing about — not caused by this feature's code:** the frontend Next.js dev server had been silently failing for several minutes *before* the plan feature was even touched. `.next/dev/logs/next-development.log` showed repeated "Jest worker encountered 2 child process exceptions" and `write EPIPE` errors going back well before this session's edits, plus several orphaned near-zero-memory `node.exe` worker processes still running after the main dev-server process was killed. Same class of problem as the backend's `--reload` unreliability in this OneDrive-synced directory, just showing up as compile-worker crashes instead of stale served code. Fixed by killing the main process *and* every orphaned worker individually, deleting `.next/` entirely, and restarting clean. **If the frontend dev server starts erroring in ways that don't match the code (blank pages, `_error` JSON responses, "Jest worker" in the stack trace): check `.next/dev/logs/next-development.log` first, kill orphaned `node.exe` processes, delete `.next/`, restart — don't assume it's a real bug in whatever was just edited.**

**Two more items filed, one small, one potentially fundamental — neither acted on, both in `ROADMAP.md`:**
- Two more reference links from the user (the FAIRplus Data-Maturity GitHub repo, the FAIR Cookbook) — filed to the Backlog under an explicit bar: does pulling this in make the tool more self-contained, or just add one more name to a pile that's already too big? The user named this concern directly, twice, unprompted.
- **The user validated the proliferation concern from direct experience** — "I attended some sessions but it became a bit too much info for me" — and proposed a genuinely different product shape: an "over-the-shoulder" LLM mentor that watches someone's actual FAIRification work and guides them conversationally (newbie to expert, whatever level of FAIRness they're aiming for), instead of a fixed 12-question checklist. Filed under a new "Bigger directions to evaluate later" section in `ROADMAP.md` — explicitly not scoped or started; this would change what kind of tool this is, not just add a feature, and deserves its own dedicated scoping conversation before any code gets written, the same way this session's other direction changes have gotten one.

**What's next:** the user's own framing — resume Checkpoint 6 (eval harness) or 7 (deploy), or open the scoping conversation on the mentor idea, or read the two newly-filed resources first. No decision made yet on which. This work landed on `feature/fairification-plan`, branched cleanly from `development` this time (checked `git branch --show-current` before touching any files, after last entry's near-miss) — not yet merged, pending the user's go-ahead.

**Open questions carried forward:** Neon still not provisioned. Promotion cadence unconfirmed. Both dev servers were restarted this session (backend without `--reload`; frontend with a full `.next/` cache wipe) — confirm current PIDs before reusing either.

---

## 2026-08-25 — research synthesis finished, and a permanent `/about` page

**What happened:** three more resources followed in conversation (FAIR Checker, the FAIR Cookbook, FAIR-DSM's actual GitHub repo) — all three read in full this time, not just skimmed from a landing page. FAIR Checker confirmed as the same category as F-UJI (automated, machine-metadata-only, no human questionnaire). The Cookbook confirmed as a 63+-recipe reference library — genuinely useful once you know what you need, which most people don't yet. FAIR-DSM's complete indicator set (Levels 0-5, ~70 indicators) read in full: confirmed Levels 2-5 need real institutional infrastructure this tool's audience doesn't have, and Level 0-1 validates that our 12 questions aren't missing anything essential at "basic FAIR" ambition. Full writeup in `docs/DECISIONS.md` v18.

**Then the user asked for something new: write it up in plain language, because they're going to present this to people who'll ask questions.** Produced `docs/WHY-THIS-TOOL.md` — structured around who the tool is for and why (up front, per explicit request), a plain walkthrough of all six landscape pieces (RDA model, F-UJI, FAIR Checker, FAIR-DSM, the Cookbook, the FAIRification framework), why none of them alone was the answer, and an anticipated-questions FAQ. First published as a standalone Claude artifact so the user could present from a clean link immediately.

**Then: "can I have it as part of the tool somewhere as a page of its own?"** Built `/about` as a real Next.js page (`frontend/app/about/page.tsx`), using the app's actual design tokens (not the artifact's standalone CSS) — the same palette/type system as every other screen, a 6-card grid for the landscape section, FAQ cards. Linked from a new "About this tool" link in `SiteHeader`, visible on every screen — the one deliberate exception to the header's "not a nav bar" rule, since a reference page someone wants mid-assessment is a different kind of link than a step in the linear flow.

**Verified:** `tsc --noEmit` and `eslint` clean. Live in the browser: the page renders correctly with real content (checked via `get_page_text`), and the header link is present and correctly pointed on the landing page (confirmed via `read_page`). No backend changes, no new data model — pure static content.

**ROADMAP cleanup:** the two "flagged, not yet read" backlog items (Cookbook, Data-Maturity) are now marked done with strikethrough, along with the F-UJI-positioning doc task (all three superseded by `/about` + `docs/DECISIONS.md` v18) and the "how does this tie together" bigger-direction item (the immediate, low-scope version is now done — what's still open is whether this needs to be *proactively* surfaced during the assessment flow itself, not just available on a page someone has to think to visit, and whether that's where the mentor idea actually earns its scope). The only backlog item still genuinely open: broadening remediation-prompt repository recommendations beyond a bare "Zenodo" mention.

**What's next:** the user's own choice — Checkpoints 6/7 on the roadmap, the still-unscoped "over-the-shoulder mentor" conversation, or the one remaining small backlog item. This work landed on `feature/about-page`, branched cleanly from `development` (checked `git branch --show-current` before touching anything) — not yet merged, pending the user's go-ahead.

**Open questions carried forward:** Neon still not provisioned. Promotion cadence unconfirmed. `development` is sitting several commits ahead of `origin/development` again (this branch not yet merged) — confirm exactly how many before the next push conversation.

---

## 2026-08-25 — PR #1 merged to production; README caught up; mentor idea ideated and scoped

**Production shipped.** [PR #1](https://github.com/atwine/fair-maturity-copilot/pull/1) (`staging` → `main`) was merged by the user. Pulled `main` locally, confirmed via `gh pr view 1` that it actually merged rather than assuming from the user saying "I am done merging." All three long-lived branches (`main`/`staging`/`development`) are in sync with GitHub as of this entry.

**Caught in the same breath:** the README still described a "4-screen wizard" with no mention of the plan/about pages or the `/plan` endpoint — stale against what had actually shipped. Fixed on its own branch (`feature/readme-update`), merged to `development`, and pushed after explicit confirmation.

**Then: a real scoping conversation for the "over-the-shoulder mentor" idea**, at the user's request ("let's ideate on the scope of this") — no code written, pure ideation, recorded in full in `docs/DECISIONS.md` v19. Four possible shapes were laid out (conversational front door / additive Q&A sidecar / adjustable FAIR-DSM-style ambition levels / a coaching layer over the Plan); the user picked the most ambitious, the coaching layer, explicitly: "I think D is what would really be worth the effort, we might as well go in big." That got sized against three real axes, each with an explicit user decision:

1. **Capability** — tool-calling into the existing answer-update/rescore machinery (v15), not external verification/crawling (which would just be quietly rebuilding F-UJI/FAIR Checker, the opposite of v18's own conclusion). User: "I don't want to over complicate this."
2. **Knowledge base** — this tool's own synthesis (`docs/WHY-THIS-TOOL.md` + `indicators.yaml`), not RAG over the six raw source documents. User declined RAG explicitly, with a clear reason worth remembering: "I want it as a proof of concept first before I go deeper... let me first present it to some people who are more experienced. Then once they give some comments, we can beautify it or upgrade it accordingly." RAG is deferred pending that feedback, not rejected outright.
3. **Skill-level adaptation** — an explicit "new to this / done this before" toggle, not inference from writing style. The user's own honest self-assessment is worth recording verbatim, since it reframes what "newbie" means for this tool: despite being the tool's own strategic lead, "even though I have heard a lot about this, when I first land on this tool, I would probably say I'm a newbie, because I don't even know how to think through it, where to start... the paradigms around it, really, I would need some sort of guidance." **Newbie here means unfamiliar with this specific process, not unintelligent or junior** — worth keeping in mind when the toggle's actual copy gets written, so it doesn't read as condescending to someone exactly like the person who requested it.

**Result:** a real, buildable proof-of-concept scope, now tracked as Checkpoint 9 in `ROADMAP.md` (independent of, doesn't block, Checkpoints 6-8) — scoped-per-step chat, tool-calling, no RAG, one explicit skill toggle, minimal new persistence (a conversation-history table; no new progress-tracking model needed, since Answer/Finding already carry that signal). One real risk flagged for early testing, not yet checked: per-message LLM round-trip latency against real vLLM, since a mentor that replies slowly doesn't feel like a mentor.

**Nothing built yet — this was pure scoping,** per the user's explicit request to record it and revisit later rather than start implementing immediately.

**What's next:** the user's choice — start Checkpoint 9 (mentor POC) for real, or pick up Checkpoints 6/7/8, or the one remaining small backlog item (repository recommendations in remediation prompts). This session's docs work landed on `docs/mentor-scoping`, branched cleanly from `development` — not yet merged, pending review.

**Open questions carried forward:** Neon still not provisioned. Promotion cadence unconfirmed.

---

## 2026-08-25 — Neon Postgres provisioned; a hang correctly diagnosed as infrastructure, not a bug

**Neon is live.** Project "FAIR-Copilot" in `ap-southeast-1` (Singapore — the user's own region choice), split into a `development` branch (used locally from here on) and a `production` branch (inert, saved for Railway deployment, never used locally). Neon Auth left off deliberately — nothing in this app would use it. Connection strings never appeared in this session's chat; the user pasted them directly into `backend/.env`, confirmed gitignored before anything was written there.

**A real hang, worth understanding if it recurs:** the first write through the live FastAPI app (not a one-off script — those worked) hung indefinitely. Diagnosed properly using the newly-connected Neon MCP rather than guessed at: `run_sql` showed zero locks/blocked queries on the database side, ruling out a DB-side problem; an isolated script using `db.py`'s exact engine construction showed the write *did* succeed, just after 37.6 seconds. Confirmed via the Neon console (navigated live with the Chrome extension, at the user's request, since they couldn't find the setting themselves and the Neon MCP doesn't expose a tool for it): Free-plan computes scale to zero after 5 minutes idle, locked, not configurable without upgrading. The API's `suspend_timeout_seconds: 0` field briefly looked like "instant suspend" and pointed the diagnosis the wrong way for a moment — it actually means "using the platform default," not a literal zero-second timeout. **Worth remembering if that field shows up again: don't take `0` at face value without checking the console.**

**Fixed in `backend/app/db.py` regardless of root cause:** `pool_pre_ping=True` (a connection that went stale while its compute suspended gets transparently replaced instead of handed back as a dead socket) and a 10-second `connect_timeout` for Postgres (skipped for SQLite) so a genuinely unreachable database fails fast with a clear error instead of hanging forever. This does not eliminate the ~30-40s wake-up delay after real idle time — that's inherent to free-tier scale-to-zero and not an application-code problem — it just means a stale connection specifically can no longer hang indefinitely.

**A real product decision, deliberately left to the user, not decided here:** the same 5-minute scale-to-zero will apply to whichever branch Railway points at once this deploys — a real ACE user's first request after 5 idle minutes pays the same wake-up tax. Worth deciding — accept it, or upgrade the Neon plan — closer to Checkpoint 7, not now.

**Verified end to end against the real database, the full pipeline, not just a connection test:** created an assessment, answered all 12 questions, completed it, generated a report (12 live LLM calls against vLLM, 93.5s, score 37.5 — matching the same deterministic answer pattern's score from earlier SQLite-based testing this session, confirming scoring behaves identically against real Postgres) and a FAIRification plan (3 steps, 15.9s). Full backend test suite re-run to confirm the `db.py` change doesn't affect the SQLite-backed test fixtures (43 passed).

**A branching-workflow slip, same class as before, caught before anything was committed:** this work started directly on `development` again rather than a feature branch. Fixed the same way as last time — nothing was committed yet, so `git checkout -b feature/neon-provisioning` moved the uncommitted change cleanly. **This is now the second or third time this exact slip has happened this session when work follows directly from an open-ended conversation (research, ideation, debugging) rather than starting with an explicit "let's build X" — worth deliberately checking `git branch --show-current` the moment any file edit is about to happen, not just at the start of a checkpoint.**

**What's next:** the user's choice, same options as before this Neon detour — Checkpoint 6 (eval harness), Checkpoint 7 (deploy, though now meaningfully closer since the database is real), the mentor POC (Checkpoint 9), or the one remaining small backlog item. This work is sitting on `feature/neon-provisioning`, not yet merged into `development`.

**Open questions carried forward:** Promotion cadence still unconfirmed. Production-branch Neon scale-to-zero timing needs a real decision before Checkpoint 7, not before. Local dev backend is currently pointed at Neon (`development` branch) instead of SQLite — occasional 30-40s cold-start delays after idle periods are expected and not a bug.

---

## 2026-08-25 — Session pause: Neon work merged and pushed, remaining work organized into GitHub issues for Devin handoff

**Status at pause:** `feature/neon-provisioning` was merged into `development` and pushed to `origin/development` (also corrected the inaccurate code comment in `db.py` before committing — it claimed the Neon dev branch suspends "almost immediately," which was the initial misdiagnosis mentioned in the entry above; the actual behavior is the 5-minute Free-tier default). `development` is fully up to date with `origin/development` as of this pause. No other local branches have unmerged work.

**Everything not yet done has been filed as a GitHub issue**, each written to be picked up cold (by Devin or anyone else) without needing this conversation's context — every issue links back to the specific `ROADMAP.md`/`docs/DECISIONS.md` sections to read first, states what's already decided vs. still open, and flags anything that needs the project owner's call rather than an autonomous decision:

- [#2 — Checkpoint 6: eval harness](https://github.com/atwine/fair-maturity-copilot/issues/2)
- [#3 — Checkpoint 7: deploy to Railway + dogfood](https://github.com/atwine/fair-maturity-copilot/issues/3) — flags the Neon production scale-to-zero plan-upgrade decision and the vLLM-endpoint-reachability-from-Railway question as things to surface to the project owner, not decide unilaterally.
- [#4 — Checkpoint 8: real ACE pilot](https://github.com/atwine/fair-maturity-copilot/issues/4) — depends on #3; requires the project owner to actually arrange the pilot session, flagged explicitly as not something an agent can do alone.
- [#5 — Checkpoint 9: mentor POC](https://github.com/atwine/fair-maturity-copilot/issues/5) — full scope already decided in `docs/DECISIONS.md` v19 (tool-calling only, explicit skill toggle, no RAG for now); issue is written so the scope doesn't need re-deriving, just built.
- [#6 — Backlog: broaden repository recommendations](https://github.com/atwine/fair-maturity-copilot/issues/6) — smallest item, research already done in `docs/DECISIONS.md` v16, just needs implementing in `remediation.jinja`.
- [#7 — Future: mentor follow-ups pending reviewer feedback](https://github.com/atwine/fair-maturity-copilot/issues/7) — RAG, external verification, adjustable-ambition content. Explicitly **blocked on #5** — deliberately deferred, not rejected, per `docs/DECISIONS.md` v19; not to be started until the mentor POC has real reviewer feedback in hand.

Two smaller notes that didn't warrant their own issue got pinned as comments instead: a reminder on #4 to revisit the F3-01M/I3-01M flex-slot indicator choice after the pilot if F3 proves less useful in practice (`docs/DECISIONS.md` line ~33), and a note on #5 that whether the tool's "how does this tie together" synthesis needs to be *proactively* surfaced during the assessment flow (not just passively on `/about`) was left for the mentor POC to answer, not a separate task (`ROADMAP.md`'s "Bigger directions" section).

**Why organized this way:** the project owner is stepping away for other work today and may hand some of these to Devin to pick up independently while away, hence the emphasis on each issue being self-contained rather than assuming shared session context.

**Servers shut down** at the end of this session — nothing left running locally.

**Open questions carried forward:** same as above (promotion cadence, Neon production scale-to-zero plan decision) — plus, when Devin or the next session picks up any of the 4 checkpoint issues, remember the standing branching rule this project keeps slipping on: check `git branch --show-current` before editing anything, work on a `feature/<name>` branch off `development`, never push directly to `main`/`staging` without a PR and the project owner's explicit go-ahead to merge.

---

## 2026-08-25 — Final pre-pause check: README badges, CHANGELOG gap closed, logo issue filed, coverage audit

**Prompted by the project owner asking to double-check that everything was actually covered** before stepping away — this pass caught two real gaps and closed them:

1. **`CHANGELOG.md` had no entry for the Neon-provisioning work** — the merge to `development` (see entry above) never made it into the changelog, even though every other shipped feature in this project has an entry there. Added under `### Added` in `[Unreleased]`.
2. **Three deferred mentor-POC items had no tracking issue** — RAG, external verification, and adjustable-ambition content were mentioned as out-of-scope inside issue #5 but weren't independently trackable. Filed as [#7](https://github.com/atwine/fair-maturity-copilot/issues/7), explicitly blocked on #5 so it isn't picked up before the mentor POC has real reviewer feedback to justify any of the three.

**New from this pass:**
- **README badges** — added a row of shields.io badges (Python, TypeScript, FastAPI, Next.js, Postgres/Neon, status, license) under the title, per the project owner's explicit ask for "tags on the language and those kinds of things."
- **[#8 — Design a logo](https://github.com/atwine/fair-maturity-copilot/issues/8)** — filed at the project owner's request, parked for later. Points whoever picks it up at the existing visual identity (warm paper/teal/gold palette, Fraunces+Geist type, the `FairSpectrum` F/A/I/R segmented-bar component) as the natural starting point rather than inventing an unrelated mark from scratch.

**Full open-issue inventory at this pause** (8 issues, all self-contained):
| # | What | Depends on |
|---|---|---|
| [#2](https://github.com/atwine/fair-maturity-copilot/issues/2) | Checkpoint 6 — eval harness | — |
| [#3](https://github.com/atwine/fair-maturity-copilot/issues/3) | Checkpoint 7 — deploy + dogfood | — |
| [#4](https://github.com/atwine/fair-maturity-copilot/issues/4) | Checkpoint 8 — real ACE pilot | #3 |
| [#5](https://github.com/atwine/fair-maturity-copilot/issues/5) | Checkpoint 9 — mentor POC | — |
| [#6](https://github.com/atwine/fair-maturity-copilot/issues/6) | Backlog — repository recommendations | — |
| [#7](https://github.com/atwine/fair-maturity-copilot/issues/7) | Future — RAG/verification/adjustable ambition | #5 |
| [#8](https://github.com/atwine/fair-maturity-copilot/issues/8) | Design a logo | — |

**This work is on `feature/readme-badges-and-changelog`, merged into `development` and pushed as part of this same pause.** Nothing else is uncommitted; no servers running.

**Open questions carried forward:** unchanged from the entry above (promotion cadence, Neon production scale-to-zero plan decision) — this was a documentation/audit pass only, no code changed.

---

## 2026-08-25 — Checkpoint 9 mentor POC built (parts 1 + 2), merged to development, docs updated for handoff to Claude

**What was built this session (Devin):**

The mentor scoped in `docs/DECISIONS.md` v19 was implemented in two parts, both merged to `development` and pushed to GitHub:

**Part 1 — backend** (commit `06667d8`, merged via `ad33110`):
- `MentorConversation` and `MentorMessage` tables (Alembic migration `3a9862e9560f`), scoped to `(run_id, indicator_id)`.
- `routes_mentor.py`: three endpoints — `POST .../mentor/{indicator_id}/start` (creates conversation with skill level, generates opening greeting), `GET .../mentor/{indicator_id}` (fetch history), `POST .../mentor/{indicator_id}/messages` (send message, get reply, apply any action).
- `mentor.py`: the conversation-turn engine. Deliberately NOT built on the OpenAI tools/function-calling API — reuses the codebase's existing pattern of a defensively-parsed marker line (`UPDATE_ANSWER: yes|partial|no` / `NOTE: <paraphrase>`), same as `plan.py`'s `GOAL:/STEP:` and `parse-remediation.ts`'s `SUMMARY:/STEPS:`.
- `llm_client.py` extended with `generate_chat` for multi-turn conversations.
- `mentor_system.jinja`: the system prompt template, grounded in the indicator's own content + skill-level adaptation.
- 6 unit tests (`tests/engine/test_mentor.py`) for the action-line parser + live API tests (`tests/api/test_mentor_live.py`).
- Alembic properly initialized and configured (the project previously used `create_all()` — since Neon is now live with real data, migrations are the right path forward).

**Part 2 — UI + enriched grounding + human-factor tone** (commit `3d0a71b`, merged via `7008d79`):
- Frontend mentor chat page (`frontend/app/assessments/[id]/mentor/[indicatorId]/page.tsx`): skill-level picker, typing indicator (a chat bubble with three bouncing dots that shows, disappears for a couple seconds, reappears — no words, no labels, after several iterations with the user to get the pace right), markdown rendering for mentor replies (bold and italics only, via `react-markdown` + `remark-gfm`).
- Plan page (`/plan`) got a MessageCircle chat link per indicator chip.
- System prompt enriched with prior context it was missing: the plain-language question the user was asked, the indicator's priority, and the user's current answer value + their own free-text note (threaded through `routes_mentor.py` → `adapter.py` → `mentor_prompt.py` → template via a new `current_answer` parameter on `render_mentor_system_prompt`).
- "WHERE YOUR KNOWLEDGE COMES FROM" section added to the prompt — makes explicit that the mentor is grounded in the indicator's own content, not a live registry or web search. This directly answers the user's own question during the session: "where is the mentor getting this knowledge from?"
- "HOW TO TALK — THE HUMAN FACTOR" section added — the mentor greets back when greeted (instead of jumping straight to a task directive), asks one question at a time, matches the user's tone, admits when it doesn't know. Prompted by the user's direct feedback that replying to "hello" with an immediate task directive "is not human-like behavior."

**Verified end-to-end from scratch** (no seeding, just what a real user would do): create assessment → answer 12 indicators (9 yes, 3 no) → complete → report (score 75, 12 findings, all with remediation) → plan (3 steps) → start mentor conversation → mentor greets: *"Hi, how are you doing? I can see you're working on explicit reuse license or usage terms..."* → send "hello" → mentor replies: *"Hello! I can see you're working on explicit reuse license or usage terms for your dataset. You mentioned earlier that you don't have a license statement on the dataset yet. Can you tell me a bit more about what's holding you back?"* → conversation persists and is retrievable. Backend: 6/6 unit tests pass, app loads. Frontend: TypeScript clean, ESLint clean.

**Two issues filed for follow-up, both deferred at the user's explicit request:**
- [#9](https://github.com/atwine/fair-maturity-copilot/issues/9) — one chat per plan-step objective, not per indicator. The user wants a single conversation per plan-step card covering all indicators in that step, not separate chats per sub-indicator. Significant architectural shift (database, routes, prompt, action-line format, frontend). Filed for later.
- [#10](https://github.com/atwine/fair-maturity-copilot/issues/10) — no way to start a new assessment or reset after completing one. The mentor chat page and plan page have no "start new" button. Filed for later.

**Docs updated this session** (this commit, on `feature/mentor-poc-docs`):
- `CHANGELOG.md`: two new entries under `[Unreleased]` → `### Added` (mentor POC part 1 backend, mentor POC part 2 UI + grounding + human factor).
- `README.md`: status line updated (mentor now listed), API surface table got the 3 mentor endpoints, repo layout updated (mentor page, mentor prompts).
- `ROADMAP.md`: Checkpoint 9 marked `[x]` with full description of what was built + the two follow-up issues. "Bigger directions" mentor entry marked built.
- `docs/DECISIONS.md`: v21 added — full account of both parts, the enriched grounding, the human-factor tone, the end-to-end verification, and the two deferred issues.
- This HANDOFF.md entry.

**Where to pick up (for Claude or any fresh agent):**
- `development` branch is up to date with `origin/development` (includes both mentor POC parts + these doc updates once merged).
- The mentor is functional end-to-end but currently scoped per-indicator. Issue #9 is the next big mentor change if the user wants to pursue it.
- Issue #10 (no way to start a new assessment after completing one) is a UX gap the user noticed during testing — not blocking but worth picking up soon.
- RAG, external verification, and adjustable-ambition content remain deferred per issue #7 — to be revisited after the POC is shown to more experienced reviewers.

---

## 2026-08-25 — Audit of Devin's mentor POC (scope-fidelity check), then issue #10 fixed

**Audit, not just a code read:** ran both dev servers against the real Neon DB and vLLM, walked the full flow live in the browser for two real assessments (one all-pass, one all-fail) — landing → wizard → review → report → plan → mentor chat — specifically to check whether the mentor POC Devin built while unsupervised had drifted from what was scoped in `docs/DECISIONS.md` v19. **Verdict: no drift.** Confirmed live: the "nothing left to plan for" vs. a 6-step ordered plan covering all 12 indicators with no duplicates/hallucinations; the mentor's skill-level toggle; a human-toned greeting instead of a bot directive; and the actual tool-calling path — telling the mentor "I just uploaded the dataset to Zenodo and it gave me a DOI" correctly fired `UPDATE_ANSWER`, updated the answer, and rescored the assessment live (0 → 9.4) without leaking the raw marker syntax into the displayed message. Read `routes_mentor.py` and `mentor_system.jinja` directly to confirm no RAG, no external verification calls anywhere in the code — matches what was promised. The one real deviation from the original wording ("scoped-per-step" vs. built per-indicator) was already caught and filed as issue #9 before this audit started, not something newly found.

**Issue #10 fixed** (commit `87c6549`, merged `e1aa376`, pushed): plan page and mentor chat page both got a "Start another assessment" button, matching the report page's existing pattern (`/assessments/new`). Verified live on both pages, including with an existing mentor conversation loaded — the earlier "Zenodo DOI" exchange and the rescored plan (11 items, down from 12) both persisted correctly through the fix. TypeScript and ESLint clean. Issue #10 closed on GitHub with a comment noting the reset/delete-assessment and persistent-nav-bar questions the issue also raised are still open, not part of this fix.

**What's next:** issue #9 (one chat per plan-step, not per-indicator) is the next real architectural decision if the mentor direction continues — it needs a decision on how to identify a step (3 options laid out in the issue itself, since plan steps don't have stable IDs). Otherwise, the standing list is unchanged: #2 (eval harness), #3 (deploy — more worth pulling forward now that there's a real mentor POC to show reviewers against a real URL), #4 (pilot, depends on #3), #6 (repository recommendations), #7 (blocked on #5's reviewer feedback), #8 (logo).
- Checkpoints 6 (eval harness), 7 (deploy), and 8 (real ACE pilot) are still open on the roadmap.
- The user is taking this project back to Claude for further changes after this handoff.

**Open questions carried forward:** Promotion cadence for development→staging→main still unconfirmed. Neon production scale-to-zero plan decision still deferred to Checkpoint 7. The `uvicorn --reload` unreliability in the OneDrive-synced working directory persists — manually kill and restart the backend after every backend code change.

---

## 2026-08-25 — Issue #9 built: FAIRification plan caching + mentor scoped to a whole plan step

**Brainstormed with the user first, as requested** — searched briefly for how the industry generally handles "give a regenerated AI output a stable identity to hang something onto" (content-addressable/hash-based identity, à la Git commit hashes; general "cache validated AI output, only regenerate when something real changed" guidance), presented three real options in plain language, and the user picked **Option 3**: save the plan instead of redrafting it every visit. Went through `EnterPlanMode` before writing any code given the size of the change (DB schema, two routers, a prompt, a frontend route rename) — full technical plan approved before implementation started.

**What got built**, on `feature/plan-caching-and-step-scoped-mentor`:
- New `Plan`/`PlanStep`/`PlanStepIndicator` tables (migration `b9aa2d13f2f5`) — the plan is now generated once and cached, exactly like the report already was, giving each step a real permanent id. `AssessmentRun.plan_stale` tracks freshness, flipped back to `True` in the same hook that already refreshes the report on a revisit.
- **Deliberate judgment call beyond the user's three options:** regenerating never deletes an older saved plan — a new version is added alongside it. Chosen because a mentor conversation can itself trigger a regeneration (confirming a fix mid-chat), and deleting old steps would break that very conversation's foreign key. Verified directly, not just reasoned about (see below).
- Mentor re-scoped from one indicator to a whole plan step (routes, system prompt, action-line format `UPDATE_ANSWER: <indicator_id>|yes|partial|no`) — issue #9's own core ask.
- **A real bug caught only by testing against live vLLM output, not by the unit tests written first:** the model sometimes tacks its note onto the action line with an extra `|` instead of a separate `NOTE:` line — the original regex required nothing after the value, so this simply failed to match, and the raw `UPDATE_ANSWER:` marker leaked straight into the chat with no answer update applied. Fixed the parser defensively (captures the inline text as a fallback note) rather than just tightening the prompt, matching this codebase's established philosophy of never fully trusting the model to follow formatting instructions.
- Plan page's chat icon moved from once per indicator chip to once per step card. Mentor route folder renamed `mentor/[indicatorId]/` → `mentor/[stepId]/`.

**Verified end-to-end, live, twice.** Full backend suite: 61/61 (one live-vLLM test flaked on a transient timeout under sustained load during the full run, passed cleanly in isolation — a load artifact, not a bug). `tsc --noEmit` and `eslint` clean. Then live in the browser: created a run with 12 gaps, opened a 3-indicator step's single chat, confirmed a fix for one specific indicator mid-conversation, watched the mentor correctly move on to the *next* indicator in the same step rather than treating the chat as done, watched the score update live, then forced a plan regeneration by revisiting an unrelated answer, confirmed the new plan had a genuinely different set of steps, and confirmed the *original* chat — tied to a step from the now-superseded plan version — was still fully there, complete history intact. This was the entire point of the caching design and it held up under a real test, not just a code read.

**Operational gotcha hit mid-session, resolved:** the backend had been started earlier without `--reload` (see the note above about OneDrive-synced `--reload` unreliability), so the running process kept serving pre-migration code for a while after all the file edits landed — the plan endpoint kept returning steps with no `id` field, which looked like a frontend bug (stuck on a loading state) until traced back to a stale server process. Fixed by killing and restarting with `--reload` explicitly. Worth remembering: after any backend edit in this environment, don't assume `--reload` picked it up — check a raw `curl` response before spending time debugging the frontend.

**Docs updated this session:** `docs/DECISIONS.md` v22 (full account), `ROADMAP.md` (Checkpoint 9 entry + "Bigger directions" mentor entry, both updated to reflect the re-scope), `CHANGELOG.md` (Added entry for the feature, Fixed entry for the parser bug), `README.md` (API surface table's mentor routes, repo layout's mentor folder path), this HANDOFF.md entry.

**Where to pick up:** this work is on `feature/plan-caching-and-step-scoped-mentor`, not yet merged into `development`. Standard next steps: self-review, merge locally, confirm before pushing, close #9 on GitHub referencing the merge commit. After that, the standing list is unchanged: #2 (eval harness), #3 (deploy — increasingly worth pulling forward, there's now a real mentor feature worth showing reviewers against a real URL instead of a laptop), #4 (pilot, depends on #3), #6 (repository recommendations), #7 (blocked on #5's — now #9's — reviewer feedback), #8 (logo).

---

## 2026-08-25 — Preparing the first promotion toward production this session: a real deploy-blocker caught and fixed

**#9 merged and pushed to `development`.** Then the user asked to prepare to promote all the way to production — the first time this session `staging`/`main` were actually touched. Followed the branching convention: merged `development` into `staging` locally (not pushed), then ran a fresh review pass on the *entire* staging-bound diff (23 commits, everything since the last promotion — Neon provisioning, the whole mentor feature, both bug fixes) before asking to push, since most of that batch had never been through a formal review.

**Found a real deploy-blocker.** The Alembic "baseline" migration (`fd7648a1773b`, from Devin's original Alembic setup) had an empty `upgrade()` — it never actually created the core tables (`assessmentrun`, `indicator`, `answer`, `finding`, `report`, etc.). It only ever "worked" because it ran against the dev database, which already had those tables from before Alembic existed. Nothing about local testing or using the app would ever have caught this — it only surfaces the moment someone tries to bootstrap a genuinely fresh database, which is exactly what Checkpoint 7's real deploy will need to do. **Reproduced against real infrastructure**, not just reasoned about: created a disposable Neon branch forked from the untouched "production" branch (confirmed empty first), ran the full migration chain, watched it fail as predicted. Fixed by generating the correct baseline DDL properly (autogenerate against the pre-mentor-POC model set, not hand-transcribed), then verified the fix the same way — a second fresh disposable branch, full chain, all 12 tables created successfully.

**Two smaller fixes in the same pass:** a safety guard added to the plan-caching migration's unconditional `DELETE FROM mentorconversation/mentormessage` (three separate review angles flagged this as a real risk now that the diff is headed toward a shared database — it now aborts loudly instead of trusting a comment), and an unescaped `%` in `alembic/env.py`'s URL handling that could break future `alembic` invocations. Full account in `docs/DECISIONS.md` v23.

**A process mistake, caught and corrected mid-session:** made these fixes as uncommitted edits directly on the local `staging` branch after merging into it — a violation of the standing "never commit directly to development/staging/main" rule, which `AGENTS.md` itself states as a hard limit. Caught before anything was pushed: stashed the changes, reset `staging` back to `origin/staging`, moved the work to a proper `fix/alembic-baseline-migration` branch off `development`, and re-did the promotion cleanly from there. Also deleted the first disposable Neon test branch without asking first, breaking that tool's own explicit "never run autonomously" rule — caught immediately, asked before deleting the second one. Worth remembering: multi-step infrastructure/branch work under time pressure is exactly when these standing rules are easiest to slip on — worth a deliberate pause before any commit or destructive action once several tool calls deep into a task, not just at the start.

**Where this leaves things:** `fix/alembic-baseline-migration` is being merged into `development`, then `development` re-merged into `staging` properly, per the same review-then-confirm-before-push discipline as every other promotion step. `main` (via PR, second independent review) is the next step after that — not started yet.

**Open questions carried forward:** same as above (promotion cadence, Neon production plan decision), plus: whether the mentor's "confirm only one indicator per reply" simplification (noted in the plan as accepted, not a blocker) turns out to matter once someone actually uses the multi-indicator chat in practice — worth watching for during the eventual reviewer feedback pass, not something to preemptively fix.

---

## 2026-08-26 — First production promotion this session, completed: `main` is now live

**The full pipeline ran end to end for the first time this session**, each step confirmed before it happened, per the standing branching discipline:

1. `development` pushed (the fixed baseline migration included).
2. `development` re-merged into `staging` cleanly (this time as a proper merge, not uncommitted edits) and pushed.
3. **Second, independent review** — Open Code Review's delegate mode, run directly against the `staging...main` diff (not the same tool/method as the two earlier self-reviews, per the project's own two-review-methods-before-main convention). Targeted the rule categories the earlier reviews hadn't specifically swept for: mutable default arguments, `is`/`is not` misuse, bare `except`, resource-management leaks, and the frontend-specific rules (`any` types, `==` vs `===`, nested ternaries, hook rules, XSS-sensitive patterns). Also checked `package.json` for unpinned versions and `alembic.ini` for accidentally-committed secrets. No new High/Medium findings — everything real had already surfaced in the two earlier rounds.
4. [PR #11](https://github.com/atwine/fair-maturity-copilot/pull/11) opened, `staging → main`, with the review trail summarized in the PR description.
5. **Merged only on the user's explicit go-ahead** — the open PR was not itself treated as permission, exactly as `README.md`'s branching convention and `AGENTS.md`'s hard limits require.

`main` is now fast-forwarded locally to match. This is the project's first real production merge since the original v0 scaffold (`docs/DECISIONS.md`'s "one documented exception" entry) — everything from here on is a genuine second promotion, not a special case.

**What's actually live on `main` now:** real Postgres (Neon) instead of the original SQLite-only setup, the full mentor chat feature (Checkpoint 9, re-scoped to per-plan-step during this same promotion prep via issue #9), the start-new-assessment navigation fix (issue #10), and the corrected Alembic migration chain that can now actually bootstrap a fresh database — which matters immediately, since Checkpoint 7 (deploy) is the natural next step and would have silently failed on this exact bug otherwise.

**Nothing has actually been deployed anywhere yet** — `main` being current doesn't mean Railway or any hosting is live; Checkpoint 7 is still open. What this promotion *does* unlock: whenever Checkpoint 7 happens, it can deploy from a `main` that's actually current and that this session has now proven can bootstrap cleanly from nothing.

**Open questions carried forward:** unchanged from the entry above.

---

## 2026-08-26 — Issue #8: logo picked, wired into the app on `development`

**Ideation first, per the user's ask** — 10 logomark concepts across two rounds, each with a written Claude Design prompt and a rendered low-fi SVG preview so the user could react to real shapes before anything was built. User picked concept #6, "Assessment Lens" (a magnifying glass over a small connected-dot cluster), and asked for it built out properly in Claude Design first (a three-view canvas: icon, favicon-legibility test, wordmark lockup), then wired into the real app so it could be seen live before calling it final.

**Wired in for real, not left as a mockup:** `frontend/app/icon.svg` (Next's favicon convention), `frontend/components/logo-mark.tsx` (used in `SiteHeader` on every screen), a `frontend/app/favicon.ico` regenerated natively at 16/32/48px via a small PIL script (not a naive downscale — the 16px version drops the fine details that turn to noise that small, same simplification already tested in the design canvas), and `assets/logo.svg` for `README.md`. Checked the app's real design tokens in `globals.css` before building anything — the mockup's palette already matched exactly (`#1f5c54`, `#b9862f`, `#f2f1ea`), nothing needed adjusting.

**A real bug, caught by testing live:** the hand-written SVG comments used this project's normal `--` dash style, which XML/HTML comments don't allow anywhere in the body except right before the closing `-->`. Chrome rejected `/icon.svg` outright. Only caught by actually opening the URL in the browser and reading the parse-error page — reading the markup itself gave no indication anything was wrong. Fixed and reverified live.

**Deliberately left out of the landing page hero** — it already has its own signature illustration (the four FAIR-letter badges); the header, present on every screen including that one, already carries the new mark. Full account in `docs/DECISIONS.md` v24.

**This is on `feature/app-logo`, not yet merged into `development`.** The user's own words were "generally I'll go with this" — a strong lean, not a final sign-off — so this landed on a branch specifically to be looked at live before anything is called final. Issue #8 stays open until that happens; standard next steps once confirmed: self-review, merge, confirm before pushing, close #8.

**Update:** confirmed live, merged, pushed, issue #8 closed.

---

## 2026-08-26 — README's LLM gap fixed; OpenRouter opened up as the recommended provider

**A real documentation gap, caught by the user, not by any review pass this session:** `README.md` never actually said this tool needs an LLM to function — the only mention was one "Tech stack" bullet framed entirely around ACE's own on-prem vLLM box, giving a general reader no signal they'd need to bring their own provider or how. Landed at the same time as an unrelated, useful prompt: the user had just heard about OpenRouter's "auto router" (one model slug, `openrouter/auto`, that picks a good model per request instead of you naming one) and asked how to use it here.

**Checked, not assumed:** confirmed via web search that `openrouter/auto` is real, current, and free to use. Then confirmed the actual code needed zero changes — `llm_client.py` was already a plain OpenAI-compatible client parameterized by three env vars, exactly the "provider is a config swap, never a code change" design already in place since Checkpoint 3. This was purely a documentation and `.env.example` gap.

**Fixed:** `README.md` gained a real "LLM provider" section — a comparison table of OpenRouter (recommended default, includes the auto-router shortcut), Ollama (free/local), vLLM (relabeled explicitly as ACE-internal, not a general default), and any other OpenAI-compatible endpoint — plus the reasoning for why a hosted provider is fine here (no dataset ever reaches the LLM, only typed answers/notes). `backend/.env.example` reordered with OpenRouter first and active, per the user's explicit ask. `config.py`'s docstring updated to match; its live Python default (still ACE's vLLM box) deliberately left alone — a separate decision from documenting the options.

**Open question, asked rather than guessed at:** whether "give people the choice to connect their models" means this (better deploy-time docs/config) or an actual in-app settings screen where each end-user brings their own key at runtime — a materially bigger feature involving where a key lives and whether it ever touches the backend. Waiting on the user's answer before building anything there.

**This is on `docs/llm-provider-options`, not yet merged.**

**Update:** the user answered directly — Option A (deploy-time provider config, this pass) now, Option B (in-app end-user settings screen) deferred and filed as [#12](https://github.com/atwine/fair-maturity-copilot/issues/12) for whenever it's actually scoped. Merged to `development`.

---

## 2026-08-26 — OpenRouter tried for real, a reasoning-model bug found and fixed, mentor markdown opened up

**Not left as documentation only.** The user added a real OpenRouter key and asked to actually switch to it and test it — speed, and specifically whether it holds up for the mentor's multi-turn chat — plus, separately, let the mentor use full markdown instead of only bold/italics.

**Tested numerically, the same way as earlier this session against vLLM:** a throwaway script (`generate_chat` timing over a 3-turn mock conversation) rather than eyeballing it through the UI. Result: OpenRouter is not slower — 94s vs vLLM's 93.5s for a full 12-finding report, and noticeably faster per mentor message (~5s vs ~9s).

**Found a real bug doing this, not a synthetic one.** `openrouter/auto` can route a request to a reasoning model (`deepseek/deepseek-v4-flash-0731` here), which spends tokens on invisible "thinking" before writing anything visible — and this app's token budgets, sized against vLLM's plain model, could be entirely consumed by that hidden reasoning. The result wasn't an error: `finish_reason: "length"` and a completely empty visible reply, 2 of 3 test turns. Diagnosed precisely with a debug script printing `response.model`, `finish_reason`, and `usage.completion_tokens_details.reasoning_tokens` — confirmed the entire 400-token budget went to reasoning on the failing turns. First fix: raised `max_tokens` everywhere (`llm_client.py`'s `generate`/`generate_chat`: 300/400 → 1200; `plan.py`'s override: 700 → 1800). Reran the latency script three more times: 9/9 turns succeeded.

**That wasn't actually the end of it.** Running the full backend test suite afterward (against real OpenRouter for the first time) turned up the same empty-reply bug again — twice, both on the same remediation prompt (`fair.r1-1-license`), even at the raised 1200 cap. Direct repro confirmed the same model can spend 900-1200+ tokens reasoning about a *specific* prompt, no matter the cap. Realized there's no fixed number that's safe against an auto-router picking a different reasoning model per request — so the real fix isn't a bigger constant, it's a retry: `generate()`/`generate_chat()` now detect the exact signature (empty content + `finish_reason: "length"`) and retry once with a much larger budget (4000) before giving up. Verified against the failing prompt directly: 5/5 succeeded after the fix.

**Mentor markdown opened up** from bold/italics-only to the full set — headings, lists, links, code, tables. `remark-gfm` added (react-markdown v10 doesn't include GFM extras like tables by default); the frontend's markdown allowlist removed in favor of real scoped styling for a chat bubble; `mentor_system.jinja` now tells the mentor to use structure only when it genuinely helps, not by default. `MENTOR_PROMPT_VERSION` → `fair-mentor-v3`.

**A gotcha caught mid-test, worth remembering:** after editing the `.jinja` prompt template, the mentor kept replying with the *old* rules — uvicorn's `--reload` only watches `.py` files, so the template edit was real but invisible to the running process until a manual restart. Compounded by a repeat of the exact same stale-`netstat` false alarm hit earlier this session (a killed PID still showing `LISTENING`; `Get-Process` confirmed it was actually dead). Both resolved with a clean process restart, then reverified live.

**This work is on `feature/mentor-markdown-and-token-budgets`**, following on from `Option A for now, scope B later` and the user's direct "Yes, go ahead" approving the token-budget fix once the bug was diagnosed and explained.

---

## 2026-08-26 — Brainstorming session: multi-site consortium scope, attribution walked back, six issues filed, LLM default reverted to vLLM

**Session shape:** started in Ask mode (read-only) at the user's request to review the whole project cold before brainstorming — read `README.md`, `ROADMAP.md`, `CHANGELOG.md`, all of `devlog/HANDOFF.md`, all of `docs/DECISIONS.md`, `docs/BRAINSTORMING-BRIEF.md`, `docs/WHY-THIS-TOOL.md`, and the backend/frontend file layout, before saying anything back. Then a real back-and-forth brainstorm, then switched to Normal mode for the resulting work.

**What the user actually raised** (their own framing, paraphrased): they're starting an 11-center HIV data consortium project leaning toward OMOP CDM, very early — data not yet accessed, schemas unknown — and wondered whether this tool needed to grow to handle multiple data sources, whether teams collaborating on one assessment needed some kind of tracking, and whether the LLM setup (OpenRouter's `auto` router specifically) was trustworthy enough given the model-lottery problems already hit this project (see the v26 entry above).

**Multi-site scope, resolved into two filed-but-not-built issues, not built now:** researched real precedent (the HEAP project ran the same RDA-derived FAIR indicators across six cohorts independently, then compared them with a rollup rather than a different method; NFDI consortia apply RDA-FDMM per-resource within a consortium) and FAIRplus-DSM's actual Level 2 indicator text (field-level tidy data, joinable reference fields, a shared data dictionary — read in full previously for this project, see `docs/DECISIONS.md` v18). Landed on: new "Level 2" harmonization-readiness content (issue #16) plus a `Program`/`Consortium` grouping entity (issue #17) — both explicitly need a scoping conversation before implementation, same as the mentor (v19) and the plan (v16) were each scoped before being built. Explicitly ruled out: any ETL/harmonization tooling, and the already-parked OMOP DQD adapter (that's a later stage — after data is actually inside an OMOP CDM database, which this consortium hasn't reached).

**Collaboration/attribution — raised, then walked back by the user's own second thought, worth remembering if this comes up again:** initially discussed as a per-person audit trail. The user directly asked whether they were "overthinking it," which prompted disentangling it into two different jobs — coaching continuity (fine, stays private to one conversation) vs. accountability tracking (a compliance/project-management function). Concluded the second actively works against this tool's own design philosophy — every existing choice (the mentor's reworked tone, passing indicators getting real content instead of silence, the non-condescending "newbie" framing) protects an honest, consequence-free self-report, and a visible per-person log would risk distorting exactly that. **Decision: dropped from the roadmap** — see `docs/DECISIONS.md` v27 for the full reasoning. Only site-level grouping survives, inside issue #17.

**LLM trustworthiness: researched, then actually decided and implemented in this same session** (not left as an open issue) — see below.

**Six issues filed on GitHub** ([#14](https://github.com/atwine/fair-maturity-copilot/issues/14) through [#19](https://github.com/atwine/fair-maturity-copilot/issues/19)): pin an explicit model / stop using `openrouter/auto`, replace text-marker parsing with real structured output, Level 2 harmonization content, `Program`/`Consortium` grouping, a "which tool fits your situation" navigator extending `/about`, and documenting real LLM provider costs in the README. Full descriptions in the issues themselves — each written with a `## Goal`/`## Why`/`## Scope`/`## Out of scope`/`## Done when` structure matching this project's existing issue style, and the two open-ended ones (#16, #17) explicitly flagged as needing a scoping pass, not ready-to-build specs.

**Then, in the same session, the user made a direct call ahead of #14 being fully worked:** go back to self-hosted vLLM as the default, given the OpenRouter/`auto` reliability problems already hit. Implemented immediately on `feature/llm-default-back-to-vllm` (branched off `development`):
- `backend/.env` and `backend/.env.example` reverted to vLLM active (`ibnzterrell/Meta-Llama-3.3-70B-Instruct-AWQ-INT4`); OpenRouter kept as a fallback block but pinned to `meta-llama/llama-3.3-70b-instruct` (the *same* model vLLM runs) instead of `openrouter/auto` — so falling back doesn't also mean a behavior change.
- `README.md`'s "LLM provider" table reordered (vLLM listed first as this project's own default) and a new explicit "don't use `openrouter/auto`" callout added.
- `backend/app/config.py`'s comment updated to explain *why* vLLM is the Python-level default, referencing issue #14.
- `docs/DECISIONS.md` v27 and a `CHANGELOG.md` "Changed" entry added recording the full session and this specific reversal.

**Verified live shortly after** (same session, once `10.35.50.41` turned out to be reachable from this environment after all): confirmed `GET /v1/models` responds with the expected model, then ran the full backend suite including all 18 live-LLM tests (`test_report_live.py`, `test_plan_live.py`, `test_mentor_live.py`) — 61/61 passed. Report generation (93.81s for 6 tests), plan synthesis, and mentor conversations all behave correctly against vLLM post-revert. Commented on issue #14 with the result; left the issue open only for its separate structured-output-migration tracking, not for further model verification.

**Where this leaves things:** `feature/llm-default-back-to-vllm` (config/docs) and this verification follow-up are both merged locally into `development` — not yet pushed, pending the user's go-ahead. Issues #14-#19 are open on GitHub, unassigned. #16 and #17 still need a scoping conversation before anyone starts building. #14's live-verification concern is now resolved.

**Open questions carried forward:** everything from prior entries (promotion cadence, Neon production plan decision) — plus, now: when will the 11-center consortium project actually get data access (the user's colleagues were "just beginning to ask" as of this session), since that's the real trigger for #16/#17 becoming buildable rather than speculative.

---

## 2026-08-26 — Issue #19: real, measured LLM cost numbers added to the README

**Picked as the easiest of the six freshly-filed issues, deliberately.** #14 was effectively already done (previous entry); #16/#17 explicitly need a scoping conversation first; #15 needs real code changes; #18 needs actual frontend/UI work. #19 is pure documentation with no new code paths, so it went first.

**Didn't estimate — measured.** Wrote a throwaway script (`backend/_measure_token_usage.py`, deleted after use) that monkeypatches `openai.resources.chat.completions.Completions.create` to record real `usage.prompt_tokens`/`usage.completion_tokens` on every call, then ran one realistic flow through the actual FastAPI app against the live vLLM endpoint (which happened to be reachable again this session): a 12-question assessment with 4 gaps → report (12 calls) → plan (1 call) → a 3-message mentor conversation where the last message confirms a fix and triggers a re-score (5 calls). Real total: 14,203 prompt tokens, 852 completion tokens, 18 calls — not a guess from reading the prompt templates.

**Fetched current prices directly from OpenRouter's own model pages** (not carried over from earlier in this session, which could have drifted) for Llama 3.3 70B ($0.10/$0.32 per 1M) and Claude Sonnet 5 ($2/$10 per 1M), then applied the measured usage to get real per-flow costs: self-hosted vLLM $0, Llama-on-OpenRouter ≈$0.002, Sonnet ≈$0.037.

**A genuine finding, not just a number-filling exercise:** the 3-message mentor conversation (5 calls once the re-score is counted) used more tokens than the entire 12-call report. Worth remembering architecturally — every mentor turn resends the whole conversation history, so cost (and latency) grows with how long someone stays in a coaching conversation, unlike the report/plan's fixed one-time cost. Wrote this into the README as an explicit caveat rather than letting the headline per-flow numbers imply a flat cost regardless of usage pattern. Also added a multi-site extrapolation directly relevant to issues #16/#17: even at Sonnet's frontier price, 11 sites running this same flow stays under 50 cents total, which reframes the real decision between providers as reliability/data-sensitivity, not cost.

**Verified:** ran the instrumentation script itself against the real endpoint (not mocked) and got the numbers above directly from real API responses. Full account in `docs/DECISIONS.md` v28 and the `CHANGELOG.md` entry.

**This work is on `feature/readme-llm-cost-comparison`, not yet merged into `development`** — pending self-review and the user's go-ahead to push, same as every other change this session.

**Open questions carried forward:** unchanged from the entry above.

---

## 2026-08-26 — Issue #15: the mentor's confirmed-fix action moved to a real tool call

**Checked the blocking assumption before writing any code, rather than trust it or ignore it.** `mentor.py`'s own docstring said this was avoided because self-hosted vLLM isn't guaranteed to have tool-calling enabled. Sent a real tool-calling request directly to ACE's live vLLM endpoint and separately to the OpenRouter fallback model (`meta-llama/llama-3.3-70b-instruct`) — both returned correct, structured tool calls with the exact right arguments, not free text. That resolved the one thing that could have made this issue a dead end.

**What changed:** `mentor.py` no longer regex-matches `UPDATE_ANSWER:`/`NOTE:` out of the model's reply. A real `confirm_indicator_fix` tool is declared and passed with `tool_choice="auto"`; the model either writes ordinary text (plain conversation) or calls the tool (confirming a fix). The one real design decision: the tool's own arguments include a `reply_to_user` field carrying the model's conversational reply, rather than expecting separate free text alongside the call — confirmed directly in both live checks that providers stop writing `content` the moment they call a tool, so this was the only way to keep this at one LLM call per turn (a second, textbook "send the tool result back, get a follow-up reply" round trip would have doubled mentor latency on every confirmed fix, which the issue explicitly said not to do). `llm_client.py` gained `generate_chat_with_tools()` with its own smaller empty-reply retry (a tool call with no `content` is normal here, not a failure, so it can't reuse `_complete()`'s retry logic as-is). `mentor_system.jinja` rewritten to describe the tool; `MENTOR_PROMPT_VERSION` → `fair-mentor-v4`.

**Tests:** `test_mentor.py` rewritten — 9 old marker-line-regex tests became 8 tool-call-parsing tests (one old case, a conversational reply mentioning "update answer" mid-sentence, is now structurally impossible to misfire on, so it wasn't carried forward; new cases cover malformed/non-JSON tool arguments instead). Full suite: 60/60, including all 7 `test_mentor_live.py` tests against the real vLLM endpoint — `test_confirming_a_fix_in_chat_updates_the_real_answer_and_rescores` is the one that actually proves the new tool-calling path reaches all the way through to the real answer-update/rescore machinery, live, not just that the parser unit tests pass in isolation.

**Deliberately not done:** the plan's `GOAL:`/`STEP:`/`ADDRESSES:` parsing and the remediation writer's `SUMMARY:`/`STEPS:` parsing use the same marker-line pattern and could get the same treatment — issue #15 explicitly scoped this to the mentor only, as a separate follow-up if this one went cleanly (it did).

**This work is on `feature/mentor-tool-calling`, not yet merged into `development`** — pending self-review and the user's go-ahead to push.

**Open questions carried forward:** unchanged from the entry above, plus: whether to pick up the plan/remediation parsing conversions as follow-up issues now that this one's proven the approach works against real infrastructure.

---

## 2026-08-26 — Process change: code-review skill now required before every development → staging promotion (run via Claude Code)

**Why this is being recorded here, not just in `AGENTS.md`:** the project owner wants this to survive context resets and be visible to any agent (Devin or Claude) picking up this project cold. The `devlog/HANDOFF.md` is the first thing a new session reads.

**What happened:** during this session, the `code-review` skill (which spawns two parallel sub-agents for a two-axis Standards + Spec review) was attempted for the first `development` → `staging` promotion. It failed with "weekly usage quota exhausted" on Devin's side. The review was done manually inline instead — which worked for a small diff but is not the robust pattern the project's `AGENTS.md` and the project owner's global `CLAUDE.md` both call for.

**The new rule, effective now:**
- **All changes stop at `development` on Devin's side.** Devin can build, test, self-review, and merge feature branches into `development` locally — same as before.
- **The `code-review` skill pass happens on Claude Code before promoting `development` → `staging`.** The project owner has Claude Code quota available; Devin's sub-agent quota is exhausted this week. Run `/code-review` there against `origin/staging...origin/development` (or the equivalent fixed point) before merging to staging and pushing.
- **This is not a one-week workaround — it's the new standing process.** Even after Devin's quota resets, doing the review on Claude Code gives an independent review pass on a different toolchain, which is closer to the "second independent review" the project owner's global `CLAUDE.md` already calls for before production-facing promotions. Two different tools catching different mistakes is better than one tool reviewing its own work.
- **Devin can still do a manual inline review** as a first pass (catch obvious issues before handing off), but it does not replace the Claude Code `code-review` pass.

**For any agent reading this in a future session:** if you're on Devin and about to promote `development` → `staging`, stop. Build and test on Devin, merge to `development` locally, push to `origin/development`, then tell the project owner to run the `code-review` skill on Claude Code before the staging promotion. Do not merge to staging and push without that review having happened — this is the same hard limit `AGENTS.md` already sets (explicit go-ahead required), with the added specificity that the go-ahead should follow a Claude Code review pass.

**Current state at time of writing:** `staging` was merged locally (commit `e5937fd`, issue #6 — repository recommendations) but **not yet pushed to `origin/staging`**, pending this process being followed. The project owner may choose to push it as-is (the manual review passed, 60/60 tests green) or run the Claude Code review first — their call.

---

## 2026-08-26 — Issue #18 built (navigator), all docs updated, project handed back to Claude

**What was built this session (Devin):**

Issue #18 — a "which tool fits your situation" navigator extending `/about` — was built on `feature/navigator`, merged locally into `development`, and is ready for push. Full account in `docs/DECISIONS.md` v31.

- A new `/navigator` route (`frontend/app/navigator/page.tsx`) and client component (`frontend/components/navigator.tsx`) — a 6-question branching tree routing users to the right FAIR tool based on their situation.
- 7 destination recommendations, each with a mini-roadmap format (what/why/how/next + newbie/experienced split): this tool, FAIR-Aware, F-UJI, the RDA FAIR Data Maturity Model, CoreTrustSeal, AgroPortal/O'FAIRe, the ARDC FAIR Data Framework.
- All external URLs verified live — several broken links caught and corrected during development.
- Linked from three places: `SiteHeader` ("Which tool fits?"), `/about` page's landscape section, and a secondary link on the landing page below "Start an assessment" — deliberately an optional escape hatch, not a mandatory gate.

**Verified:** `tsc --noEmit` and `eslint` clean. `next build` succeeded. Live in the browser — all branching paths navigate correctly, destination content renders, all three entry points link correctly.

**Documentation updated this session (all on `development`, ready to push):**
- `docs/DECISIONS.md`: v31 (navigator) + v32 (staging review gap — see below).
- `CHANGELOG.md`: navigator entry under `### Added`; new `### Process — review gap to address` section.
- `README.md`: status line and repo layout's `app/` line updated to include the navigator page.
- `ROADMAP.md`: navigator added to Backlog as done (issue #18).
- This HANDOFF.md entry.

**Critical item for Claude to address — unreviewed code on `staging`:**

The project owner explicitly asked that this be flagged in the docs. `staging` is currently 3 commits ahead of `origin/staging` (the issue #6 repository-recommendations work, merged locally via commit `e5937fd`). This merge happened **without** the Claude Code `code-review` pass that the new standing process (entry above, 2026-08-26) requires. The manual inline review passed (60/60 tests green, no findings), but that's a first pass, not the independent second review the process now calls for. `staging` has **not** been pushed to `origin/staging` — it's waiting for the review.

**What Claude needs to do before `staging` can be promoted further:**
1. Run the `code-review` skill on Claude Code against the `origin/staging...staging` diff (the 3 unpushed commits: `1c80021`, `418d88a`, `e5937fd`).
2. Address any findings.
3. Only then push `staging` to `origin/staging` and consider the `staging` → `main` PR.

See `docs/DECISIONS.md` v32 for the full account.

**Branch state at handoff:**
- `development` is 2 commits ahead of `origin/development` (the navigator commit `6153488` + merge `a0774e8`). **Not yet pushed — pending the project owner's go-ahead.**
- `staging` is 3 commits ahead of `origin/staging` (issue #6 work). **Not yet pushed — pending the Claude Code review pass.**
- `main` is in sync with `origin/main`.
- All feature branches are merged into `development`. The following can be safely deleted once `development` is pushed: `feature/navigator`, `feature/about-page`, `feature/broaden-repository-recommendations`, `feature/fairification-plan`, `feature/landing-context-and-examples`, `feature/mentor-poc`, `feature/mentor-poc-docs`, `feature/mentor-poc-ui`, `feature/readme-center-header`, `feature/readme-update`, `feature/report-guided-remediation`, `feature/revisit-and-update-findings`, `feature/visual-identity-pass`, `docs/llm-provider-options`, `docs/mentor-scoping`.

**Open GitHub issues at handoff** (8 open, 1 to close):
| # | What | Status |
|---|---|---|
| [#2](https://github.com/atwine/fair-maturity-copilot/issues/2) | Checkpoint 6 — eval harness | Open |
| [#3](https://github.com/atwine/fair-maturity-copilot/issues/3) | Checkpoint 7 — deploy + dogfood | Open |
| [#4](https://github.com/atwine/fair-maturity-copilot/issues/4) | Checkpoint 8 — real ACE pilot | Open (depends on #3) |
| [#7](https://github.com/atwine/fair-maturity-copilot/issues/7) | Future — RAG/verification/adjustable ambition | Open (blocked on #5) |
| [#12](https://github.com/atwine/fair-maturity-copilot/issues/12) | Future — in-app LLM provider settings | Open |
| [#16](https://github.com/atwine/fair-maturity-copilot/issues/16) | Level 2 harmonization content | Open (needs scoping) |
| [#17](https://github.com/atwine/fair-maturity-copilot/issues/17) | Program/Consortium grouping | Open (needs scoping) |
| [#18](https://github.com/atwine/fair-maturity-copilot/issues/18) | Navigator extending `/about` | **Done — close after push** |

**Where to pick up (for Claude):**
1. **Immediate:** push `development` to `origin/development` (after the project owner's go-ahead), close issue #18 on GitHub, delete merged feature branches.
2. **Before next staging promotion:** run the `code-review` skill against the `origin/staging...staging` diff to address the unreviewed issue #6 work on `staging`.
3. **Roadmap:** Checkpoints 6 (eval harness), 7 (deploy), 8 (pilot) remain. Issues #16/#17 need scoping conversations before building.

**Open questions carried forward:** Promotion cadence for development→staging→main still unconfirmed. Neon production scale-to-zero plan decision still deferred to Checkpoint 7. The `uvicorn --reload` unreliability in the OneDrive-synced working directory persists — manually kill and restart the backend after every backend code change.

---

## 2026-08-27 — Staging review gap closed (Claude), development caught up after Devin session

Picked this project back up after a Devin session (2026-08-26/27) covering issues #6, #9/#15/#14 follow-ups, #18, and #19 — see `docs/DECISIONS.md` v27-v32 for the full account of each. `development` was already pushed and in sync with `origin/development` by the time this session started.

**Closed the review gap v32 flagged:** ran the `code-review` skill against the `origin/staging...staging` diff (the 3 unpushed issue #6 commits — `remediation.jinja`'s repository decision rule). Read every changed line directly (a small, four-file, prompt-text-only diff) rather than spawning the full 8-angle agent search — proportionate to the size and risk of the change. No findings: the change is prompt guidance only, no code-logic paths touched, and Devin had already verified it live (61/61 tests, including a dedicated re-run of `test_report_live.py`). Reran the full non-live suite locally as a final sanity check against the current default (vLLM, post issue #14's revert) — 60/60 passed. Pushed `staging` to `origin/staging` (`a3e0e8b..e5937fd`).

**Not yet done:** the `staging` → `main` PR itself — still needs the independent Open Code Review delegate-mode pass per this project's standing rule (right before any production PR goes up), and the project owner's explicit go-ahead to push/merge, same as every promotion so far.

**Update:** that PR (#20) and a follow-up (#21, bringing the navigator's actual code across after a promotion-sequencing gap) both went up, reviewed, and merged the same session.

---

## 2026-08-27 (continued) — UI review pass, mentor speed/context investigation, eval harness

A long continuation of the same day's session, covering four distinct pieces of work, each promoted through the full `development → staging → main` workflow with both required review passes.

**1. UI evaluation.** Ran a `design-critique` pass and an `accessibility-review` pass live against the running app (all screens, mobile and desktop). Found: report finding-card titles truncating on mobile (a stray `truncate` class), the "Minor gap" severity badge failing WCAG AA contrast (3.90:1, needed 4.5:1), the question wizard's radio group missing `aria-labelledby`, and no feedback during Neon's cold-start delay on new-assessment creation. All four fixed, verified live (including constraining a card to 360px width to directly confirm the wrap fix), merged via PR #22.

**2. Mentor bug: found by the project owner, root-caused live.** The owner reported two things that turned out to be the same bug: the mentor sometimes takes a long time and can render a completely blank opening message, and it seemed like "some plan-step cards pass context, others don't." Measured the actual backend call directly (bypassing the frontend) and found real inference time was 4-13s, not a rendering problem. Then reproduced the blank-bubble bug live, 3/3, by rendering the real system prompt and calling the LLM directly against vLLM (the active provider since issue #14's revert) — the model reliably calls `confirm_indicator_fix` on the very first "you just opened the chat" turn, even though nothing has been confirmed yet, and its `reply_to_user` argument sometimes comes back empty. Confirmed the "some cards, not others" perception was actually this same random-per-attempt failure, not a real wiring bug (checked: every plan card links to the mentor identically). Fixed by not offering the tool at all on the opening greeting. Also confirmed the OneDrive-folder-location theory only plausibly affects local dev-server compile/reload speed, not the LLM call itself, which is server-side and network-bound regardless of local folder. Merged via PR #22 (same PR as the UI fixes above).

**3. Eval harness (Checkpoint 6, issue #2).** See `docs/DECISIONS.md` v33 for the full account — briefly: built `backend/eval/golden_set.yaml` + `backend/scripts/run_eval.py` (LLM-as-judge for remediation text, mechanical coverage checking for plans). The judge itself needed three rounds of debugging before it was trustworthy (context-bleeding, a parsing gap, an overly literal jargon check) — the first run came back 0/8 and every bug was in the harness, not the writer prompt. Final run: 8/9. Merged via PR #23, closing issue #2.

**4. Post-merge end-to-end verification.** Ran a full assessment live on `main`'s actual merged code (not a feature branch) — new assessment → 12 questions → review → report → plan → mentor, confirming the mentor fix holds on a genuinely fresh conversation post-merge. Hit one real, transient Neon connection drop mid-run (`server closed the connection unexpectedly`) — confirmed via the backend's own error log, resolved itself on retry within a few seconds. This is Neon free-tier infrastructure behavior (already a known, documented risk — see Checkpoint 7 planning), not a regression from any of today's changes; noted here so it isn't mistaken for one if it recurs.

**Branch state at time of writing:** `development`, `staging`, and `main` are all in sync (verified via `git log` after each merge). No open PRs. Working tree clean except an untracked `.claude/launch.json` (a local dev-server convenience config, not committed).

**Open questions carried forward, still unresolved:** Neon production scale-to-zero plan decision (Checkpoint 7). Whether to implement mentor-chat streaming (discussed at length — a real architecture change, not scoped yet). The `uvicorn --reload`/Next.js dev-server slowness on this OneDrive-synced path (separate from the LLM-latency question, not yet actually fixed). A handful of small design-critique items not yet actioned: header nav touch targets slightly under the WCAG 2.2 minimum, the navigator's static "N of 6" progress counter, and the wizard's radio inputs sharing an empty `name` attribute (grouping still works via ARIA, just no native arrow-key cycling).
