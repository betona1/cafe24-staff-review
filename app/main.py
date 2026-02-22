import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import config
from app.database import init_db
from app.routers import admin, images, reviews, widget


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
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
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")


@app.get("/")
async def root():
    return {"message": "카페24 스태프 리뷰 API", "docs": "/docs"}
