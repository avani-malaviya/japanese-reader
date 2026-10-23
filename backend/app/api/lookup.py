from dataclasses import asdict

from fastapi import APIRouter

from app.api.schemas import (
    MeaningRequest,
    MeaningResponse,
    ReadingOut,
    ReadingRequest,
    ReadingResponse,
)
from app.config import MAX_MEANING_ENTRIES
from app.services.meaning import get_meaning
from app.services.reading import get_readings

router = APIRouter()


@router.post("/reading", response_model=ReadingResponse)
def reading(request: ReadingRequest) -> ReadingResponse:
    readings = get_readings(request.text, request.context, request.offset)
    return ReadingResponse(
        text=request.text,
        readings=[ReadingOut(**asdict(r)) for r in readings],
    )


@router.post("/meaning", response_model=MeaningResponse)
def meaning(request: MeaningRequest) -> MeaningResponse:
    result = get_meaning(request.text, MAX_MEANING_ENTRIES)
    return MeaningResponse.model_validate(
        {"text": request.text, "looked_up": result.looked_up, "entries": [asdict(e) for e in result.entries]}
    )
