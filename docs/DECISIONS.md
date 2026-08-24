# Decision log

How this project got scoped down from ten ideas to one, in order.

## v1 — ten ideas

Started broad: researched ACE's actual mandate (bioinformatics/data science, AMR, genomics — via ace.ac.ug), the existing open-source landscape (Sunbird AI for Luganda MT, Jacaranda's UlizaMama and Rwanda's Mbaza RBC for health chatbots, H3Africa/H3ABioNet for genomic infrastructure), and current funder priorities (Gates Foundation's EVAH initiative, Gates+OpenAI's Horizon 1000, the Gates/Google.org/Masakhane LINGUA Africa call) to produce ten scored candidate ideas. Full report: `background/v1-ten-ideas-for-ace.html`.

## v2 — four ideas

Cut based on direct feedback: the project owner is a developer and strategic/technical lead, not a bioinformatician, and wanted things he could personally build and debug — not hand off to deep domain specialists. Dropped AMR/WGS prediction, the federated genomic data-sharing toolkit, the pathogen genomics dashboard, and the pipeline-reproducibility tool on that basis. Also dropped a generic NCD chatbot and a crop-disease/Luganda voice tool as explicitly out of scope. Kept and refined: Luganda health-domain MT (flagship, since real assets already exist), a grant/manuscript-writing copilot, a FAIR data maturity tool, and a DHIS2 anomaly-detection tool. Full report: `background/v2-refined-ideas-for-ace.html`.

## v3 — two ideas, one engine

Further feedback: the grant-writing copilot was dropped on adoption-risk grounds (colleagues already have their own tools and wouldn't switch). The DHIS2 idea was replaced after new context surfaced — real, pending data access at TASO (The AIDS Support Organisation, Uganda), with an OMOP CDM/OHDSI architecture already being scoped by the team for federated analysis. Research showed a full OMOP ETL platform would duplicate existing work (INSPIRE datahub, several OpenMRS→OMOP ETL attempts), but that OHDSI's own Data Quality Dashboard output is dense and expert-oriented — the same gap shape as the FAIR maturity tool. Reframed both as one reusable engine (`intake → scoring → LLM remediation writer → report`) with a FAIR adapter and a future OMOP adapter. Full report: `background/v3-two-ideas-one-engine.html`.

## v4 — build order confirmed

FAIR adapter (idea #3) confirmed as the build-first project: no external data dependency, can start immediately, and validates the shared engine before the OMOP adapter depends on it. OMOP adapter (idea #4) tracked in `../ROADMAP.md` as parked, blocked on TASO's data access and ETL-path decision. Luganda MT (idea #1) confirmed strong but separately parked, pending the team's in-flight evaluation of ~10,000 curated translation pairs — it will live in its own repo when it starts, since it doesn't share the engine/adapter architecture.

## v5 — plan approved, engine scaffold built, process corrections

The v0 plan (indicator subset, data model, questionnaire flow, prompt design, milestones, eval approach) was produced via Plan Mode and approved. Two choices were made during planning that diverged from the plan's own default recommendations: Next.js was chosen over the plan's suggested server-rendered Jinja2+htmx frontend, and LLM serving was set to two verified on-prem OpenAI-compatible endpoints (local Ollama for dev, vLLM-hosted Llama 3.3 70B for pilot) rather than the plan's original hosted-third-party-API-for-dev suggestion — this removed any external data-exposure question entirely, since nothing leaves the local network at any stage.

Two process corrections landed alongside the first implementation checkpoint: the repo had been committed directly to a shared branch, against the standing branching convention — corrected by renaming `master` to `main` and moving to a feature-branch workflow with mandatory self-review before merge (see `README.md`). And the plan's day-based milestone estimates were replaced with checkpoint tracking in `ROADMAP.md`, since they assumed unassisted solo development and didn't match the actual pace of Claude-assisted implementation.

## v6 — branching corrected to the full three-tier structure

The v5 branching fix was incomplete: it moved work to a feature branch before merging into `main`, but skipped the staging tier and the PR-gated production step the user's CLAUDE.md actually specifies. Corrected to the literal three-tier structure: `feature/<name>` → `development` → `staging` → `main`, with `main` reachable only via a reviewed, explicitly-approved PR from `staging`. The already-merged backend scaffold on `main` stays as a one-time, explicitly-approved exception rather than a history rewrite — everything from this point on goes through the full structure. GitHub branch protection on `main` was attempted as a platform-enforced backstop and found unavailable on a private repo below GitHub Pro; noted as an option, not pursued. See `README.md`'s "Branching convention" for the canonical, current description.
