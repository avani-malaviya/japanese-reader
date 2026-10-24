import base64
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.schemas import (
    ColumnOut,
    ColumnsOut,
    FigureOut,
    OcrResponse,
    PageItemOut,
    ParagraphOut,
    RubyOut,
)
from app.config import MAX_UPLOAD_BYTES
from app.services.regions.base import LayoutDetector
from app.services.regions.doclayout_detector import get_detector
from app.services.ocr.base import ColumnsItem, OcrEngine, PageItem, Paragraph
from app.services.ocr.mokuro_engine import get_engine
from app.services.ocr.service import InvalidImageError, read_page

router = APIRouter()


def ocr_engine() -> OcrEngine:
    return get_engine()


def layout_detector() -> LayoutDetector:
    return get_detector()


def to_out(item: PageItem) -> PageItemOut:
    if isinstance(item, ColumnsItem):
        return ColumnsOut(
            columns=[
                ColumnOut(width_ratio=c.width_ratio, items=[to_out(i) for i in c.items])
                for c in item.columns
            ]
        )
    if isinstance(item, Paragraph):
        return ParagraphOut(
            text=item.text,
            ruby=[RubyOut(**asdict(r)) for r in item.ruby],
            role=item.role,
            level=item.level,
        )
    src = "data:image/png;base64," + base64.b64encode(item.png).decode("ascii")
    return FigureOut(src=src, width_ratio=item.width_ratio, align=item.align)


# Sync handler on purpose: FastAPI runs it in a worker thread, so slow OCR doesn't block the server.
@router.post("/ocr", response_model=OcrResponse)
def ocr(
    image: Annotated[UploadFile, File()],
    engine: Annotated[OcrEngine, Depends(ocr_engine)],
    detector: Annotated[LayoutDetector, Depends(layout_detector)],
) -> OcrResponse:
    data = image.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large")
    try:
        result = read_page(engine, detector, data)
    except InvalidImageError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return OcrResponse(items=[to_out(item) for item in result.items], text=result.text)
