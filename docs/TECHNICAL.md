# Technical reference

This document covers everything a developer forking this repo or contributing
to it needs to know: architecture, the full API surface, branching
conventions, repo layout, LLM cost analysis, and testing strategy. The
[README](../README.md) is intentionally kept lean for first-time users who
just want to get the tool running.

## Architecture

Built as a reusable **engine + adapter** pattern, not a one-off script:

```
intake (structured findings) → scoring → LLM remediation writer → plain-language report
```

Each adapter owns its own indicator content, prompt wording, and plan
ordering; the engine owns everything standard-agnostic (scoring, remediation
grounding, plan parsing, mentor loop). Two adapters exist today: `fair-v0`
(12 single-dataset FAIR questions) and `harmonization-v0` (6 multi-site
consistency questions). Nothing in `backend/app/engine/` may reference any
adapter by name — that boundary has been proven with a real second adapter,
not just the empty test double it was originally validated against. A third
adapter (OMOP CDM Data Quality Dashboard) is parked in
[`ROADMAP.md`](../ROADMAP.md) — the boundary is ready for it whenever the
need arrives.

## The problem this solves

The Research Data Alliance's FAIR Data Maturity Model defines 41 indicators
for assessing how Findable, Accessible, Interoperable, and Reusable a dataset
or research practice is. The existing automated checkers —
[F-UJI](https://www.f-uji.net) and
[FAIR Checker](https://fair-checker.france-bioinformatique.fr) — cover the
machine-readable half of that (can a crawler resolve your metadata), and only
ever talk to a computer, never a person; their output is written for data
engineers, not for a research group lead trying to figure out what to
actually fix. The two richer resources in this space — the
[FAIR Cookbook](https://faircookbook.elixir-europe.org) (60+ detailed
recipes) and [FAIR-DSM](https://fairplus.github.io/Data-Maturity/) (a
5-level enterprise maturity roadmap) — assume the reader already knows which
part applies to them, or has real institutional infrastructure to build on.

This tool is a guided version, for the gap none of those fill: walk a
non-technical stakeholder through a 12-indicator subset of the RDA model in
plain language, score it, use an LLM to turn every weak indicator into a
specific actionable next step, and synthesize the whole set of gaps into one
ordered FAIRification plan. A second adapter (`harmonization-v0`, issue #16)
answers a different question for a different audience: whether multiple sites
in one initiative describe their data consistently enough to combine and
compare — 6 plain-language questions grounded in FAIRplus-DSM's Level 2
indicators, with a non-penalized "we haven't started this yet" answer for
initiatives at an early stage. See
[`docs/WHY-THIS-TOOL.md`](WHY-THIS-TOOL.md) (also live in-app at `/about`)
for the full writeup of how this fits alongside the rest of the FAIR-tooling
landscape.

For a single self-contained document covering the project's origin story,
value proposition, current state, and open questions — written for
brainstorming with a fresh collaborator (human or AI) rather than for
implementation — see [`docs/BRAINSTORMING-BRIEF.md`](BRAINSTORMING-BRIEF.md).

## Tech stack

- **Backend**: FastAPI + SQLModel + Alembic, Postgres (Neon)
- **Frontend**: Next.js 16 + React 19 + TypeScript + Tailwind v4 + shadcn/ui
  (built on Base UI, not Radix — its polymorphic components use a `render`
  prop, not `asChild`)
- **LLM**: any OpenAI-compatible provider — see "LLM provider" in the README
  for the quick-start version, or the cost analysis below for the full
  picture.

## LLM provider — full reference

**This tool needs a real LLM to function** — it's what turns each answer into
plain-language feedback, synthesizes the FAIRification plan, and powers the
mentor chat. Without one configured, the assessment wizard works but the
report, plan, and mentor screens will fail. There's no default that "just
works" out of the box for a new clone of this repo, so pick one:

| Option | Cost | Setup | Good for |
|---|---|---|---|
| **vLLM** (this project's own default) | Your own GPU infra, ~$0 marginal cost once running | Self-hosted | Teams with real GPU hardware who want to run their own model at scale, with consistent behavior instead of a router's per-request pick — this is how ACE runs its own pilot |
| **[OpenRouter](https://openrouter.ai/keys)** (recommended if you don't have your own GPU infra) | Pay-per-token | Sign up, copy an API key, **pin a specific model** | Getting running in a minute, no hardware needed |
| **[Ollama](https://ollama.com)** | Free | Install locally, `ollama pull llama3.1:8b` | Trying this out at zero cost, or fully offline work — nothing leaves your machine. Only really viable for lightweight use: small quantized local models struggle with this app's larger prompts (the mentor's system prompt in particular) |
| **Anything else OpenAI-compatible** | Varies | Provider-specific | Together AI, Groq, Azure OpenAI, the OpenAI API itself, or any other provider that speaks the same `/chat/completions` shape |

**Don't use OpenRouter's `openrouter/auto` model.** It picks a different
model per request, which sounds convenient but isn't safe to depend on here:
it can silently route a request to a reasoning model that spends its whole
completion-token budget "thinking" and returns an empty reply — this
happened twice in testing (see `docs/DECISIONS.md`). Name a specific model
instead. If you're using OpenRouter as a fallback for a self-hosted vLLM
box, pin it to the *same* model your vLLM box runs, so falling back doesn't
also mean a behavior change.

All of these are configured the exact same way — three values in
`backend/.env` (`LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`), never a code
change. See `backend/.env.example` for a ready-to-uncomment block for each
option above.

### What this actually costs

Real numbers, not a guess — measured by instrumenting one full flow end to
end (a 12-question assessment with 4 gaps → report → plan → a 3-message
mentor conversation, one of which confirms a fix and triggers a re-score) and
counting the actual tokens the LLM client sent and received: **14,203 prompt
tokens, 852 completion tokens, across 18 calls total.** Applying that same
usage to three provider options (prices as listed on each provider's own
pricing page — check current numbers before relying on this long-term, they
change):

| Provider | Price per 1M tokens (in / out) | Cost for that one measured flow | Notes |
|---|---|---|---|
| Self-hosted vLLM (Llama 3.3 70B) | $0 marginal | **$0** | Real cost is the GPU hardware itself, not per-call — this is what makes it cheap *in steady state*, not cheap to start |
| Llama 3.3 70B, hosted on OpenRouter | $0.10 / $0.32 | **≈ $0.002** | Same model as the self-hosted option above — a behavior-matched fallback, priced cheaply enough not to matter even at real usage volume |
| Claude Sonnet 5 (frontier, for comparison) | $2 / $10 | **≈ $0.037** | ~20x pricier than the Llama 3.3 70B options for this workload — the cost of not needing your own GPU hardware at all |

A few things worth knowing before treating these numbers as the whole
picture:
- **A full assessment (report + plan) is a fixed, one-time cost per run** —
  the mentor is not. Every mentor message resends the whole conversation
  history, so a longer coaching conversation costs more than a short one, and
  grows the longer someone stays in it. The mentor's share of the measured
  flow above (5 calls, including the re-score triggered by a confirmed fix)
  was already the single largest contributor to total tokens despite being
  just 3 user messages.
- **For a multi-site initiative** (see issues
  [#16](https://github.com/atwine/fair-maturity-copilot/issues/16)/[#17](https://github.com/atwine/fair-maturity-copilot/issues/17))
  running this once per site, these per-run numbers multiply directly — 11
  sites at the OpenRouter/Llama price above is still only a few cents total;
  at the Sonnet price, still under 50 cents. Cost is very unlikely to be the
  deciding factor between these options at this tool's scale; reliability and
  data-sensitivity are the real tradeoffs (see the "don't use
  `openrouter/auto`" note above).

**Why a publicly hosted provider is a reasonable option here, not just a
self-hosted one:** this tool never sends a dataset itself to the LLM — only
the plain-language answers and free-text notes a person types into the
assessment wizard. There's no file upload, no raw data, nothing sensitive by
default leaving your machine beyond what you type into the form fields. That
said, for anything involving multiple organizations' data practices (see the
multi-site consortium work tracked in issues #16/#17), we lean toward
self-hosted as the more conservative default.

## API surface

| Method | Path | What it does |
|---|---|---|
| GET | `/adapters/{adapter_id}/questions` | The ordered question set for an adapter (`fair-v0` or `harmonization-v0`) |
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

Answers can also be edited after an assessment is completed
(`PUT /assessments/{id}/answers/{indicator_id}`) — this is how "revisiting"
a finding from the report works: it re-scores that one indicator, regenerates
its remediation, and refreshes the report's cached score.

Interactive API docs are available at `http://localhost:8000/docs` when the
backend is running.

## Testing

Most tests (`tests/engine/`, `tests/adapters/`) need no database or LLM
connection — they're the fastest way to confirm the setup works. `tests/api/`
needs no external DB either (each test gets its own throwaway SQLite file),
but `tests/api/test_report_live.py`, `test_plan_live.py`,
`test_mentor_live.py`, and `test_harmonization_live.py` do call the real LLM
configured in `.env`. `seed_indicators.py` needs a real `DATABASE_URL`
(Postgres via Neon, or a local SQLite URL like `sqlite:///./dev.db` for quick
local testing) — run it before starting the API, or report generation will
fail with a clear error telling you to.

### Dev server tip

`--reload-dir app` matters more than it looks: without it, `--reload` watches
everything under `backend/`, including `.venv` (8,000+ files that never
change). On a cloud-synced working directory (OneDrive, Dropbox, etc.) that's
not just wasted CPU — every one of those file checks can pay a sync-client
tax. This cuts down *unnecessary* watching, but doesn't fully solve dev-server
reload speed on a synced folder: `uvicorn --reload` itself can still hang
mid-restart on Windows after a real code change (reproduced live: the reload
log stops right after "Reloading…" with both the old and new process idling,
no crash, no further output). If a reload seems stuck for more than a few
seconds, don't wait it out — kill the process and start it fresh.

## Branching convention

Three long-lived branches, promotion in one direction only:

```
feature/<name>  →  development  →  staging  →  main
 (isolated)          (integration)   (pre-prod)   (production)
```

- **All new work** happens on a `feature/<short-name>` branch, cut from
  `development`. Never commit directly to `development`, `staging`, or
  `main`.
- **Feature → `development`**: gets a code-review pass on the diff first.
  Pushing the resulting `development` update to GitHub is never automatic —
  always confirmed before it happens, not reported after.
- **`development` → `staging`**: same discipline — review, then confirm
  before pushing.
- **`staging` → `main`**: only via a pull request, never a direct push. A
  second, independent review (Open Code Review delegate mode) runs on that
  PR before it goes up. Merging the PR requires explicit go-ahead — an open
  PR is not itself permission to merge.
- `main` is production. It should only ever change via a reviewed, approved
  PR from `staging`.

**One documented exception:** the first backend scaffold (engine + boundary
test) was merged directly into `main` before this three-tier structure was
set up, with explicit one-time approval to leave it as-is rather than rewrite
already-pushed history. Every commit from that point forward follows the
structure above. See `docs/DECISIONS.md` and `devlog/HANDOFF.md` for the full
account.

## Repo layout

```
backend/
  app/
    engine/            — standard-agnostic core (models, scoring, remediation, plan parsing, mentor loop, LLM client, content loader)
    adapters/registry.py — maps adapter_id -> concrete adapter; the one place that knows which adapters exist
    adapters/fair/      — FAIR-specific indicators.yaml, adapter, remediation + plan + mentor prompts
    adapters/harmonization/ — multi-site consistency check (issue #16): 6 indicators, own prompts, "not_started" severity
    api/                — REST routes + schemas (see "API surface" above)
  fixtures/             — synthetic demo dataset profiles (no real ACE/TASO data touches an LLM)
  scripts/               — seed_indicators.py (loads all adapters), run_demo_assessment.py, run_eval.py
  eval/                  — golden_set.yaml: LLM-judge test cases for remediation + plan quality (Checkpoint 6)
  tests/                 — engine boundary, scoring, plan parsing, mentor parser; both adapters' content + flow tests; live API tests against real vLLM
  .env.example          — required env vars, including both LLM provider presets
frontend/
  app/                   — new, question/[indicatorId] (also used to revisit a finding), review, report, plan, mentor/[stepId], about, navigator
  lib/                   — api-client.ts + types.ts, mirroring the backend's REST contract
  components/            — fair-spectrum, navigator, loading-state, ui/ (shadcn)
docs/
  TECHNICAL.md          — this file
  PLANNING_PROMPT.md    — the Plan Mode prompt that produced the v0 build plan
  DECISIONS.md          — why this project, and not the nine other ideas we scoped first
  WHY-THIS-TOOL.md      — plain-language explainer: who this is for, and how it fits the wider FAIR-tooling landscape
  PLANS/                — approved implementation plans for individual issues (e.g. issue-16-harmonization-plan.md)
  demo_reports/          — generated output from scripts/run_demo_assessment.py — what the tool actually produces
  eval_reports/          — generated output from scripts/run_eval.py — LLM-judge quality checks
  fairification-framework-Africa/ — reference material this tool's design was checked against (see DECISIONS.md v16-v18)
  background/           — the earlier idea-scoping reports (v1-v3)
devlog/
  HANDOFF.md            — running session log, written so any agent (Claude, Devin) can resume cold
assets/
  logo.svg              — the brand mark (README); kept in sync by hand with frontend/app/icon.svg and components/logo-mark.tsx
ROADMAP.md              — what's built, what's next, what's tracked-but-parked
CHANGELOG.md            — dated record of what shipped
```
