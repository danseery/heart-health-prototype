from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ContentItem, ContentSummary, new_id
from app.schemas import ContentSummaryResponse
from app.services.ai import generate_content_summary

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/{content_id}/summary", response_model=ContentSummaryResponse)
def get_content_summary(
    content_id: str,
    db: Session = Depends(get_db),
) -> ContentSummaryResponse:
    item = db.get(ContentItem, content_id)
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found.")

    summary = db.scalar(
        select(ContentSummary).where(ContentSummary.content_item_id == content_id)
    )
    cached = True
    if not summary:
        summary = ContentSummary(
            id=new_id("summary"),
            content_item_id=content_id,
            summary=generate_content_summary(item.title, item.body),
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        cached = False

    return ContentSummaryResponse(
        content_id=item.id,
        title=item.title,
        topic=item.topic,
        author=item.author,
        summary=summary.summary,
        cached=cached,
    )
