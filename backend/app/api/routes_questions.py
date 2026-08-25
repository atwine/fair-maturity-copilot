from fastapi import APIRouter, HTTPException

from app.adapters.registry import get_adapter
from app.api.schemas import QuestionOut

router = APIRouter(prefix="/adapters", tags=["questions"])


@router.get("/{adapter_id}/questions", response_model=list[QuestionOut])
def get_questions(adapter_id: str) -> list[QuestionOut]:
    try:
        adapter = get_adapter(adapter_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown adapter: {adapter_id!r}")

    return [
        QuestionOut(
            indicator_id=q.indicator.id,
            title=q.indicator.title,
            plain_language_question=q.indicator.plain_language_question,
            help_text=q.indicator.help_text,
            example=q.indicator.example,
            priority=q.indicator.priority,
            principle_group=q.indicator.principle_group,
            display_order=q.indicator.display_order,
            options=q.options,
        )
        for q in adapter.question_set()
    ]
