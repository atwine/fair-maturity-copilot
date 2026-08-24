# Roadmap

This project is one reusable engine (`intake → scoring → LLM remediation writer → report`) applied to more than one technical standard, one adapter at a time.

## v0 — FAIR data maturity adapter — **in planning**

Guided self-assessment against a subset of the RDA's 41 FAIR indicators, with LLM-generated plain-language remediation for each weak indicator.

- Status: planning prompt drafted (`docs/PLANNING_PROMPT.md`), not yet run through Plan Mode.
- First pilot: ACE's own data practices.
- No external dependency — can start immediately.

## v1 — OMOP CDM data-quality adapter — **tracked, parked**

Same engine, pointed at OHDSI's Data Quality Dashboard output (3,300+ automated checks against an OMOP CDM database) instead of FAIR indicators — translating dense, informaticist-oriented DQD reports into plain-language findings for non-technical data staff.

- Status: **blocked**, not started. Waiting on: TASO (The AIDS Support Organisation, Uganda) data access, and the team's still-open decision on source system and ETL path to OMOP CDM.
- Explicitly out of scope for this adapter: building a new ETL engine. Existing OpenMRS→OMOP tools ([jayasanka-sack/openmrs-to-omop](https://github.com/jayasanka-sack/openmrs-to-omop), [Hephaestus](https://github.com/dermatologist/hephaestus)) and the pan-African INSPIRE datahub already cover that layer — this adapter starts downstream, at an existing OMOP CDM database.
- **Revisit trigger:** when TASO's OMOP CDM data (via whichever ETL path the team lands on) is actually queryable, and once v0's engine/adapter boundary has been validated by a real pilot.

## Related, but a separate project

**Health-domain Luganda translation** (existing English↔Luganda seq2seq models + evaluation set, Sunbird fine-tune planned) is a strong, well-resourced idea but architecturally unrelated to this engine — it lives in its own repo when it starts. Parked until the team's in-flight evaluation of ~10,000 curated translation pairs is finalized. See `docs/background/` for the full scoping history.
