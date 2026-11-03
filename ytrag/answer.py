import logging
import re
from typing import Any, Optional

from ytrag.config import settings
from ytrag.index import search as qdrant_search
from ytrag.models import Citation, format_timestamp
from ytrag.services.groq_service import generate_completion

logger = logging.getLogger("ytrag.answer")

SYSTEM_PROMPT = """You are VidSage, an educational assistant that answers questions using retrieved excerpts from the user's YouTube lectures.

The retrieved transcripts may contain speech recognition errors.
Answer only using information directly supported by the supplied lecture excerpts.
Do not use your general training knowledge to speculate or fill gaps.
If the excerpts do not clearly explain the requested topic, say:
'Ye topic in lectures me cover nahi hua.'

Match the language of the user's question.
For Hinglish questions, answer naturally in Hinglish.
Keep answers concise and suitable for exam/interview revision (around 4-6 sentences).
Cite the relevant excerpts using their citation identifiers like [1], [2].
Never invent lecture titles, video IDs, timestamps, or source links."""


def extract_citation_indices(text: str) -> list[int]:
    """Extract 1-based citation indices like [1], [2], [3] from generated answer."""
    matches = re.findall(r"\[(\d+)\]", text)
    indices: list[int] = []
    for m in matches:
        idx = int(m)
        if idx not in indices:
            indices.append(idx)
    return indices


def build_context_block(retrieved_chunks: list[dict[str, Any]]) -> str:
    """Format retrieved lecture chunks into a numbered context block for LLM prompting."""
    blocks: list[str] = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        title = chunk.get("video_title", "Unknown Lecture")
        start_t = format_timestamp(chunk.get("start_sec", 0))
        end_t = format_timestamp(chunk.get("end_sec", 0))
        # Remove title prefix from chunk text to avoid redundancy
        raw_text = chunk.get("text", "")
        lines = raw_text.split("\n\n", 1)
        body = lines[1] if len(lines) > 1 else lines[0]

        block = (
            f"[{i}] Lecture: {title}\n"
            f"Timestamp: {start_t} - {end_t}\n"
            f"Excerpt:\n{body.strip()}"
        )
        blocks.append(block)
    return "\n\n".join(blocks)


def answer(
    question: str,
    top_k: Optional[int] = None,
    max_distance: Optional[float] = None,
    rewind_sec: int = 5,
) -> dict[str, Any]:
    """Retrieve relevant lecture chunks, apply relevance filtering, generate grounded answer via Groq LLM, and validate citations.
    
    Returns:
        dict: {
            "question": str,
            "answer": str,
            "grounded": bool,
            "citations": list[dict],
            "retrieved_count": int,
        }
    """
    settings.validate_for_answering()
    effective_top_k = top_k if top_k is not None else settings.top_k
    threshold = max_distance if max_distance is not None else settings.max_distance

    # 1. Vector retrieval from Qdrant
    logger.info(f"Retrieving top {effective_top_k} chunks for: '{question}'")
    raw_results = qdrant_search(query=question, top_k=effective_top_k)

    if not raw_results:
        logger.info("Zero chunks retrieved from vector search.")
        return {
            "question": question,
            "answer": "Ye topic in lectures me cover nahi hua.",
            "grounded": False,
            "citations": [],
            "retrieved_count": 0,
        }

    # 2. Relevance filtering
    # In Qdrant Cosine distance, score is cosine similarity in [-1, 1]
    filtered_results = [r for r in raw_results if r.get("score", 0.0) >= threshold]
    if not filtered_results:
        logger.info(
            f"All retrieved chunks scored below threshold {threshold} "
            f"(best score: {raw_results[0].get('score', 0):.3f}). Refusing to answer."
        )
        return {
            "question": question,
            "answer": "Ye topic in lectures me cover nahi hua.",
            "grounded": False,
            "citations": [],
            "retrieved_count": len(raw_results),
        }

    # 3. Context Construction
    context_str = build_context_block(filtered_results)
    user_prompt = (
        f"Retrieved Lecture Excerpts:\n"
        f"---------------------------\n"
        f"{context_str}\n"
        f"---------------------------\n\n"
        f"User Question: {question}\n\n"
        f"Grounded Answer (remember to cite excerpts like [1], [2]):"
    )

    # 4. LLM Generation via Groq
    generated_text = generate_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    # 5. Citation Validation
    # Check if the LLM answered with refusal
    refusal_markers = [
        "cover nahi hua",
        "nahi hua",
        "not covered",
        "does not mention",
        "no information",
    ]
    is_refusal = any(marker in generated_text.lower() for marker in refusal_markers)

    cited_indices = extract_citation_indices(generated_text)
    validated_citations: list[dict[str, Any]] = []

    for idx in cited_indices:
        if 1 <= idx <= len(filtered_results):
            source_chunk = filtered_results[idx - 1]
            vid_id = source_chunk["video_id"]
            start_s = source_chunk["start_sec"]
            end_s = source_chunk["end_sec"]
            # Apply rewind offset for smooth playback navigation
            rewind_time = max(0, start_s - rewind_sec)

            lines = source_chunk["text"].split("\n\n", 1)
            excerpt_body = lines[1] if len(lines) > 1 else lines[0]

            citation_data = {
                "citation_id": f"[{idx}]",
                "video_id": vid_id,
                "title": source_chunk["video_title"],
                "start_sec": start_s,
                "end_sec": end_s,
                "timestamp": format_timestamp(start_s),
                "url": f"https://www.youtube.com/watch?v={vid_id}&t={rewind_time}s",
                "text": excerpt_body.strip(),
            }
            validated_citations.append(citation_data)

    # Grounding status is true only if NOT refusal and at least one valid citation exists
    grounded = (not is_refusal) and len(validated_citations) > 0

    return {
        "question": question,
        "answer": generated_text,
        "grounded": grounded,
        "citations": validated_citations,
        "retrieved_count": len(filtered_results),
    }
