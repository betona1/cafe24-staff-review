import os

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./reviews.db")
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
MAX_IMAGE_SIZE: int = int(os.getenv("MAX_IMAGE_SIZE", "10485760"))  # 10MB
MAX_IMAGES_PER_REVIEW: int = 5
