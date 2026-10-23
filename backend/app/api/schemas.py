from typing import Literal

from pydantic import BaseModel, Field

from app.config import MAX_CONTEXT_CHARS, MAX_LOOKUP_CHARS


class OcrResponse(BaseModel):
    paragraphs: list[str]
    text: str


class ReadingRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_LOOKUP_CHARS)
    # The paragraph the selection sits in, and where in it, so readings can follow context.
    context: str | None = Field(default=None, max_length=MAX_CONTEXT_CHARS)
    offset: int | None = Field(default=None, ge=0)


class ReadingOut(BaseModel):
    kana: str
    label: str
    kind: Literal["on", "kun", "word"]
    contextual: bool


class ReadingResponse(BaseModel):
    text: str
    readings: list[ReadingOut]
