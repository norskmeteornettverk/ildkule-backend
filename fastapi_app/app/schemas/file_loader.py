from pydantic import BaseModel, Field


class FileLoadRequest(BaseModel):
    date_from: str = Field(
        ...,
        min_length=8,
        max_length=8,
        description="Inclusive start date for the import window, formatted as YYYYMMDD.",
    )
    date_to: str = Field(
        ...,
        min_length=8,
        max_length=8,
        description="Inclusive end date for the import window, formatted as YYYYMMDD.",
    )
