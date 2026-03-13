from pydantic import BaseModel, Field


class FileLoadRequest(BaseModel):
    date_from: str = Field(..., min_length=8, max_length=8)
    date_to: str = Field(..., min_length=8, max_length=8)

