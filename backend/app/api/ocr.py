from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.schemas import OcrResponse, ParagraphOut
from app.config import MAX_UPLOAD_BYTES
from app.services.ocr.base import OcrEngine
from app.services.ocr.mokuro_engine import get_engine
from app.services.ocr.service import InvalidImageError, read_page

router = APIRouter()


def ocr_engine() -> OcrEngine:
    return get_engine()


# Sync handler on purpose: FastAPI runs it in a worker thread, so slow OCR doesn't block the server.
@router.post("/ocr", response_model=OcrResponse)
def ocr(
    image: Annotated[UploadFile, File()],
    engine: Annotated[OcrEngine, Depends(ocr_engine)],
) -> OcrResponse:
    data = image.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large")
    try:
        result = read_page(engine, data)
    except InvalidImageError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return OcrResponse(items=[ParagraphOut(text=p) for p in result.paragraphs], text=result.text)
