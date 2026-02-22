import sqlite3

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app import config
from app.database import get_db_dependency
from app.models import ImageResponse
from app.utils.storage import delete_image, save_image

router = APIRouter(prefix="/api", tags=["images"])


@router.post(
    "/reviews/{review_id}/images",
    response_model=list[ImageResponse],
    status_code=201,
)
async def upload_images(
    review_id: int,
    files: list[UploadFile],
    db: sqlite3.Connection = Depends(get_db_dependency),
) -> list[ImageResponse]:
    """리뷰에 이미지를 업로드한다."""
    # 리뷰 존재 여부 확인
    row = db.execute(
        "SELECT id FROM reviews WHERE id = ?", (review_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")

    # 현재 이미지 수 확인
    count_row = db.execute(
        "SELECT COUNT(*) as cnt FROM review_images WHERE review_id = ?",
        (review_id,),
    ).fetchone()
    current_count: int = count_row["cnt"] if count_row else 0

    if current_count + len(files) > config.MAX_IMAGES_PER_REVIEW:
        raise HTTPException(
            status_code=400,
            detail=(
                f"이미지는 리뷰당 최대 {config.MAX_IMAGES_PER_REVIEW}개까지 "
                f"업로드할 수 있습니다. (현재 {current_count}개)"
            ),
        )

    # 파일 업로드가 없는 경우
    if not files:
        raise HTTPException(
            status_code=400,
            detail="업로드할 파일이 없습니다.",
        )

    saved_images: list[ImageResponse] = []

    for file in files:
        # 파일 저장
        result: dict = await save_image(file, review_id)

        # DB에 레코드 삽입
        cursor = db.execute(
            """
            INSERT INTO review_images (review_id, file_path, original_name, file_size)
            VALUES (?, ?, ?, ?)
            """,
            (
                review_id,
                result["file_path"],
                result["original_name"],
                result["file_size"],
            ),
        )
        image_id: int = cursor.lastrowid  # type: ignore[assignment]

        # 삽입된 레코드 조회
        image_row = db.execute(
            "SELECT * FROM review_images WHERE id = ?", (image_id,)
        ).fetchone()

        saved_images.append(
            ImageResponse(
                id=image_row["id"],
                review_id=image_row["review_id"],
                file_path=image_row["file_path"],
                original_name=image_row["original_name"],
                file_size=image_row["file_size"],
                created_at=image_row["created_at"],
            )
        )

    return saved_images


@router.delete("/images/{image_id}")
async def delete_single_image(
    image_id: int,
    db: sqlite3.Connection = Depends(get_db_dependency),
) -> dict:
    """이미지를 삭제한다."""
    # 이미지 레코드 조회
    row = db.execute(
        "SELECT * FROM review_images WHERE id = ?", (image_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")

    # 파일시스템에서 삭제
    delete_image(row["file_path"])

    # DB 레코드 삭제
    db.execute("DELETE FROM review_images WHERE id = ?", (image_id,))

    return {"detail": "삭제되었습니다"}
