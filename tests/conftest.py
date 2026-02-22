import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# 테스트용 환경변수 설정 (app 임포트 전에 설정)
_test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db.name}"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp()

from app.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """세션 시작 시 테스트 DB 초기화."""
    init_db()
    yield
    # 테스트 완료 후 정리
    if os.path.exists(_test_db.name):
        os.unlink(_test_db.name)


@pytest.fixture()
def client():
    """FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture()
def sample_review() -> dict:
    """샘플 리뷰 데이터."""
    return {
        "product_no": "12345",
        "product_name": "테스트 상품",
        "author": "테스트 작성자",
        "rating": 5,
        "title": "훌륭한 상품",
        "content": "정말 좋습니다. 강력 추천!",
    }
