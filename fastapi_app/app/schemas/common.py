from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str = Field(..., description="Human-readable success message.")


class MsgResponse(BaseModel):
    msg: str = Field(..., description="Short status message.")


class ErrorDetailResponse(BaseModel):
    detail: str = Field(..., description="Error detail message.")
