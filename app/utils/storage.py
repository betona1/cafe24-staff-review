import os
import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app import config

ALLOWED_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


async def save_image(file: UploadFile, review_id: int) -> dict:
    """
    업로드된 이미지 파일을 저장한다.

    - content_type과 확장자 검증
    - 파일 크기 <= MAX_IMAGE_SIZE 검증
    - UUID 기반 파일명으로 충돌 방지
    - UPLOAD_DIR/review_{review_id}/ 경로에 저장

    Returns:
        dict: file_path(상대경로), original_name, file_size
    """
    # 확장자 검증
    original_name: str = file.filename or "unknown"
    extension: str = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"허용되지 않는 파일 확장자입니다: {extension}",
        )

    # content_type 검증
    content_type: str = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"허용되지 않는 파일 형식입니다: {content_type}",
        )

    # 파일 내용을 메모리에 읽어 크기 확인
    content: bytes = await file.read()
    file_size: int = len(content)
    if file_size > config.MAX_IMAGE_SIZE:
        max_mb: float = config.MAX_IMAGE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"파일 크기가 {max_mb:.0f}MB를 초과합니다.",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="빈 파일은 업로드할 수 없습니다.",
        )

    # 저장 디렉토리 생성
    review_dir: str = os.path.join(config.UPLOAD_DIR, f"review_{review_id}")
    os.makedirs(review_dir, exist_ok=True)

    # UUID 기반 파일명 생성
    unique_name: str = f"{uuid.uuid4()}{extension}"
    full_path: str = os.path.join(review_dir, unique_name)

    # 파일 저장
    with open(full_path, "wb") as f:
        f.write(content)

    # 상대 경로 반환 (UPLOAD_DIR 기준)
    relative_path: str = f"review_{review_id}/{unique_name}"

    return {
        "file_path": relative_path,
        "original_name": original_name,
        "file_size": file_size,
    }


def delete_image(file_path: str) -> None:
    """
    파일시스템에서 이미지 파일을 삭제한다.
    파일이 존재하지 않으면 무시한다.
    """
    full_path: str = os.path.join(config.UPLOAD_DIR, file_path)
    if os.path.exists(full_path):
        os.remove(full_path)


def delete_review_images(review_id: int) -> None:
    """
    리뷰에 속한 모든 이미지 디렉토리를 삭제한다.
    디렉토리가 존재하지 않으면 무시한다.
    """
    review_dir: str = os.path.join(config.UPLOAD_DIR, f"review_{review_id}")
    if os.path.exists(review_dir):
        shutil.rmtree(review_dir)
