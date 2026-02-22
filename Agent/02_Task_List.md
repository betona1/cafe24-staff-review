# 작업 목록

## Phase 1: 프로젝트 초기화
- [ ] 프로젝트 디렉토리 구조 생성
- [ ] `requirements.txt` 작성
- [ ] `.gitignore` 작성
- [ ] Git 초기화 및 초기 커밋
- [ ] `app/config.py` 환경변수 설정 모듈 작성

## Phase 2: 백엔드 — 데이터베이스 & 모델
- [ ] `app/database.py` DB 연결 및 테이블 생성
- [ ] `app/models.py` Pydantic 모델 정의 (ReviewCreate, ReviewUpdate, ReviewResponse)
- [ ] 테스트용 시드 데이터 함수 작성

## Phase 3: 백엔드 — 리뷰 CRUD API
- [ ] `app/routers/reviews.py` 리뷰 CRUD 엔드포인트
  - [ ] GET /api/reviews (목록, 페이징, 필터)
  - [ ] POST /api/reviews (생성)
  - [ ] GET /api/reviews/{id} (상세)
  - [ ] PUT /api/reviews/{id} (수정)
  - [ ] DELETE /api/reviews/{id} (삭제)
- [ ] `tests/test_reviews.py` 리뷰 API 테스트

## Phase 4: 백엔드 — 이미지 업로드
- [ ] `app/utils/storage.py` 파일 스토리지 추상화
- [ ] `app/routers/images.py` 이미지 업로드/삭제 엔드포인트
  - [ ] POST /api/reviews/{id}/images (업로드)
  - [ ] DELETE /api/reviews/{id}/images (삭제)
- [ ] 파일 타입 및 크기 검증
- [ ] `tests/test_images.py` 이미지 API 테스트

## Phase 5: 백엔드 — 위젯 API & 통계
- [ ] `app/routers/widget.py` 위젯용 공개 API
  - [ ] GET /api/widget/reviews/{product_id} (노출 리뷰만)
- [ ] GET /api/stats 통계 API
- [ ] `tests/test_widget.py` 위젯 API 테스트

## Phase 6: 백엔드 — 앱 조립
- [ ] `app/main.py` FastAPI 앱 생성, 라우터 등록, CORS, 정적 파일 마운트
- [ ] `app/routers/admin.py` 관리자 페이지 서빙
- [ ] 전체 테스트 통과 확인

## Phase 7: 프론트엔드 — 관리자 대시보드
- [x] `templates/admin.html` 기본 레이아웃 (헤더, 통계바, 테이블)
- [x] 리뷰 목록 렌더링 (테이블, 페이지네이션)
- [x] 리뷰 작성 모달 (별점 입력, 폼)
- [x] 리뷰 수정 모달
- [x] 이미지 업로드 UI (드래그앤드롭/클릭)
- [x] 노출/숨김 토글
- [x] 삭제 확인 다이얼로그
- [x] 검색 기능
- [x] 위젯 임베드 코드 모달
- [x] 토스트 알림
- [x] 엑셀 업로드 모달

## Phase 8: 프론트엔드 — 카페24 위젯
- [x] `static/widget.js` IIFE 위젯 스크립트
  - [x] API 호출 및 렌더링
  - [x] 별점 표시
  - [x] 이미지 라이트박스
  - [x] 페이지네이션
  - [x] 에러 시 graceful 처리
- [x] `static/widget.css` 위젯 스타일 (srw- 접두사)

## Phase 9: 배포 준비
- [ ] `railway.json` 배포 설정
- [ ] `Procfile` 작성
- [ ] `runtime.txt` Python 버전 명시
- [ ] 환경변수 목록 문서화
- [ ] CORS 운영 설정 가이드

## Phase 10: 배포 & 카페24 연동
- [ ] GitHub 저장소 push
- [ ] Railway 프로젝트 생성 및 배포
- [ ] HTTPS 도메인 확인
- [ ] 카페24 위젯 삽입 테스트
- [ ] 운영 환경 CORS 설정

## Phase 11: 문서화
- [ ] `README.md` 완성
- [ ] `docs/SETUP.md` 로컬 개발 가이드
- [ ] `docs/DEPLOY.md` 배포 가이드
- [ ] `docs/CAFE24_INTEGRATION.md` 카페24 연동 가이드
- [ ] `docs/API.md` API 명세서
