# Claude Code로 처음부터 만드는 방법

## 사전 준비

### 1. Claude Code 설치
```bash
npm install -g @anthropic-ai/claude-code
```

### 2. 프로젝트 폴더 생성 & 이동
```bash
mkdir cafe24-staff-review
cd cafe24-staff-review
```

### 3. 이 프로젝트 파일들을 폴더에 복사
다운로드한 프로젝트 파일 전체를 이 폴더에 넣으세요.

### 4. Git 초기화
```bash
git init
git add .
git commit -m "feat: initial project scaffold with Claude Code setup"
```

## Claude Code 실행 & 개발 시작

```bash
claude
```

Claude Code가 시작되면 `CLAUDE.md`를 자동으로 읽어 프로젝트 맥락을 이해합니다.

## 개발 순서 (프롬프트 예시)

### Phase 1: 백엔드 기반 구축

```
@backend-dev Agent/02_Task_List.md를 읽고 Phase 1~2의 태스크를 순서대로 완료해줘.
프로젝트 구조는 이미 만들어져 있으니 app/config.py, app/database.py, app/models.py를 작성해줘.
```

### Phase 2: 리뷰 CRUD API

```
@backend-dev Phase 3 태스크를 진행해줘.
app/routers/reviews.py에 리뷰 CRUD 엔드포인트를 작성하고,
tests/test_reviews.py에 테스트도 함께 만들어줘.
테스트가 통과하는지 확인까지 해줘.
```

### Phase 3: 이미지 업로드

```
@backend-dev Phase 4를 진행해줘.
이미지 업로드/삭제 API를 만들고 파일 타입과 크기 검증도 추가해줘.
```

### Phase 4: 위젯 API & 앱 조립

```
@backend-dev Phase 5~6을 진행해줘.
위젯용 공개 API, 통계 API를 만들고 app/main.py에서 모든 라우터를 조립해줘.
전체 테스트가 통과하는지 확인해줘.
```

### Phase 5: 관리자 대시보드

```
@frontend-dev Phase 7을 진행해줘.
templates/admin.html에 다크 테마의 관리자 대시보드를 만들어줘.
리뷰 목록, 작성 모달, 수정, 삭제, 이미지 업로드, 검색, 페이지네이션 모두 포함.
```

### Phase 6: 카페24 위젯

```
@frontend-dev Phase 8을 진행해줘.
static/widget.js는 반드시 IIFE 패턴으로, 
static/widget.css는 srw- 접두사를 사용해줘.
카페24 쇼핑몰에 삽입해도 기존 CSS와 충돌하지 않도록 작성해줘.
```

### Phase 7: 로컬 테스트

```
/project:dev-server
```

브라우저에서 http://localhost:8000/admin 접속하여 전체 기능 테스트

### Phase 8: 배포

```
@deployer Phase 9~10을 진행해줘.
배포 설정 파일을 확인하고 Railway에 배포해줘.
```

### Phase 9: 카페24 연동

배포 URL이 나오면 `docs/CAFE24_INTEGRATION.md`의 가이드를 따라
카페24 스마트디자인에서 위젯 코드를 삽입합니다.

## 유용한 팁

### 에러가 발생하면
```
이 에러를 분석하고 수정해줘: [에러 메시지 붙여넣기]
```

### 코드 품질 개선
```
app/ 디렉토리의 코드를 리뷰하고 개선할 점을 찾아서 수정해줘.
```

### 새 기능 추가
```
Agent/02_Task_List.md에 새 태스크를 추가하고 구현해줘:
- 리뷰 정렬 순서 드래그앤드롭 변경
```

### 컨텍스트가 부족할 때
```
CLAUDE.md와 Agent/01_Requirements.md를 다시 읽고 
현재 진행 상황을 Agent/02_Task_List.md에서 확인해줘.
```
