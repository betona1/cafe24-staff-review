import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import config
from app.database import get_db, init_db
from app.routers import admin, images, reviews, widget

logger = logging.getLogger(__name__)

# 프로젝트 루트 디렉토리 (app/ 상위)
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
SEED_BACKUP = BASE_DIR / "data" / "seed_backup.json"


def _restore_from_seed() -> None:
    """DB가 비어있을 때 seed 백업에서 리뷰 데이터를 복원한다."""
    if not SEED_BACKUP.exists():
        return

    with get_db() as db:
        count = db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        if count > 0:
            return  # 데이터가 이미 있으면 건너뜀

        logger.info("DB가 비어있습니다. seed backup에서 복원합니다...")

        with open(SEED_BACKUP, "r", encoding="utf-8") as f:
            backup = json.load(f)

        restored = 0
        for r in backup.get("reviews", []):
            db.execute(
                "INSERT INTO reviews "
                "(product_no, product_name, author, rating, title, content, "
                " is_visible, display_order, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    r["product_no"],
                    r.get("product_name", ""),
                    r["author"],
                    r["rating"],
                    r.get("title", ""),
                    r["content"],
                    1 if r.get("is_visible", True) else 0,
                    r.get("display_order", 0),
                    r.get("created_at"),
                    r.get("updated_at"),
                ),
            )
            restored += 1

        logger.info("seed 복원 완료: %d개 리뷰", restored)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)
    _restore_from_seed()
    yield


app = FastAPI(title="카페24 스태프 리뷰", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(reviews.router)
app.include_router(images.router)
app.include_router(widget.router)
app.include_router(admin.router)

# 정적 파일
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")


@app.get("/")
async def root():
    return {"message": "카페24 스태프 리뷰 API", "docs": "/docs"}
