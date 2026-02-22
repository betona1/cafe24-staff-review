# 카페24 스태프 리뷰 앱

## 프로젝트 개요

카페24 쇼핑몰용 스태프 리뷰 관리 시스템. 알파리뷰 스타일의 스태프 리뷰를 관리하고 카페24 상품 상세 페이지에 위젯으로 노출한다.

### 핵심 아키텍처

```
[카페24 쇼핑몰] ←── JS 위젯(CORS) ──→ [FastAPI 서버 (Railway)]
 상품 상세 페이지                         리뷰 CRUD API + 관리자 UI
     ↓                                        ↓
 {$product_no} 치환코드              SQLite/PostgreSQL + 이미지 스토리지
```

### 기술 스택

- **Backend**: Python 3.11+, FastAPI, Uvicorn
- **Database**: SQLite (개발) → PostgreSQL (운영)
- **Frontend (관리자)**: Vanilla JS + HTML (SPA, 별도 프레임워크 없음)
- **Frontend (위젯)**: Vanilla JS + CSS (IIFE 패턴, 카페24 삽입용)
- **배포**: Railway (GitHub 연동 자동 배포)
- **이미지**: 로컬 uploads/ (개발) → S3 호환 스토리지 (운영)

## 프로젝트 구조

```
cafe24-staff-review/
├── CLAUDE.md                    # 이 파일
├── README.md                    # 사용자용 문서
├── .gitignore
├── requirements.txt
├── railway.json                 # Railway 배포 설정
├── Procfile                     # 대체 배포 설정
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 앱 엔트리포인트
│   ├── config.py                # 환경변수 & 설정
│   ├── database.py              # DB 연결 & 초기화
│   ├── models.py                # Pydantic 모델
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── reviews.py           # 리뷰 CRUD API
│   │   ├── images.py            # 이미지 업로드/삭제
│   │   ├── widget.py            # 위젯용 공개 API
│   │   └── admin.py             # 관리자 페이지 서빙
│   └── utils/
│       ├── __init__.py
│       └── storage.py           # 파일 스토리지 추상화
├── templates/
│   └── admin.html               # 관리자 대시보드 (SPA)
├── static/
│   ├── widget.js                # 카페24 임베드 위젯
│   └── widget.css               # 위젯 스타일
├── uploads/                     # 리뷰 이미지 (gitignore)
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_reviews.py
│   ├── test_images.py
│   └── test_widget.py
├── docs/
│   ├── SETUP.md                 # 로컬 개발 환경 설정
│   ├── DEPLOY.md                # Railway 배포 가이드
│   ├── CAFE24_INTEGRATION.md    # 카페24 위젯 연동 가이드
│   └── API.md                   # API 명세
├── Agent/
│   ├── 01_Requirements.md       # 요구사항 정의서
│   └── 02_Task_List.md          # 작업 목록
└── .claude/
    ├── settings.json            # Claude Code 권한 설정
    ├── agents/                  # 서브에이전트 정의
    │   ├── backend-dev.md
    │   ├── frontend-dev.md
    │   └── deployer.md
    └── commands/                # 커스텀 슬래시 명령
        ├── dev-server.md
        ├── run-tests.md
        └── deploy.md
```

## 개발 규칙

### 코드 스타일
- Python: Black 포매터, isort, 타입 힌트 필수
- JS: 세미콜론 사용, const 우선, 한국어 주석 허용
- HTML/CSS: 위젯 CSS는 `srw-` 접두사로 네임스페이스 충돌 방지

### 커밋 컨벤션
- `feat:` 새 기능
- `fix:` 버그 수정
- `docs:` 문서 변경
- `refactor:` 리팩토링
- `test:` 테스트 추가/수정
- `deploy:` 배포 관련

### 테스트
- `pytest` 사용
- 테스트 실행: `pytest tests/ -v`
- 새 API 엔드포인트 추가 시 반드시 테스트 작성

### API 설계 원칙
- RESTful 규칙 준수
- 모든 응답은 JSON
- 에러 응답: `{"detail": "에러 메시지"}`
- 위젯 API (`/api/widget/*`)는 인증 없이 공개
- 관리 API (`/api/reviews/*`)는 추후 인증 추가 예정

### 카페24 연동 핵심 사항
- 위젯 JS는 IIFE 패턴으로 전역 오염 방지
- `{$product_no}` 카페24 치환코드로 상품번호 자동 매핑
- CORS 설정 필수 (카페24 도메인 허용)
- 위젯 CSS는 쇼핑몰 기존 스타일과 충돌하지 않도록 `srw-` 접두사 사용

## 자주 사용하는 명령어

```bash
# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 테스트 실행
pytest tests/ -v

# 포맷팅
black app/ tests/
isort app/ tests/

# Railway 배포 (CLI)
railway up
```

## 환경변수

```
DATABASE_URL=sqlite:///./reviews.db    # 개발용
SECRET_KEY=your-secret-key             # 관리자 인증용
ALLOWED_ORIGINS=*                      # CORS (운영 시 카페24 도메인으로 제한)
UPLOAD_DIR=./uploads                   # 이미지 저장 경로
MAX_IMAGE_SIZE=10485760                # 10MB
```

## 작업 흐름

이 프로젝트에서 작업할 때는 다음 에이전트를 활용하세요:
1. `@backend-dev` — FastAPI 백엔드 개발 (API, DB, 인증)
2. `@frontend-dev` — 관리자 UI 및 카페24 위젯 개발
3. `@deployer` — Railway 배포 및 카페24 연동 설정

작업 진행 상황은 `Agent/02_Task_List.md`에서 관리합니다.
복잡한 사용법이나 에러 발생 시 `docs/` 디렉토리의 문서를 참조하세요.
