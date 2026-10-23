from pydantic import BaseModel


class OcrResponse(BaseModel):
    paragraphs: list[str]
    text: str
