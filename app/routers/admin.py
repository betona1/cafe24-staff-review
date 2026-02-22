"""관리자 대시보드 페이지 서빙."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


@router.get("/admin", response_class=HTMLResponse)
async def admin_page() -> HTMLResponse:
    """관리자 대시보드 페이지 서빙."""
    html_path = TEMPLATES_DIR / "admin.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
