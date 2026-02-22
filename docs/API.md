# API 명세서

Base URL: `https://your-server.com`

> Swagger UI: `{Base URL}/docs`

## 관리 API

### 리뷰 목록 조회
```
GET /api/reviews?page=1&per_page=20&product_no=&search=
```
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| product_no | string | N | 상품번호 필터 |
| search | string | N | 작성자/제목/내용 검색 |
| page | int | N | 페이지 (기본: 1) |
| per_page | int | N | 페이지당 개수 (기본: 20, 최대: 100) |

**응답 200:**
```json
{
  "items": [
    {
      "id": 1,
      "product_no": "27",
      "product_name": "프리미엄 티셔츠",
      "author": "스타일리스트 김",
      "rating": 5,
      "title": "올 시즌 베스트",
      "content": "핏감이 정말 좋아요...",
      "is_visible": true,
      "display_order": 0,
      "created_at": "2026-02-22 10:30:00",
      "updated_at": "2026-02-22 10:30:00",
      "images": [
        {
          "id": 1,
          "review_id": 1,
          "file_path": "review_1/abc123.jpg",
          "original_name": "photo.jpg",
          "file_size": 102400,
          "created_at": "2026-02-22 10:30:00"
        }
      ]
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20
}
```

### 리뷰 생성
```
POST /api/reviews
Content-Type: application/json
```
```json
{
  "product_no": "27",
  "product_name": "프리미엄 티셔츠",
  "author": "스타일리스트 김",
  "rating": 5,
  "title": "올 시즌 베스트",
  "content": "핏감이 정말 좋아요..."
}
```
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| product_no | string | Y | 카페24 상품번호 |
| product_name | string | N | 상품명 (관리용) |
| author | string | Y | 작성자명 |
| rating | int | Y | 별점 (1~5) |
| title | string | N | 리뷰 제목 |
| content | string | Y | 리뷰 내용 |

**응답 201:** ReviewResponse 객체

### 리뷰 상세 조회
```
GET /api/reviews/{review_id}
```
**응답 200:** ReviewResponse 객체 (이미지 포함)

### 리뷰 수정
```
PUT /api/reviews/{review_id}
Content-Type: application/json
```
전달된 필드만 업데이트됩니다.
```json
{
  "rating": 4,
  "content": "수정된 내용"
}
```
**응답 200:** ReviewResponse 객체

### 리뷰 삭제
```
DELETE /api/reviews/{review_id}
```
연관된 이미지도 함께 삭제됩니다.

**응답 200:** `{"detail": "삭제되었습니다"}`

### 노출 상태 변경
```
PATCH /api/reviews/{review_id}/visibility
Content-Type: application/json
```
```json
{"is_visible": false}
```
**응답 200:** ReviewResponse 객체

### 엑셀 일괄 업로드
```
POST /api/reviews/excel-upload
Content-Type: multipart/form-data
```
| 필드 | 타입 | 설명 |
|------|------|------|
| file | File | .xlsx 파일 |

엑셀 컬럼 순서: 상품번호, 상품명, 작성자명, 별점(1~5), 리뷰제목, 리뷰내용

**응답 200:**
```json
{
  "success_count": 10,
  "fail_count": 2,
  "errors": [
    {"row": 5, "message": "상품번호는 필수입니다; 별점은 1~5 사이 정수여야 합니다"}
  ]
}
```

### 엑셀 템플릿 다운로드
```
GET /api/reviews/excel-template
```
헤더가 포함된 빈 .xlsx 파일을 다운로드합니다.

## 이미지 API

### 이미지 업로드
```
POST /api/reviews/{review_id}/images
Content-Type: multipart/form-data
```
| 필드 | 타입 | 설명 |
|------|------|------|
| files | File[] | 이미지 파일 (JPG/PNG/WEBP/GIF, 10MB 이하, 리뷰당 최대 5개) |

**응답 201:** ImageResponse 배열

### 이미지 삭제
```
DELETE /api/images/{image_id}
```
**응답 200:** `{"detail": "삭제되었습니다"}`

## 위젯 API (공개, 인증 불필요)

### 상품별 리뷰 조회
```
GET /api/widget/reviews/{product_no}?page=1&per_page=5
```
`is_visible=1`인 리뷰만 반환합니다. `display_order ASC, created_at DESC` 순 정렬.

**응답 200:**
```json
{
  "items": [...],
  "total": 12,
  "page": 1,
  "per_page": 5,
  "average_rating": 4.8,
  "total_reviews": 12
}
```

## 통계 API

### 대시보드 통계
```
GET /api/stats
```
**응답 200:**
```json
{
  "total_reviews": 42,
  "visible_reviews": 38,
  "average_rating": 4.6,
  "total_products": 12
}
```

## 에러 응답

모든 에러는 다음 형식:
```json
{"detail": "에러 메시지"}
```

| 상태 코드 | 설명 |
|-----------|------|
| 400 | 잘못된 요청 (파일 형식, 크기, 엑셀 형식 오류) |
| 404 | 리소스 미발견 |
| 422 | 유효성 검사 실패 (필수 필드 누락, 별점 범위 초과) |
| 500 | 서버 내부 오류 |
