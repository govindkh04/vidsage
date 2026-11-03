import logging
import uuid
from typing import Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from ytrag.config import settings
from ytrag.embed import get_embedder
from ytrag.models import Chunk

logger = logging.getLogger("ytrag.qdrant")

# Namespace UUID for generating deterministic UUIDs from chunk IDs
NAMESPACE_VIDSAGE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def chunk_id_to_uuid(chunk_id: str) -> str:
    """Generate a deterministic UUID from chunk ID (e.g., 'VIDEO_ID:724')."""
    return str(uuid.uuid5(NAMESPACE_VIDSAGE, chunk_id))


class QdrantService:
    """Service for managing Qdrant vector collection, indexing, and retrieval."""

    def __init__(self):
        settings.validate_for_indexing()
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=30.0,
        )
        self.collection_name = settings.collection_name
        self.embedder = get_embedder()
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create the collection if it does not exist, enforcing vector dimension."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            logger.info(
                f"Creating Qdrant collection '{self.collection_name}' with dimension {self.embedder.dim} (Cosine)..."
            )
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.embedder.dim,
                    distance=qmodels.Distance.COSINE,
                ),
            )
            # Create payload index on video_id for filtering
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="video_id",
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )
        else:
            # Check dimension compatibility
            info = self.client.get_collection(self.collection_name)
            existing_size = info.config.params.vectors.size
            if existing_size != self.embedder.dim:
                raise ValueError(
                    f"Collection '{self.collection_name}' exists with vector dimension {existing_size}, "
                    f"but active embedding model produces dimension {self.embedder.dim}. "
                    "Use a collection name matching the embedding dimension (e.g. 'dsa_lectures_1024')."
                )

    def upsert_chunks(self, chunks: list[Chunk], batch_size: int = 64) -> int:
        """Batch embed and upsert chunks into Qdrant using deterministic UUIDs."""
        if not chunks:
            return 0

        logger.info(f"Embedding and upserting {len(chunks)} chunks into '{self.collection_name}'...")
        total_upserted = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.text for c in batch]
            embeddings = self.embedder.embed_documents(texts)

            points = []
            for chunk, vector in zip(batch, embeddings):
                point_id = chunk_id_to_uuid(chunk.chunk_id)
                payload = {
                    "chunk_id": chunk.chunk_id,
                    "video_id": chunk.video_id,
                    "video_title": chunk.video_title,
                    "start_sec": chunk.start_sec,
                    "end_sec": chunk.end_sec,
                    "text": chunk.text,
                    "source_url": chunk.source_url,
                }
                points.append(
                    qmodels.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload,
                    )
                )

            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True,
            )
            total_upserted += len(points)
            logger.info(f"Upserted {total_upserted}/{len(chunks)} chunks.")

        return total_upserted

    def search(
        self,
        query: str,
        top_k: int = 6,
        video_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Retrieve most relevant chunks from Qdrant for a query with optional video filtering."""
        query_vector = self.embedder.embed_query(query)

        query_filter = None
        if video_id:
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="video_id",
                        match=qmodels.MatchValue(value=video_id),
                    )
                ]
            )

        # Use query_points (or search)
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        ).points

        retrieved: list[dict[str, Any]] = []
        for r in results:
            payload = r.payload or {}
            retrieved.append(
                {
                    "score": float(r.score),
                    "chunk_id": payload.get("chunk_id"),
                    "video_id": payload.get("video_id"),
                    "video_title": payload.get("video_title"),
                    "start_sec": payload.get("start_sec"),
                    "end_sec": payload.get("end_sec"),
                    "text": payload.get("text"),
                    "source_url": payload.get("source_url"),
                }
            )

        return retrieved

    def stats(self) -> dict[str, Any]:
        """Return collection indexing statistics."""
        info = self.client.get_collection(self.collection_name)
        return {
            "collection_name": self.collection_name,
            "points_count": info.points_count,
            "vector_size": info.config.params.vectors.size,
            "distance": str(info.config.params.vectors.distance),
            "status": str(info.status),
            "embed_model": self.embedder.model_name,
        }
