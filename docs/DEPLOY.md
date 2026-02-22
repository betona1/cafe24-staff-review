# Railway 배포 가이드

## Railway란?

GitHub 연동으로 자동 배포되는 클라우드 플랫폼.
코드를 push하면 자동으로 빌드 & 배포됩니다.

**비용**: Trial 후 월 $5 Hobby Plan (소규모 앱에 충분)

## 배포 절차

### 1. 사전 준비

```bash
# GitHub 저장소 생성 & push
git init
git add .
git commit -m "feat: initial project setup"
git remote add origin https://github.com/your-name/cafe24-staff-review.git
git push -u origin main
```

### 2. Railway CLI 설치 (선택, 웹 UI로도 가능)

```bash
npm install -g @railway/cli
railway login
```

### 3-A. 웹 UI로 배포 (추천)

1. https://railway.app 접속 → GitHub 로그인
2. **New Project** → **Deploy from GitHub repo**
3. `cafe24-staff-review` 저장소 선택
4. 자동 감지 → Python 앱으로 인식
5. **Settings** → **Environment Variables** 설정:

| 변수명 | 값 | 설명 |
|--------|-----|------|
| `DATABASE_URL` | `sqlite:///./reviews.db` | DB 경로 |
| `SECRET_KEY` | `(랜덤 생성)` | 보안 키 |
| `ALLOWED_ORIGINS` | `https://your-shop.cafe24.com` | CORS |
| `UPLOAD_DIR` | `./uploads` | 이미지 경로 |

6. **Settings** → **Networking** → **Generate Domain** 클릭
7. `https://your-app.up.railway.app` 형태의 URL 생성됨

### 3-B. CLI로 배포

```bash
cd cafe24-staff-review
railway init
railway variables set DATABASE_URL="sqlite:///./reviews.db"
railway variables set SECRET_KEY="$(python -c 'import secrets;print(secrets.token_hex(32))')"
railway variables set ALLOWED_ORIGINS="https://your-shop.cafe24.com"
railway up
railway domain
```

### 4. 배포 확인

```bash
# 헬스체크
curl https://your-app.up.railway.app/api/stats

# 관리자 페이지
# 브라우저에서 https://your-app.up.railway.app/admin 접속
```

## 프로젝트 설정 파일

### railway.json (이미 포함됨)

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/stats",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### runtime.txt

```
python-3.11.x
```

## 이미지 스토리지 주의사항

Railway의 파일시스템은 **ephemeral** (배포 시 초기화됨).
업로드된 이미지가 유지되려면:

### 옵션 A: Railway Volume (간단)
Railway Settings → Volumes → Mount `/app/uploads`

### 옵션 B: S3 호환 스토리지 (확장성)
Cloudflare R2 또는 AWS S3 사용.
`app/utils/storage.py`를 S3 업로드로 교체.

## 자동 배포

GitHub에 push하면 Railway가 자동으로 재배포합니다.

```bash
git add .
git commit -m "feat: add new feature"
git push origin main
# → Railway 자동 빌드 & 배포
```

## 커스텀 도메인 (선택)

Railway Settings → Networking → Custom Domain에서
`review.your-shop.com` 같은 도메인을 연결할 수 있습니다.
DNS에 CNAME 레코드를 추가하면 됩니다.
