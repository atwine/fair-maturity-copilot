from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="fair-maturity-copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# Routers are added here as they're built (routes_assessment, routes_questions,
# routes_answers, routes_report — see docs/PLANNING_PROMPT.md milestones).
