from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Review ---

class ReviewCreate(BaseModel):
    product_no: str = Field(..., min_length=1)
    product_name: str = ""
    author: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    title: str = ""
    content: str = Field(..., min_length=1)
    is_visible: bool = True
    display_order: int = 0


class ReviewUpdate(BaseModel):
    product_no: Optional[str] = None
    product_name: Optional[str] = None
    author: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = None
    content: Optional[str] = None
    is_visible: Optional[bool] = None
    display_order: Optional[int] = None


class ImageResponse(BaseModel):
    id: int
    review_id: int
    file_path: str
    original_name: str
    file_size: int
    created_at: str


class ReviewResponse(BaseModel):
    id: int
    product_no: str
    product_name: str
    author: str
    rating: int
    title: str
    content: str
    is_visible: bool
    display_order: int
    created_at: str
    updated_at: str
    images: list[ImageResponse] = []


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    page: int
    per_page: int


# --- Excel ---

class ExcelError(BaseModel):
    row: int
    message: str


class ExcelUploadResult(BaseModel):
    success_count: int
    fail_count: int
    errors: list[ExcelError]


# --- Stats ---

class StatsResponse(BaseModel):
    total_reviews: int
    visible_reviews: int
    average_rating: float
    total_products: int


# --- Widget ---

class WidgetReviewResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    page: int
    per_page: int
    average_rating: float
    total_reviews: int
