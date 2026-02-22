# 카페24 스태프 리뷰 앱

카페24 쇼핑몰용 스태프 리뷰 관리 시스템입니다.
알파리뷰 스타일의 스태프 리뷰를 작성하고, 상품 상세 페이지에 위젯으로 노출합니다.

## 주요 기능

- ⭐ 텍스트 리뷰 + 별점 (1~5점)
- 📷 이미지 첨부 (다중 업로드, 최대 5장)
- 📊 엑셀 일괄 업로드 (.xlsx 파일로 리뷰 대량 등록)
- 📦 상품별 리뷰 관리 (검색, 필터, 노출/숨김 토글)
- 🔗 카페24 프론트 위젯 (JS 임베드, IIFE 패턴)
- 📈 대시보드 통계 (전체/노출 리뷰 수, 평균 별점, 등록 상품 수)

## 빠른 시작

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env

# 3. 서버 실행
uvicorn app.main:app --reload --port 8000

# 4. 접속
# 관리자: http://localhost:8000/admin
# API 문서: http://localhost:8000/docs
```

## Claude Code로 개발하기

이 프로젝트는 Claude Code에 최적화되어 있습니다.

```bash
cd cafe24-staff-review
claude
```

사용 가능한 서브에이전트:
- `@backend-dev` — FastAPI 백엔드 개발
- `@frontend-dev` — 관리자 UI, 카페24 위젯
- `@deployer` — Railway 배포, 카페24 연동

사용 가능한 명령:
- `/project:dev-server` — 개발 서버 시작
- `/project:run-tests` — 테스트 실행
- `/project:deploy` — Railway 배포

## 문서

- [로컬 개발 환경 설정](docs/SETUP.md)
- [Railway 배포 가이드](docs/DEPLOY.md)
- [카페24 위젯 연동 가이드](docs/CAFE24_INTEGRATION.md)
- [API 명세서](docs/API.md)

## 기술 스택

Python 3.11 · FastAPI · SQLite · Vanilla JS · Railway
