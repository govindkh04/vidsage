import logging
from fastapi import APIRouter, HTTPException, Request, status
from api.schemas.request import AskRequest
from api.schemas.response import AskResponse, CitationItem
from api.services.rate_limiter import ask_rate_limiter
from ytrag.answer import answer as generate_answer

logger = logging.getLogger("api.ask")
router = APIRouter(tags=["Question Answering"])


@router.post("/ask", response_model=AskResponse)
def ask_question(req: AskRequest, request: Request) -> AskResponse:
    """Submit a user question (in English or Hinglish) and receive a grounded answer with verified lecture citations."""
    # 1. Enforce rate limiting
    ask_rate_limiter.check(request)

    # 2. Run grounded RAG answering
    try:
        result = generate_answer(
            question=req.question,
            top_k=req.top_k,
            max_distance=req.threshold,
        )
    except Exception as e:
        logger.exception("Error executing question answering pipeline")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the answer: {str(e)}",
        )

    # 3. Format response
    citation_items = [
        CitationItem(
            citation_id=c["citation_id"],
            video_id=c["video_id"],
            title=c["title"],
            start_sec=c["start_sec"],
            end_sec=c["end_sec"],
            timestamp=c["timestamp"],
            url=c["url"],
            text=c["text"],
        )
        for c in result.get("citations", [])
    ]

    return AskResponse(
        question=result["question"],
        answer=result["answer"],
        grounded=result["grounded"],
        citations=citation_items,
        retrieved_count=result.get("retrieved_count", 0),
    )
