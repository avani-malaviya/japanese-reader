from fastapi import APIRouter

from app.api.schemas import ReadingOut, ReadingRequest, ReadingResponse
from app.services.reading import get_readings

router = APIRouter()


@router.post("/reading", response_model=ReadingResponse)
def reading(request: ReadingRequest) -> ReadingResponse:
    readings = get_readings(request.text, request.context, request.offset)
    return ReadingResponse(
        text=request.text,
        readings=[ReadingOut(**r.__dict__) for r in readings],
    )
