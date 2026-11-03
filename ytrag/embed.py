import logging
from typing import Optional
from sentence_transformers import SentenceTransformer

from ytrag.config import settings

logger = logging.getLogger("ytrag.embed")


class Embedder:
    """Embedding generation abstraction wrapping Sentence Transformers."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embed_model
        logger.info(f"Loading embedding model: {self.model_name}...")
        self._model = SentenceTransformer(self.model_name)
        # Determine vector dimensionality
        test_vec = self._model.encode("test", normalize_embeddings=True)
        self._dim = int(len(test_vec))
        logger.info(f"Embedding model loaded. Dimension: {self._dim}")

    @property
    def dim(self) -> int:
        """Vector dimensionality."""
        return self._dim

    def embed_documents(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Embed a list of chunk document texts with batching and normalization."""
        if not texts:
            return []
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 20,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string for semantic vector search."""
        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()


# Singleton cached embedder instance
_cached_embedder: Optional[Embedder] = None


def get_embedder(model_name: Optional[str] = None) -> Embedder:
    """Get or initialize singleton Embedder instance."""
    global _cached_embedder
    target_name = model_name or settings.embed_model
    if _cached_embedder is None or _cached_embedder.model_name != target_name:
        _cached_embedder = Embedder(model_name=target_name)
    return _cached_embedder
