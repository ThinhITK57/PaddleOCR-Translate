from pydantic import BaseModel
from typing import List


class OCRResult(BaseModel):
    page: int
    text: str


class OCRResponse(BaseModel):
    results: List[OCRResult]
