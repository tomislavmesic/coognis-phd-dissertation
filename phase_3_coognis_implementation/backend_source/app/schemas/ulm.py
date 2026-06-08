from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class UlmIngestRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    document: str | None = Field(default=None, min_length=1)
    url: str | None = Field(default=None, max_length=2048)

    @model_validator(mode="after")
    def validate_source_input(self):
        if bool(self.document) == bool(self.url):
            raise ValueError("Provide exactly one of 'document' or 'url'.")
        return self


class SourceDocumentResponse(BaseModel):
    id: int
    title: str | None
    content: str | None
    url: str | None
    chunk_index: int
    chunk_count: int
    indexing_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeSourceResponse(BaseModel):
    id: int
    source_type: str
    source_value: str
    indexing_status: str
    created_at: datetime
    documents: list[SourceDocumentResponse]

    model_config = {"from_attributes": True}


class KnowledgeSourceListResponse(BaseModel):
    items: list[KnowledgeSourceResponse]
    total: int


class RetrievedChunk(BaseModel):
    source_id: int | None = None
    document_id: int | None = None
    title: str | None = None
    chunk_index: int | None = None
    source_type: str | None = None
    url: str | None = None
    score: float | None = None
    content: str = Field(min_length=1)


class UlmRetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=10)


class UlmGenerateRequest(BaseModel):
    query: str = Field(min_length=1)
    retrieved_chunks: list[RetrievedChunk] = Field(min_length=1)


class UlmGeneratedSource(BaseModel):
    source_id: int | None = None
    document_id: int | None = None
    title: str | None = None
    chunk_index: int | None = None
    url: str | None = None


class UlmGenerateResponse(BaseModel):
    explanation: str
    sources: list[UlmGeneratedSource]


class UlmRetrievedContext(BaseModel):
    retrieved_chunks: list[RetrievedChunk]
