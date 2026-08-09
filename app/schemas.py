from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=20000,
        description="The raw text that needs to be summarized",
        examples=["FastAPI is a modern, fast web framework for building APIs with Python..."],
    )
    max_words: int = Field(
        default=60,
        ge=10,
        le=500,
        description="Rough target length for the summary, in words",
    )


class SummarizeResponse(BaseModel):
    summary: str
    original_length_words: int
    summary_length_words: int


class ErrorResponse(BaseModel):
    detail: str

class ClassifyRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=20000,
        description="The customer message or text to classify",
        examples=["My payment was deducted but my order was cancelled."],
    )


class ClassifyResponse(BaseModel):
    intent: str
    priority: str
    sentiment: str
    requires_human: bool