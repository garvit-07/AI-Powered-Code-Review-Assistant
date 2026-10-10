from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewListItem, ReviewOut
from app.services.llm import ReviewError, Reviewer, get_reviewer

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


async def _get_own_review(review_id: int, user: User, db: AsyncSession) -> Review:
    review = await db.scalar(
        select(Review).where(Review.id == review_id, Review.user_id == user.id)
    )
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    return review


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    reviewer: Reviewer = Depends(get_reviewer),
):
    """Send code to the GenAI model and store the structured feedback."""
    try:
        feedback, model = await reviewer.review(payload.code, payload.language)
    except ReviewError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    review = Review(
        user_id=user.id,
        language=payload.language,
        code=payload.code,
        summary=feedback.summary,
        score=feedback.score,
        feedback=feedback.model_dump(mode="json"),
        model=model,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@router.get("", response_model=list[ReviewListItem])
async def list_reviews(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The current user's review history, newest first."""
    rows = await db.scalars(
        select(Review)
        .where(Review.user_id == user.id)
        .order_by(Review.created_at.desc(), Review.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        ReviewListItem(
            id=r.id,
            language=r.language,
            summary=r.summary,
            score=r.score,
            findings_count=len(r.feedback.get("findings", [])),
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/{review_id}", response_model=ReviewOut)
async def get_review(
    review_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await _get_own_review(review_id, user, db)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await db.delete(await _get_own_review(review_id, user, db))
    await db.commit()
