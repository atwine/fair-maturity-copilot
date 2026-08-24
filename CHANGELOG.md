# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project doesn't have releases/version tags yet — everything lands under `Unreleased` until v0 first ships to a real pilot user.

## [Unreleased]

### Added
- Repo scaffold: `README.md`, `ROADMAP.md`, `docs/PLANNING_PROMPT.md`, `docs/DECISIONS.md`, `docs/background/` (the v1-v3 idea-scoping history), `devlog/HANDOFF.md`.
- Backend engine scaffold (`backend/app/engine/`): standard-agnostic data model (`Adapter`, `Indicator`, `AssessmentRun`, `Answer`, `Finding`, `RemediationDraft`, `Report`), the `Adapter` Protocol seam (`ports.py`), generic severity scoring, the remediation-writer stage with automated grounding checks, and an OpenAI-compatible LLM client configured for both a local Ollama endpoint (dev) and a vLLM-hosted Llama 3.3 70B endpoint (pilot) via env vars only.
- `backend/tests/engine/test_boundary.py` — proves the engine/adapter boundary against a fake adapter, before any FAIR-specific content exists.
- FastAPI app skeleton (`backend/app/main.py`) with CORS wired for a future Next.js frontend.

### Fixed
- Banned-jargon regex in the remediation grounding check (`backend/app/engine/remediation.py`) was missing a word-boundary on its RDA-code branch, which could reject valid remediation text that merely contained an RDA-code-like substring inside a longer word. Caught in review before merging to `main`.

### Changed
- Repo default branch renamed `master` → `main`; adopted the full three-tier branching structure — `feature/<name>` → `development` → `staging` → `main`, with `main` reachable only via a reviewed, explicitly-approved PR (see `README.md`'s "Branching convention"). An initial two-tier version of this fix (feature → main directly) was corrected in the same session after review.
- `ROADMAP.md`'s v0 milestones reframed from calendar-day estimates to checkpoints — the original day-based plan assumed unassisted solo development, which doesn't match the actual Claude-assisted pace.
- Added a synthetic demo dataset checkpoint (`ROADMAP.md` Checkpoint 3) ahead of the API/frontend work — real ACE/TASO data, especially anything OMOP-shaped, likely needs a cleared data-governance path before touching any LLM, so the tool needs to be demoable and testable on fake data first.
