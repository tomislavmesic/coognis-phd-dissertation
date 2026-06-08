import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(slots=True)
class VectorRetrievalDocument:
    identifier: int
    content: str


@dataclass(slots=True)
class VectorRetrievalMatch:
    identifier: int
    score: float


class VectorRetrievalService:
    """Shared lightweight vector-space retrieval for local semantic-ish ranking."""

    @classmethod
    def normalize_text(cls, value: str) -> str:
        tokens = re.findall(r"[a-z0-9]+", (value or "").lower())
        normalized_tokens = [cls._normalize_token(token) for token in tokens]
        return " ".join(token for token in normalized_tokens if token)

    @staticmethod
    def _normalize_token(token: str) -> str:
        if len(token) <= 3:
            return token
        if token.endswith("ies") and len(token) > 4:
            return f"{token[:-3]}y"
        if token.endswith("ses") and len(token) > 5:
            return token[:-2]
        if token.endswith("xes") and len(token) > 5:
            return token[:-2]
        if token.endswith("zes") and len(token) > 5:
            return token[:-2]
        if token.endswith("ches") and len(token) > 6:
            return token[:-2]
        if token.endswith("shes") and len(token) > 6:
            return token[:-2]
        if token.endswith("s") and not token.endswith("ss") and len(token) > 4:
            return token[:-1]
        return token

    def rank_documents(
        self,
        *,
        query: str,
        documents: list[VectorRetrievalDocument],
        limit: int,
    ) -> list[VectorRetrievalMatch]:
        normalized_query = self.normalize_text(query)
        if not normalized_query or not documents or limit <= 0:
            return []

        prepared_documents = [
            (document, self.normalize_text(document.content))
            for document in documents
        ]
        corpus = [content for _, content in prepared_documents if content.strip()]
        valid_documents = [document for document, content in prepared_documents if content.strip()]
        if not corpus:
            return []

        vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            stop_words="english",
        )
        try:
            matrix = vectorizer.fit_transform([normalized_query, *corpus])
        except ValueError:
            return []

        if matrix.shape[1] == 0:
            return []

        query_vector = matrix[0:1]
        document_vectors = matrix[1:]
        similarities = cosine_similarity(query_vector, document_vectors).ravel()

        matches = [
            VectorRetrievalMatch(identifier=document.identifier, score=float(score))
            for document, score in zip(valid_documents, similarities, strict=False)
            if score > 0.0
        ]
        matches.sort(key=lambda item: (-item.score, item.identifier))
        return matches[:limit]
