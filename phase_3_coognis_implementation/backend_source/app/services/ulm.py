import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db_session
from app.core.config import settings
from app.models import KnowledgeSource, SourceDocument
from app.schemas.ulm import (
    KnowledgeSourceListResponse,
    KnowledgeSourceResponse,
    RetrievedChunk,
    UlmRetrievedContext,
    UlmRetrieveRequest,
    UlmGenerateRequest,
    UlmGenerateResponse,
    UlmGeneratedSource,
    UlmIngestRequest,
)
from app.services.local_llm import LocalLlmClient, get_llm_client_from_db
from app.services.vector_retrieval import VectorRetrievalDocument, VectorRetrievalService


class UlmService:
    """Persistence service for the ULM ingestion module."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.vector_retrieval_service = VectorRetrievalService()

    def ingest(self, payload: UlmIngestRequest) -> KnowledgeSourceResponse:
        if payload.document:
            source_type = "document"
            source_value = self._truncate_source_value(payload.document)
        else:
            source_type = "url"
            source_value = payload.url or ""

        source = KnowledgeSource(
            source_type=source_type,
            source_value=source_value,
            indexing_status="queued",
        )
        self.db.add(source)
        self.db.flush()

        if payload.document:
            self._index_document_source(
                source=source,
                title=payload.title,
                content=payload.document,
                url=None,
            )
        else:
            try:
                fetched_title, fetched_text = self._fetch_url_text(payload.url or "")
                resolved_title = (payload.title or fetched_title or payload.url or "").strip() or None
                self._index_document_source(
                    source=source,
                    title=resolved_title,
                    content=fetched_text,
                    url=payload.url,
                )
            except ValueError:
                source.indexing_status = "failed"
                self.db.commit()
                raise

        self.db.commit()
        return self.get_source(source.id)

    def get_source(self, source_id: int) -> KnowledgeSourceResponse:
        statement = (
            select(KnowledgeSource)
            .options(selectinload(KnowledgeSource.documents))
            .where(KnowledgeSource.id == source_id)
        )
        source = self.db.execute(statement).scalar_one()
        return KnowledgeSourceResponse.model_validate(source)

    def list_sources(self) -> KnowledgeSourceListResponse:
        statement = select(KnowledgeSource).options(selectinload(KnowledgeSource.documents)).order_by(
            KnowledgeSource.id.asc()
        )
        sources = self.db.execute(statement).scalars().all()
        return KnowledgeSourceListResponse(
            items=[KnowledgeSourceResponse.model_validate(source) for source in sources],
            total=len(sources),
        )

    def build_generation_prompt(self, payload: UlmGenerateRequest) -> str:
        chunk_blocks = []
        for index, chunk in enumerate(payload.retrieved_chunks, start=1):
            title = chunk.title or f"Chunk {index}"
            chunk_blocks.append(f"[{index}] {title}\n{chunk.content}")

        context = "\n\n".join(chunk_blocks)
        return (
            "You are ULM, generating a helpful explanation from retrieved external knowledge.\n\n"
            f"User query:\n{payload.query}\n\n"
            f"Retrieved context:\n{context}\n\n"
            "Rules:\n"
            "- Use only the retrieved context.\n"
            "- Do not invent policies, facts, or steps that are not supported by the retrieved context.\n"
            "- If the retrieved context is incomplete, say what is still missing.\n"
            "- Prefer a concise, practical answer.\n"
            "- When useful, separate the direct answer from a short note about limitations.\n"
        )

    def generate(self, payload: UlmGenerateRequest, llm_client: LocalLlmClient) -> UlmGenerateResponse:
        prompt = self.build_generation_prompt(payload)
        explanation = llm_client.generate(prompt)
        sources = [
            UlmGeneratedSource(
                source_id=chunk.source_id,
                document_id=chunk.document_id,
                title=chunk.title,
                chunk_index=chunk.chunk_index,
                url=chunk.url,
            )
            for chunk in payload.retrieved_chunks
        ]
        return UlmGenerateResponse(explanation=explanation, sources=sources)

    def retrieve(self, payload: UlmRetrieveRequest) -> UlmRetrievedContext:
        return self.retrieve_context(query=payload.query, limit=payload.limit)

    def retrieve_context(self, *, query: str | None = None, limit: int = 3) -> UlmRetrievedContext:
        statement = (
            select(SourceDocument, KnowledgeSource.source_type)
            .join(KnowledgeSource, KnowledgeSource.id == SourceDocument.knowledge_source_id)
            .where(
                SourceDocument.indexing_status == "indexed",
                SourceDocument.content.is_not(None),
            )
            .order_by(SourceDocument.id.asc())
        )
        rows = self.db.execute(statement).all()
        documents = [row[0] for row in rows]
        source_types_by_document_id = {row[0].id: row[1] for row in rows}

        ranked_documents = documents
        vector_scores: dict[int, float] = {}
        if query and query.strip():
            vector_matches = self.vector_retrieval_service.rank_documents(
                query=query,
                documents=[
                    VectorRetrievalDocument(
                        identifier=document.id,
                        content=" ".join(
                            part.strip()
                            for part in [document.title or "", document.content or "", document.url or ""]
                            if part and part.strip()
                        ),
                    )
                    for document in documents
                ],
                limit=max(limit * 4, limit),
            )
            vector_scores = {match.identifier: match.score for match in vector_matches}
            ranked_document_ids = [match.identifier for match in vector_matches]
            ranked_document_map = {document.id: document for document in documents}
            ranked_documents = [
                ranked_document_map[document_id]
                for document_id in ranked_document_ids
                if document_id in ranked_document_map
            ]
            ranked_documents = [
                document
                for document in ranked_documents
                if vector_scores.get(document.id, 0.0) >= settings.ulm_retrieval_min_score
            ]

        if not ranked_documents and not query:
            ranked_documents = documents

        chunks = [
            RetrievedChunk(
                source_id=document.knowledge_source_id,
                document_id=document.id,
                title=document.title,
                chunk_index=document.chunk_index,
                source_type=source_types_by_document_id.get(document.id),
                url=document.url,
                score=vector_scores.get(document.id),
                content=document.content or document.url or "",
            )
            for document in ranked_documents[:limit]
            if (document.content or document.url)
        ]
        return UlmRetrievedContext(retrieved_chunks=chunks)

    @staticmethod
    def _truncate_source_value(value: str, *, max_length: int = 2048) -> str:
        normalized = re.sub(r"\s+", " ", (value or "").strip())
        if len(normalized) <= max_length:
            return normalized
        return normalized[:max_length].rstrip()

    @staticmethod
    def _build_chunk_title(title: str | None, chunk_index: int, chunk_count: int) -> str | None:
        base_title = (title or "").strip()
        if not base_title:
            return None
        if chunk_count <= 1:
            return base_title
        return f"{base_title} (Chunk {chunk_index + 1}/{chunk_count})"

    def _index_document_source(
        self,
        *,
        source: KnowledgeSource,
        title: str | None,
        content: str,
        url: str | None,
    ) -> None:
        chunks = self._chunk_text(content)
        if not chunks:
            raise ValueError("No usable text could be indexed from the provided source.")
        chunk_count = len(chunks)
        for chunk_index, chunk_content in enumerate(chunks):
            self.db.add(
                SourceDocument(
                    knowledge_source_id=source.id,
                    title=self._build_chunk_title(title, chunk_index, chunk_count),
                    content=chunk_content,
                    url=url,
                    chunk_index=chunk_index,
                    chunk_count=chunk_count,
                    indexing_status="indexed",
                )
            )

        source.indexing_status = "indexed"

    def _fetch_url_text(self, url: str) -> tuple[str | None, str]:
        normalized_url = (url or "").strip()
        if not normalized_url:
            raise ValueError("A source URL is required.")

        parsed = urlparse(normalized_url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Only http and https URLs are supported for ULM ingestion.")

        headers = {
            "User-Agent": settings.ulm_url_user_agent,
            "Accept": "text/html,application/xhtml+xml",
        }

        try:
            response = httpx.get(
                normalized_url,
                headers=headers,
                follow_redirects=True,
                timeout=settings.ulm_url_fetch_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ValueError(f"Unable to fetch the URL content: {exc}") from exc

        content_type = (response.headers.get("content-type") or "").lower()
        if "html" not in content_type and "text/plain" not in content_type:
            raise ValueError("The URL did not return a supported text or HTML document.")

        body = response.text or ""
        cleaned_text, page_title = self._extract_clean_page_text(body)
        if not cleaned_text:
            raise ValueError("No useful text could be extracted from the URL.")

        max_chars = max(settings.ulm_url_max_content_chars, settings.ulm_chunk_size_chars)
        if len(cleaned_text) > max_chars:
            cleaned_text = cleaned_text[:max_chars].rstrip()

        return page_title, cleaned_text

    def _extract_clean_page_text(self, html: str) -> tuple[str, str | None]:
        soup = BeautifulSoup(html or "", "html.parser")

        page_title = soup.title.get_text(" ", strip=True) if soup.title else None

        for selector in [
            "script",
            "style",
            "noscript",
            "svg",
            "img",
            "picture",
            "figure",
            "iframe",
            "canvas",
            "video",
            "audio",
            "form",
            "button",
            "input",
            "select",
            "textarea",
            "nav",
            "header",
            "footer",
            "aside",
        ]:
            for element in soup.select(selector):
                element.decompose()

        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find(attrs={"role": "main"})
            or soup.body
            or soup
        )

        for element in main.find_all(True):
            attrs_dict = element.attrs or {}
            attrs = " ".join(
                str(value)
                for key, value in attrs_dict.items()
                if key in {"class", "id", "role", "aria-label"}
            ).lower()
            if any(
                token in attrs
                for token in {
                    "cookie",
                    "consent",
                    "banner",
                    "breadcrumbs",
                    "breadcrumb",
                    "sidebar",
                    "social",
                    "share",
                    "promo",
                    "advert",
                    "newsletter",
                    "related",
                    "recommend",
                    "comment",
                    "pagination",
                }
            ):
                element.decompose()

        text = main.get_text("\n", strip=True)
        cleaned_lines: list[str] = []
        seen_lines: set[str] = set()

        for raw_line in text.splitlines():
            line = re.sub(r"\s+", " ", raw_line).strip()
            if len(line) < 2:
                continue
            if line.lower() in seen_lines:
                continue
            seen_lines.add(line.lower())
            cleaned_lines.append(line)

        cleaned_text = "\n".join(cleaned_lines)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()

        return cleaned_text, page_title

    def _chunk_text(self, value: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", (value or "").strip())
        if not normalized:
            return []

        chunk_size = max(settings.ulm_chunk_size_chars, 200)
        overlap = max(min(settings.ulm_chunk_overlap_chars, chunk_size - 50), 0)

        chunks: list[str] = []
        start = 0
        while start < len(normalized):
            tentative_end = min(start + chunk_size, len(normalized))
            end = self._snap_chunk_end(normalized, start=start, tentative_end=tentative_end, chunk_size=chunk_size)

            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= len(normalized):
                break
            tentative_start = max(end - overlap, start + 1)
            start = self._snap_chunk_start(normalized, tentative_start)

        return chunks or [normalized]

    @staticmethod
    def _snap_chunk_end(value: str, *, start: int, tentative_end: int, chunk_size: int) -> int:
        if tentative_end >= len(value):
            return len(value)

        window = value[start:tentative_end]
        sentence_boundary = max(window.rfind(". "), window.rfind("? "), window.rfind("! "))
        if sentence_boundary > max(100, chunk_size // 3):
            return start + sentence_boundary + 1

        whitespace_boundary = window.rfind(" ")
        if whitespace_boundary > max(80, chunk_size // 4):
            return start + whitespace_boundary

        while tentative_end < len(value) and not value[tentative_end].isspace():
            tentative_end += 1

        return tentative_end

    @staticmethod
    def _snap_chunk_start(value: str, tentative_start: int) -> int:
        if tentative_start <= 0:
            return 0
        if tentative_start >= len(value):
            return len(value)

        sentence_match = re.search(r"(?<=[.!?])\s+", value[tentative_start:])
        if sentence_match is not None:
            sentence_start = tentative_start + sentence_match.end()
            if sentence_start < len(value):
                return sentence_start

        start = tentative_start
        while start < len(value) and value[start].isspace():
            start += 1
        if start >= len(value):
            return len(value)

        if start > 0 and not value[start - 1].isspace():
            while start < len(value) and not value[start].isspace():
                start += 1
            while start < len(value) and value[start].isspace():
                start += 1

        return start


def get_llm_client(
    db: Session = Depends(get_db_session),
) -> LocalLlmClient:
    return get_llm_client_from_db(db)
