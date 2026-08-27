# Contributing to fair-maturity-copilot

Thanks for your interest in contributing! This is a small project built by
[ACE](https://ace.ac.ug) for assessing FAIR data maturity in research
organizations. Whether you're fixing a typo, reporting a bug, or proposing a
new adapter, this guide will help you get started.

## Reporting a bug or suggesting a feature

The easiest way to contribute is to
[open an issue](https://github.com/atwine/fair-maturity-copilot/issues/new/choose).
Use the **Bug report** template if something isn't working as expected, or
the **Feature request** template if you have an idea for an improvement.
Fill in as much detail as you can — the templates will prompt you for what's
useful.

## Proposing a code change

### Branching

This project uses a three-branch promotion model:

```
feature/<name>  →  development  →  staging  →  main
```

- **All work happens on a `feature/<short-name>` branch**, cut from
  `development`. Don't commit directly to `development`, `staging`, or
  `main`.
- Open a pull request from your feature branch into `development` (not
  `main` or `staging`).
- A maintainer will review your PR, merge it into `development`, and handle
  promotion to `staging` and `main` from there.

### Before you open a PR

1. **Run the tests** — see [Quick start](README.md#quick-start) for how to
   set up the backend and frontend, then:

   ```bash
   cd backend
   ./.venv/Scripts/python.exe -m pytest tests/ -v
   ```

   Most tests need no database or LLM. If you changed frontend code:

   ```bash
   cd frontend
   npm install
   npx tsc --noEmit
   npm run build
   ```

2. **Keep your changes focused** — one feature or fix per PR. If you're
   tempted to fix unrelated things, open a separate PR for those.

3. **Follow existing code style** — match the patterns you see in
   neighboring files. The backend uses Python 3.12 with type hints; the
   frontend uses TypeScript with Tailwind + shadcn/ui.

4. **Update docs if needed** — if your change adds a new API route, env
   var, or setup step, update the relevant section in
   [`docs/TECHNICAL.md`](docs/TECHNICAL.md) and
   [`CHANGELOG.md`](CHANGELOG.md).

### What to expect in review

A maintainer will look at your PR and may ask for changes. This is normal —
it's not a rejection. Common things reviewers check:

- Does the change fit the engine/adapter pattern? (See
  [`docs/TECHNICAL.md`](docs/TECHNICAL.md) — nothing in
  `backend/app/engine/` may reference a specific adapter by name.)
- Are there tests for the new behavior?
- Does the change break any existing tests?
- Is the code style consistent with the surrounding code?

## Adding a new adapter

This project is built so new assessment standards can be added as adapters
without touching the engine. If you want to add one (e.g. for a different
data-quality framework), the high-level steps are:

1. Create `backend/app/adapters/<your-adapter>/` with `indicators.yaml`,
   `adapter.py`, `content.py`, and prompt templates — mirror the structure
   of `backend/app/adapters/fair/` or `backend/app/adapters/harmonization/`.
2. Register it in `backend/app/adapters/registry.py`.
3. Add it to `backend/scripts/seed_indicators.py`'s `_CONTENT_MODULES` list.
4. Write tests in `backend/tests/adapters/<your-adapter>/`.
5. Update `docs/TECHNICAL.md`'s API surface and repo layout sections.

See [`docs/DECISIONS.md`](docs/DECISIONS.md) for the design reasoning behind
the engine/adapter boundary.

## Questions?

If anything in this guide is unclear, feel free to
[open an issue](https://github.com/atwine/fair-maturity-copilot/issues/new)
with your question — we'll help and improve this guide based on what came up.
