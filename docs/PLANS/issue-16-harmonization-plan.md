# Level 2: Multi-Site Harmonization Readiness Check (Issue #16)

> **Handoff note:** this is the full, approved implementation plan for issue
> #16, copied into the repo (from the Claude Code plan-mode file) so it
> travels with the codebase and any agent — Claude, Devin, or a fresh session
> of either — picking this up can find it without needing this session's
> local machine state. See `devlog/HANDOFF.md` for the running log of what's
> actually been built against this plan so far and what's left.

## Context

The FAIR Maturity Copilot today only ever asks one kind of question: "is this
one dataset well-managed?" (the existing 12-question `fair-v0` check). A real,
near-term need — an 11-center HIV data consortium moving toward a shared OMOP
data model — needs a different question answered: "do these sites describe
their data consistently enough to combine and compare?" That's a genuinely
different kind of check, not a deeper version of the same one.

Issue #16 asked for this content, grounded in the real FAIRplus-DSM "Level 2"
standard, and left one thing explicitly unresolved: should this be bolted
onto the existing check, or built as its own thing? The project owner and
Claude worked through six plain-language questions together (including a "we
haven't started yet" answer that must never count against you — copied from
a real multi-cohort project, HEAP, which does the same), and agreed the tool
should redirect people to outside FAIR-DSM resources for anything more
infrastructure-heavy than that, rather than rebuild what already exists
elsewhere.

This plan builds that: a second, independent check (`harmonization-v0`)
living alongside the existing one, offered as a next step once someone
finishes the check they already know, not as an upfront fork that complicates
the common case. Two decisions confirmed with the project owner before
implementation started: it should be discoverable both from the finished
report *and* from the "Which tool fits?" page, and a "haven't started yet"
answer gets its own clearly separate, non-judgmental section in the report —
not lumped in with "needs attention."

Everything here is scoped to issue #16 only. Issue #17 (grouping many sites'
results into one rolled-up view) is a separate, not-yet-scoped piece of work
and is explicitly **not** part of this plan.

## Why a separate adapter, not an extension of `fair-v0`

Investigated directly rather than assumed. The engine already has a clean
seam for this (`app/engine/ports.py`'s `Adapter` Protocol +
`app/adapters/registry.py`) — built for exactly this purpose, but never
actually exercised with a second real adapter (the only other "adapter" in
the codebase is a deliberately empty test double, `FakeAdapter` in
`tests/engine/test_boundary.py`). Concretely, the new content needs:
- its own tone for writing remediation advice ("here's how to begin" is not
  "here's how to fix a gap" or "here's who to ask"),
- its own genuinely new "haven't started, and that's fine" outcome that must
  never hurt the score, and
- its own natural step-ordering when it writes a walkthrough plan.

Those are exactly the things the adapter boundary exists to hold separately.
Extending `fair-v0` would mean threading all of this through code built
around a different vocabulary. A second adapter is the correct-sized change,
and it's also the first real proof that the engine/adapter split holds up
for more than one thing — worth knowing regardless of this feature.

## What's being reused vs. built new

Reused as-is, no changes: `app/engine/mentor.py`'s conversation loop, the
`/plan` page and mentor-chat frontend pages (already fully generic), the
existing branching/review workflow, the existing eval-harness pattern
(`backend/scripts/run_eval.py`), the existing `navigator.tsx` choice-screen
UI pattern (reused for two new small link targets, not rebuilt).

Built new: the `harmonization-v0` adapter's content/prompts, one new answer
value + severity (`not_started`) threaded through scoring/remediation/report,
and two small "start the multi-site check" entry points (report page +
navigator).

Fixed as a required prerequisite: `app/api/routes_plan.py` currently imports
FAIR's plan-building code directly, bypassing the adapter boundary entirely
— every run's walkthrough plan is built with FAIR's own wording today,
regardless of which adapter it belongs to. This has been harmless so far
because there's only ever been one adapter to notice the bug. It stops being
harmless the moment a second adapter exists, so it's fixed first, proven
against the *existing* check with zero behavior change, before any new
content is built on top of it.

---

## Sequence

Five feature branches off `development`, each self-reviewed, then a single
`development → staging → main` promotion pass at the end (both required
review passes — `code-review` skill on the `staging` push, `open-code-review-delegate`
skill right before the `main` PR — plus the project owner's explicit
go-ahead before each push and before the final merge, per this project's
standing branching convention, see `README.md`).

### PR 1 — Engine fixes (no new content yet, zero visible change)

Purpose: make the engine layer actually adapter-agnostic and teach it about
the new non-penalized outcome, proven against the *existing* check only.

- **`backend/app/engine/scoring.py`** — `composite_score()` currently gives an
  unrecognized outcome a score of zero credit but still counts it toward the
  total, which is a *penalty*, not neutral. Fix it to genuinely exclude a
  `not_started` finding from the score altogether — it neither helps nor
  hurts. Also move `severity_for_answer()` here from
  `app/adapters/fair/scoring_rubric.py` (it's pure generic lookup logic that
  never belonged to one adapter) — then delete that file.
- **`backend/app/engine/remediation.py`** (line 36) — extend the existing
  "don't demand quoted-back specifics" rule to also cover `not_started`
  answers, the same way it already does for "I don't know" and "already
  passing" — a one-line change.
- **New `backend/app/engine/plan.py`** — pulls the generic plan-building
  pieces (`Plan`, `PlanStep`, `PlanGenerationFailed`, the parser, the
  "exclude passing items" filter) out of `app/adapters/fair/plan.py` into the
  engine, where they actually belong since none of it is FAIR-specific. Add
  `build_plan(...)` to the `Adapter` Protocol in `app/engine/ports.py`.
  `app/adapters/fair/plan.py` shrinks to just its own wording template plus a
  thin wrapper.
- **`backend/app/api/routes_plan.py`** — the actual fix: stop importing
  `app.adapters.fair.plan` directly; call `get_adapter(run.adapter_id).build_plan(...)`
  instead, same as every other route already does.
- **`backend/app/api/routes_answers.py`** — the allowed-answers list is
  currently one hardcoded global set (4 values, for every adapter). Change it
  to check against the specific question's own options instead — correct
  regardless of how many adapters exist, and the natural way to let a 5th
  value in for the new check without a special case.
- **`backend/scripts/seed_indicators.py`** and **`backend/tests/api/conftest.py`**
  — both currently only know about `fair-v0`'s content file. Extend both to
  loop over a small list of content modules so a second adapter's questions
  actually get loaded into the database and into test fixtures.

**Verification**: run the full existing backend test suite — must pass
unchanged, proving nothing about today's check regressed. Add new,
adapter-independent tests proving the new exclusion behavior and grounding
exemption work correctly using made-up test data (no real adapter needed).

### PR 2 — The `harmonization-v0` adapter itself (backend only, not yet reachable in the UI)

Purpose: build the new check's content and behavior, testable directly
against the API, before touching any screen.

- **New `backend/app/adapters/harmonization/`** — mirrors
  `backend/app/adapters/fair/`'s structure exactly: `adapter.py`,
  `content.py`, `indicators.yaml` (the six agreed questions, five answer
  options each including "haven't started yet," worked examples, help text —
  same shape as the existing 12), `prompt.py` + `prompts/remediation.jinja`
  (with a new "how to begin" tone for the `not_started` answer, distinct from
  the existing "how to fix" and "who to ask" tones), `plan.py` +
  `prompts/harmonization_plan.jinja` (its own natural step-ordering, not
  FAIR's), `mentor_prompt.py` + `prompts/mentor_system.jinja` (also needs its
  own "how to begin" tone — a mentor chat about a not-yet-started item
  shouldn't read like something's broken).
- While building `content.py`, also promote its already-generic YAML-loading
  logic into a small shared `backend/app/engine/content_loader.py` used by
  both adapters — avoids maintaining two copies of identical loading code.
- Register the new adapter in `app/adapters/registry.py`.
- New backend tests mirroring the existing `fair-v0` test files, plus one
  full create → answer (including a "haven't started yet" answer) → complete
  → report → plan flow test.
- Extend `backend/eval/golden_set.yaml` and `backend/scripts/run_eval.py`
  (currently hardcoded to `fair-v0`) with harmonization cases, and run it —
  the same LLM-quality check every remediation prompt in this project gets
  before shipping.

**Verification**: new backend tests pass; `run_eval.py` run against the
extended golden set, report read before moving on — same bar as the existing
Checkpoint 6 harness.

### PR 3 — Frontend plumbing (still exercised only through the existing check)

Purpose: teach the frontend about a 5th answer/severity value and about
adapter-specific content in general, proven against the *existing* check
first so nothing about today's screens visibly changes.

- **`frontend/lib/types.ts`** — add `"not_started"` to the answer-value and
  severity types. Also widen the "principle group" type from a fixed list of
  4 to a general text label — it's adapter-defined content already, just
  wasn't exercised by more than one adapter until now.
- **`frontend/components/fair-spectrum.tsx`** — the little colored progress
  strip on the question page currently has hardcoded colors for exactly the
  existing 4 groups. Needs to assign colors to whatever groups a given
  adapter actually has, instead of a fixed lookup table. This is the one
  genuinely fiddly piece of this PR — re-verify the existing check's colors
  look exactly the same after the change, in both light and dark mode.
- **`frontend/app/globals.css`** — add color tokens for the new "not started"
  state (contrast-checked for readability, same manual check already done
  for the "minor gap" color earlier this project), distinct from the
  existing "worth finding out" purple since they mean different things.
- **`frontend/app/assessments/[id]/report/page.tsx`** — add the "not
  started" label/color, and its own separate report section (per the
  project owner's confirmed preference) rather than folding it into "needs
  attention." Also fixes a small related bug this surfaces: the button to
  view the walkthrough plan is currently only shown when something "needs
  attention" — a report with only "not started" items would hide a plan
  that actually exists.

**Verification**: full backend suite unaffected (frontend-only PR). Live
walkthrough of the *existing* check in the browser (light + dark mode) to
confirm nothing visibly changed.

### PR 4 — Making the new check reachable

Purpose: the two entry points the project owner chose, without adding any
extra step to the common, existing path.

- **`frontend/app/assessments/new/page.tsx`** — no new chooser screen shown
  by default (matches the "offer it after, don't ask up front" decision).
  Instead it reads which check to start from how it was reached (a link
  parameter), defaulting to today's single-dataset check exactly as now.
- **`frontend/app/assessments/[id]/report/page.tsx`** — new small "suggested
  next step" card on a *finished* report: "Also coordinating data across
  multiple sites? Check how they fit together" → starts the new check.
- **`frontend/components/navigator.tsx`** — the existing "multiple sites"
  branch of the "Which tool fits?" page currently sends people entirely
  outside the tool. Rework its wording and link so it offers the new in-tool
  check as the real next step, while still pointing to outside FAIR-DSM
  resources for the genuinely bigger, infrastructure-heavy stuff that stays
  out of scope on purpose.

**Verification**: live, full end-to-end walkthrough in the browser —
starting the new check from both entry points, all six questions including a
"haven't started yet" answer, the report's three sections, the plan, and a
mentor conversation on a "not started" item.

### Docs (folded into whichever PR touches the relevant thing, not deferred)

`docs/DECISIONS.md` (the separate-adapter decision and why), `CHANGELOG.md`
(Added section), `ROADMAP.md` (mark the relevant line done), `devlog/HANDOFF.md`
(a dated entry per PR, per this repo's own handoff convention). Close issue
#16 from the PR that ships the reachable check (PR 4), same pattern as issue
#2 earlier in this project.

---

## Critical files

- `backend/app/engine/scoring.py` — score exclusion fix
- `backend/app/engine/ports.py` — Adapter Protocol, gains `build_plan`
- `backend/app/api/routes_plan.py` — the boundary-leak fix
- `backend/app/api/routes_answers.py` — per-question answer validation
- `backend/app/adapters/registry.py` — where the new adapter gets registered
- `backend/app/adapters/fair/` — the pattern `harmonization/` mirrors
- `frontend/lib/types.ts` — the 5th value/severity
- `frontend/components/fair-spectrum.tsx` — hardcoded-colors fix
- `frontend/components/navigator.tsx` — the "multiple sites" branch rework
- `frontend/app/assessments/[id]/report/page.tsx` — new section + next-step card

## How this gets executed

PR 1 → PR 4 in order (PR 3 can happen alongside PR 2 since they don't touch
the same files, but PR 4 needs both finished first). Each PR gets
self-reviewed, merged to `development` with the project owner's go-ahead
before the push, same as every other change to this project. After PR 4 is
in and end-to-end verified live, one promotion pass takes everything from
`development` to `staging` (with the required `code-review` pass) to `main`
(with the required `open-code-review-delegate` pass), each push and the
final merge confirmed with the project owner first.
