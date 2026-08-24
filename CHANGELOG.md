# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project doesn't have releases/version tags yet — everything lands under `Unreleased` until v0 first ships to a real pilot user.

## [Unreleased]

### Added
- Remediation prompt template (`backend/app/adapters/fair/prompts/remediation.jinja`) and renderer (`prompt.py`) — pulled forward from a later checkpoint since the demo run below needed real remediation text.
- 4 synthetic demo dataset fixtures (`backend/fixtures/synthetic_datasets.py`), varied in size/format/domain/FAIR maturity, and `scripts/run_demo_assessment.py` running them end-to-end through the real engine and a live LLM. Generated reports committed at `docs/demo_reports/`.
- Tests: `tests/engine/test_remediation.py` (grounding-check logic, including the dont_know bypass below) and `tests/fixtures/test_synthetic_datasets.py` (fixture well-formedness).
- FAIR adapter content (`backend/app/adapters/fair/`): `indicators.yaml` with the 12 selected RDA indicators (plain-language question, definition, help text, priority, scoring rubric for each), `FairAdapter` implementing the engine's `Adapter` Protocol, and `scripts/seed_indicators.py` to load them into the database. Flex-slot indicator resolved to F3-01M — see `docs/DECISIONS.md`.
- `backend/tests/adapters/fair/test_adapter.py` — covers question-set completeness, content non-emptiness, and answer-to-severity scoring.
- Repo scaffold: `README.md`, `ROADMAP.md`, `docs/PLANNING_PROMPT.md`, `docs/DECISIONS.md`, `docs/background/` (the v1-v3 idea-scoping history), `devlog/HANDOFF.md`.
- Backend engine scaffold (`backend/app/engine/`): standard-agnostic data model (`Adapter`, `Indicator`, `AssessmentRun`, `Answer`, `Finding`, `RemediationDraft`, `Report`), the `Adapter` Protocol seam (`ports.py`), generic severity scoring, the remediation-writer stage with automated grounding checks, and an OpenAI-compatible LLM client configured for both a local Ollama endpoint (dev) and a vLLM-hosted Llama 3.3 70B endpoint (pilot) via env vars only.
- `backend/tests/engine/test_boundary.py` — proves the engine/adapter boundary against a fake adapter, before any FAIR-specific content exists.
- FastAPI app skeleton (`backend/app/main.py`) with CORS wired for a future Next.js frontend.

### Fixed
- Banned-jargon regex in the remediation grounding check (`backend/app/engine/remediation.py`) was missing a word-boundary on its RDA-code branch, which could reject valid remediation text that merely contained an RDA-code-like substring inside a longer word. Caught in review before merging to `main`.
- `indicators.yaml`'s unquoted `yes`/`no` keys and values were silently parsed as Python booleans by PyYAML (the classic YAML 1.1 "Norway problem"), breaking every scoring lookup. Caught by actually running the tests, not by review.
- `scripts/seed_indicators.py` raised `DetachedInstanceError` when logging its success message, from reading an ORM attribute after the database session that loaded it had already closed.
- `content.py`'s YAML anchors/aliases meant every indicator sharing the default scoring rubric or answer options pointed at the exact same Python dict/list object rather than a copy — a latent shared-mutable-state bug. Now deep-copied per indicator; the YAML file is also now parsed once and cached instead of being re-read by three separate functions.
- The remediation grounding check rejected correct "who to ask" responses for `dont_know` answers with thin notes, since those legitimately don't share words with a near-empty note. Found live against real vLLM output during the Checkpoint 3 demo run; `dont_know` answers now bypass the reference-overlap check (word-count and jargon checks still apply).
- `scripts/run_demo_assessment.py`'s docstring said the tool defaults to local Ollama, written before the LLM default switch below — caught in review, updated to match.

### Changed
- Repo default branch renamed `master` → `main`; adopted the full three-tier branching structure — `feature/<name>` → `development` → `staging` → `main`, with `main` reachable only via a reviewed, explicitly-approved PR (see `README.md`'s "Branching convention"). An initial two-tier version of this fix (feature → main directly) was corrected in the same session after review.
- `ROADMAP.md`'s v0 milestones reframed from calendar-day estimates to checkpoints — the original day-based plan assumed unassisted solo development, which doesn't match the actual Claude-assisted pace.
- Added a synthetic demo dataset checkpoint (`ROADMAP.md` Checkpoint 3) ahead of the API/frontend work — real ACE/TASO data, especially anything OMOP-shaped, likely needs a cleared data-governance path before touching any LLM, so the tool needs to be demoable and testable on fake data first.
- **LLM default switched from local Ollama to vLLM** (`app/config.py`, `.env.example`) — the Checkpoint 3 demo run showed Ollama was far slower in practice on available hardware, and vLLM is both dedicated A100 infra and the actual production target. Ollama kept as an offline fallback only.
