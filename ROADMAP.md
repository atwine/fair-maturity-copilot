# Roadmap

This project is one reusable engine (`intake → scoring → LLM remediation writer → report`) applied to more than one technical standard, one adapter at a time.

**A note on timelines:** the original plan (`docs/PLANNING_PROMPT.md` output) estimated work in developer-days, assuming solo, unassisted implementation. In practice, with Claude doing most of the actual writing, a "day" of that plan can take a fraction of a working session — the first checkpoint below took well under a day. Below is tracked as **checkpoints**, not calendar days; how fast they land depends on session time and review turnaround, not headcount-style estimation. The detailed technical plan each checkpoint follows still lives in the approved plan file referenced in `devlog/HANDOFF.md`.

## v0 — FAIR data maturity adapter — **in progress**

Guided self-assessment against a subset of the RDA's 41 FAIR indicators, with LLM-generated plain-language remediation for each weak indicator.

- [x] **Checkpoint 1 — engine scaffold + boundary proof.** FastAPI app, SQLModel data model, the `Adapter` Protocol seam, dual-provider (Ollama/vLLM) LLM client, remediation grounding checks. Proven with a fake adapter before any FAIR content exists (`backend/tests/engine/test_boundary.py`, passing).
- [x] **Checkpoint 2 — FAIR adapter content.** `indicators.yaml` (the 12 selected RDA indicators, flex-slot resolved to F3-01M — see `docs/DECISIONS.md`), `FairAdapter.score()`, `scripts/seed_indicators.py`. Tested against SQLite (no Neon project yet) — seed script confirmed idempotent on a second run.
- [ ] **Checkpoint 3 — synthetic demo dataset(s).** A small library of fake, realistic "datasets being assessed" — varied sizes/formats/domains — so the tool can be demoed and dogfooded end-to-end without waiting on real ACE data, and without ever needing to run real institutional data through an LLM before that's actually been cleared. See the note below — this matters even more once the OMOP adapter exists.
- [ ] **Checkpoint 4 — backend REST API.** Assessment/question/answer/report routes, CORS, exercised manually before any frontend exists.
- [ ] **Checkpoint 5 — Next.js frontend.** Scaffold, shadcn setup, the 4-screen wizard (new → question → review → report) against the API contract.
- [ ] **Checkpoint 6 — remediation writer live.** Prompt template wired to the engine, hand-reviewed output against the Ollama dev endpoint, tested against the synthetic datasets from Checkpoint 3.
- [ ] **Checkpoint 7 — eval harness.** Golden-set regression suite; prompt iterated until it passes.
- [ ] **Checkpoint 8 — switch to pilot LLM.** Point at the vLLM Llama 3.3 70B endpoint, confirm eval scores hold.
- [ ] **Checkpoint 9 — deploy + dogfood.** Both services on Railway; a full self-run against real ACE data.
- [ ] **Checkpoint 10 — real ACE pilot.** A non-developer stakeholder runs it unassisted; feedback becomes new golden-set cases and indicator-subset corrections.

First pilot user: ACE's own data practices. No external dependency — already underway.

**Why the synthetic dataset checkpoint matters beyond just having a demo:** real institutional data — and especially anything OMOP CDM/health-record-shaped for the future v1 adapter — likely carries data-governance and consent restrictions that make sending it to *any* LLM (even an on-prem one) a real policy question, not just a technical one. A well-built synthetic dataset (varied sizes, formats, and plausible-but-fake governance gaps) lets the tool be built, tested, and demonstrated end-to-end without that question ever blocking progress — and gives a safe default for showing the tool to people outside ACE later. Building this early (Checkpoint 3, right after the indicator content) rather than bolting it on at the end.

## v1 — OMOP CDM data-quality adapter — **tracked, parked**

Same engine, pointed at OHDSI's Data Quality Dashboard output (3,300+ automated checks against an OMOP CDM database) instead of FAIR indicators — translating dense, informaticist-oriented DQD reports into plain-language findings for non-technical data staff.

- Status: **blocked**, not started. Waiting on: TASO (The AIDS Support Organisation, Uganda) data access, and the team's still-open decision on source system and ETL path to OMOP CDM.
- Explicitly out of scope for this adapter: building a new ETL engine. Existing OpenMRS→OMOP tools ([jayasanka-sack/openmrs-to-omop](https://github.com/jayasanka-sack/openmrs-to-omop), [Hephaestus](https://github.com/dermatologist/hephaestus)) and the pan-African INSPIRE datahub already cover that layer — this adapter starts downstream, at an existing OMOP CDM database.
- **Revisit trigger:** when TASO's OMOP CDM data (via whichever ETL path the team lands on) is actually queryable, and once v0's engine/adapter boundary has been validated by a real pilot.
- **Data-governance note carried over from v0's Checkpoint 3:** real TASO/OMOP data almost certainly needs a cleared policy path before it can touch any LLM, on-prem or not. Plan for this adapter to be built and demoed against synthetic OMOP-shaped Data Quality Dashboard output first, with real data substituted in only after that's explicitly cleared — not the other way around.

## Related, but a separate project

**Health-domain Luganda translation** (existing English↔Luganda seq2seq models + evaluation set, Sunbird fine-tune planned) is a strong, well-resourced idea but architecturally unrelated to this engine — it lives in its own repo when it starts. Parked until the team's in-flight evaluation of ~10,000 curated translation pairs is finalized. See `docs/background/` for the full scoping history.
