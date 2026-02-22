# 로컬 개발 환경 설정

## 사전 요구사항

- Python 3.11 이상
- Git
- Node.js 18+ (Railway CLI 설치용, 선택)

## 1단계: 프로젝트 클론

```bash
git clone https://github.com/your-repo/cafe24-staff-review.git
cd cafe24-staff-review
```

## 2단계: 가상환경 설정

```bash
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

## 3단계: 의존성 설치

```bash
pip install -r requirements.txt
```

## 4단계: 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일 내용:
```
DATABASE_URL=sqlite:///./reviews.db
SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_ORIGINS=*
UPLOAD_DIR=./uploads
MAX_IMAGE_SIZE=10485760
```

## 5단계: 개발 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

접속:
- 관리자 페이지: http://localhost:8000/admin
- API 문서 (Swagger): http://localhost:8000/docs
- API 문서 (ReDoc): http://localhost:8000/redoc

## 6단계: 테스트 실행

```bash
pytest tests/ -v
```

## 디렉토리 설명

| 경로 | 설명 |
|------|------|
| `app/` | FastAPI 백엔드 코드 |
| `templates/` | 관리자 HTML 템플릿 |
| `static/` | 카페24 위젯 파일 (JS, CSS) |
| `uploads/` | 리뷰 이미지 저장 (Git 미추적) |
| `tests/` | pytest 테스트 |
| `docs/` | 프로젝트 문서 |

## Claude Code 사용법

이 프로젝트는 Claude Code로 개발할 수 있도록 설정되어 있습니다.

```bash
# 프로젝트 디렉토리에서 Claude Code 시작
cd cafe24-staff-review
claude

# 유용한 명령
/project:dev-server     # 개발 서버 시작
/project:run-tests      # 테스트 실행
/project:deploy         # Railway 배포

# 서브에이전트 호출
@backend-dev   # 백엔드 작업
@frontend-dev  # 프론트엔드 작업
@deployer      # 배포 작업
```
