import os

# Railway Volume 경로 (/data 마운트 시 자동 사용)
DATA_DIR: str = os.getenv("DATA_DIR", "")

if DATA_DIR:
    _default_db = f"sqlite:///{DATA_DIR}/reviews.db"
    _default_upload = f"{DATA_DIR}/uploads"
else:
    _default_db = "sqlite:///./reviews.db"
    _default_upload = "./uploads"

DATABASE_URL: str = os.getenv("DATABASE_URL", _default_db)
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", _default_upload)
MAX_IMAGE_SIZE: int = int(os.getenv("MAX_IMAGE_SIZE", "10485760"))  # 10MB
MAX_IMAGES_PER_REVIEW: int = 5
