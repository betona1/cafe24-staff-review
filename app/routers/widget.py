"""위젯용 공개 API -- 카페24 상품 상세 페이지에서 호출."""

import sqlite3
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db_dependency
from app.models import ImageResponse, ReviewResponse, WidgetReviewResponse

router = APIRouter(prefix="/api/widget", tags=["widget"])


def _build_review_with_images(
    review_row: sqlite3.Row,
    db: sqlite3.Connection,
) -> ReviewResponse:
    """리뷰 Row를 ReviewResponse로 변환하고, 해당 이미지 목록을 첨부한다."""
    images_rows = db.execute(
        "SELECT id, review_id, file_path, original_name, file_size, created_at "
        "FROM review_images WHERE review_id = ? ORDER BY id ASC",
        (review_row["id"],),
    ).fetchall()

    images: List[ImageResponse] = [
        ImageResponse(
            id=img["id"],
            review_id=img["review_id"],
            file_path=img["file_path"],
            original_name=img["original_name"],
            file_size=img["file_size"],
            created_at=str(img["created_at"]),
        )
        for img in images_rows
    ]

    return ReviewResponse(
        id=review_row["id"],
        product_no=review_row["product_no"],
        product_name=review_row["product_name"],
        author=review_row["author"],
        rating=review_row["rating"],
        title=review_row["title"],
        content=review_row["content"],
        is_visible=bool(review_row["is_visible"]),
        display_order=review_row["display_order"],
        created_at=str(review_row["created_at"]),
        updated_at=str(review_row["updated_at"]),
        images=images,
    )


@router.get("/reviews/{product_no}", response_model=WidgetReviewResponse)
async def get_widget_reviews(
    product_no: str,
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(5, ge=1, le=50, description="페이지당 리뷰 수"),
    db: sqlite3.Connection = Depends(get_db_dependency),
) -> WidgetReviewResponse:
    """상품별 공개 리뷰 목록 (위젯용, 인증 불필요)."""

    # 1) 해당 상품의 공개 리뷰 전체 통계 (평균 별점, 총 개수)
    stats_row = db.execute(
        "SELECT COUNT(*) AS cnt, COALESCE(AVG(rating), 0) AS avg_rating "
        "FROM reviews WHERE product_no = ? AND is_visible = 1",
        (product_no,),
    ).fetchone()

    total_reviews: int = stats_row["cnt"]
    average_rating: float = round(float(stats_row["avg_rating"]), 1)

    # 2) 페이징된 리뷰 목록
    offset = (page - 1) * per_page
    review_rows = db.execute(
        "SELECT id, product_no, product_name, author, rating, title, content, "
        "       is_visible, display_order, created_at, updated_at "
        "FROM reviews "
        "WHERE product_no = ? AND is_visible = 1 "
        "ORDER BY display_order ASC, created_at DESC "
        "LIMIT ? OFFSET ?",
        (product_no, per_page, offset),
    ).fetchall()

    items = [_build_review_with_images(row, db) for row in review_rows]

    return WidgetReviewResponse(
        items=items,
        total=total_reviews,
        page=page,
        per_page=per_page,
        average_rating=average_rating,
        total_reviews=total_reviews,
    )
