from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_answers, routes_assessment, routes_plan, routes_questions, routes_report
from app.config import settings

app = FastAPI(title="fair-maturity-copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_questions.router)
app.include_router(routes_assessment.router)
app.include_router(routes_answers.router)
app.include_router(routes_report.router)
app.include_router(routes_plan.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
