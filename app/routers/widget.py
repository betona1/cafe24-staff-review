"""위젯용 공개 API -- 카페24 상품 상세 페이지에서 호출."""

import sqlite3
from typing import List, Literal

from fastapi import APIRouter, Depends, Query

from app.database import get_db_dependency
from app.models import (
    ImageResponse,
    RatingDistribution,
    ReviewResponse,
    WidgetReviewResponse,
)

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


def _get_rating_distribution(
    db: sqlite3.Connection, product_no: str
) -> RatingDistribution:
    """별점 분포를 계산한다."""
    rows = db.execute(
        "SELECT rating, COUNT(*) AS cnt "
        "FROM reviews WHERE product_no = ? AND is_visible = 1 "
        "GROUP BY rating",
        (product_no,),
    ).fetchall()

    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for row in rows:
        rating = row["rating"]
        if rating in dist:
            dist[rating] = row["cnt"]

    return RatingDistribution(
        star_5=dist[5],
        star_4=dist[4],
        star_3=dist[3],
        star_2=dist[2],
        star_1=dist[1],
    )


def _get_photo_review_count(
    db: sqlite3.Connection, product_no: str
) -> int:
    """포토리뷰 수를 계산한다."""
    row = db.execute(
        "SELECT COUNT(DISTINCT r.id) AS cnt "
        "FROM reviews r "
        "INNER JOIN review_images ri ON ri.review_id = r.id "
        "WHERE r.product_no = ? AND r.is_visible = 1",
        (product_no,),
    ).fetchone()
    return row["cnt"] if row else 0


def _get_all_photo_urls(
    db: sqlite3.Connection, product_no: str, limit: int = 20
) -> list[str]:
    """갤러리 스트립용 포토 URL (리뷰당 첫 이미지, 최신순)."""
    rows = db.execute(
        "SELECT ri.file_path "
        "FROM review_images ri "
        "INNER JOIN reviews r ON r.id = ri.review_id "
        "WHERE r.product_no = ? AND r.is_visible = 1 "
        "AND ri.id = ("
        "  SELECT MIN(ri2.id) FROM review_images ri2 WHERE ri2.review_id = r.id"
        ") "
        "ORDER BY r.created_at DESC "
        "LIMIT ?",
        (product_no, limit),
    ).fetchall()
    return [row["file_path"] for row in rows]


_SORT_MAP = {
    "latest": "display_order ASC, created_at DESC",
    "rating_high": "rating DESC, created_at DESC",
    "rating_low": "rating ASC, created_at DESC",
}

# photo_only 쿼리에서는 JOIN 때문에 테이블 접두사가 필요
_SORT_MAP_PREFIXED = {
    "latest": "r.display_order ASC, r.created_at DESC",
    "rating_high": "r.rating DESC, r.created_at DESC",
    "rating_low": "r.rating ASC, r.created_at DESC",
}


@router.get("/reviews/{product_no}", response_model=WidgetReviewResponse)
async def get_widget_reviews(
    product_no: str,
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(5, ge=1, le=50, description="페이지당 리뷰 수"),
    sort: Literal["latest", "rating_high", "rating_low"] = Query(
        "latest", description="정렬 기준"
    ),
    photo_only: bool = Query(False, description="포토 리뷰만 보기"),
    db: sqlite3.Connection = Depends(get_db_dependency),
) -> WidgetReviewResponse:
    """상품별 공개 리뷰 목록 (위젯용, 인증 불필요)."""

    # 1) 전체 통계 (항상 전체 기준)
    stats_row = db.execute(
        "SELECT COUNT(*) AS cnt, COALESCE(AVG(rating), 0) AS avg_rating "
        "FROM reviews WHERE product_no = ? AND is_visible = 1",
        (product_no,),
    ).fetchone()

    total_reviews: int = stats_row["cnt"]
    average_rating: float = round(float(stats_row["avg_rating"]), 1)

    # 2) 별점 분포
    rating_distribution = _get_rating_distribution(db, product_no)

    # 3) 포토리뷰 수
    photo_review_count = _get_photo_review_count(db, product_no)

    # 4) 갤러리 URL
    all_photo_urls = _get_all_photo_urls(db, product_no)

    # 5) 필터링된 리뷰 수 (페이지네이션용)
    if photo_only:
        count_row = db.execute(
            "SELECT COUNT(DISTINCT r.id) AS cnt "
            "FROM reviews r "
            "INNER JOIN review_images ri ON ri.review_id = r.id "
            "WHERE r.product_no = ? AND r.is_visible = 1",
            (product_no,),
        ).fetchone()
        filtered_total = count_row["cnt"]
    else:
        filtered_total = total_reviews

    # 6) 페이징된 리뷰 목록 (필터 + 정렬 적용)
    offset = (page - 1) * per_page
    order_clause = _SORT_MAP.get(sort, _SORT_MAP["latest"])

    if photo_only:
        prefixed_order = _SORT_MAP_PREFIXED.get(sort, _SORT_MAP_PREFIXED["latest"])
        review_rows = db.execute(
            "SELECT DISTINCT r.id, r.product_no, r.product_name, r.author, "
            "       r.rating, r.title, r.content, r.is_visible, "
            "       r.display_order, r.created_at, r.updated_at "
            "FROM reviews r "
            "INNER JOIN review_images ri ON ri.review_id = r.id "
            "WHERE r.product_no = ? AND r.is_visible = 1 "
            f"ORDER BY {prefixed_order} "
            "LIMIT ? OFFSET ?",
            (product_no, per_page, offset),
        ).fetchall()
    else:
        review_rows = db.execute(
            "SELECT id, product_no, product_name, author, rating, title, content, "
            "       is_visible, display_order, created_at, updated_at "
            "FROM reviews "
            "WHERE product_no = ? AND is_visible = 1 "
            f"ORDER BY {order_clause} "
            "LIMIT ? OFFSET ?",
            (product_no, per_page, offset),
        ).fetchall()

    items = [_build_review_with_images(row, db) for row in review_rows]

    return WidgetReviewResponse(
        items=items,
        total=filtered_total,
        page=page,
        per_page=per_page,
        average_rating=average_rating,
        total_reviews=total_reviews,
        rating_distribution=rating_distribution,
        photo_review_count=photo_review_count,
        all_photo_urls=all_photo_urls,
    )
