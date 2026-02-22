"""리뷰 CRUD API 테스트."""

from io import BytesIO

from openpyxl import Workbook


class TestCreateReview:
    def test_create_review(self, client, sample_review):
        resp = client.post("/api/reviews", json=sample_review)
        assert resp.status_code == 201
        data = resp.json()
        assert data["product_no"] == sample_review["product_no"]
        assert data["author"] == sample_review["author"]
        assert data["rating"] == sample_review["rating"]
        assert data["content"] == sample_review["content"]
        assert data["is_visible"] is True
        assert "id" in data

    def test_create_review_missing_fields(self, client):
        resp = client.post("/api/reviews", json={"product_no": "123"})
        assert resp.status_code == 422

    def test_create_review_invalid_rating(self, client):
        resp = client.post(
            "/api/reviews",
            json={
                "product_no": "123",
                "author": "작성자",
                "rating": 6,
                "content": "내용",
            },
        )
        assert resp.status_code == 422


class TestListReviews:
    def test_list_reviews(self, client, sample_review):
        # 리뷰 생성
        client.post("/api/reviews", json=sample_review)
        resp = client.get("/api/reviews")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_reviews_pagination(self, client, sample_review):
        # 여러 리뷰 생성
        for _ in range(3):
            client.post("/api/reviews", json=sample_review)
        resp = client.get("/api/reviews?page=1&per_page=2")
        data = resp.json()
        assert len(data["items"]) <= 2
        assert data["per_page"] == 2

    def test_list_reviews_filter_product(self, client):
        client.post(
            "/api/reviews",
            json={
                "product_no": "FILTER_TEST",
                "author": "필터",
                "rating": 3,
                "content": "필터 테스트",
            },
        )
        resp = client.get("/api/reviews?product_no=FILTER_TEST")
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["product_no"] == "FILTER_TEST"

    def test_list_reviews_search(self, client):
        client.post(
            "/api/reviews",
            json={
                "product_no": "999",
                "author": "검색테스트작성자",
                "rating": 4,
                "content": "검색 대상 리뷰",
            },
        )
        resp = client.get("/api/reviews?search=검색테스트작성자")
        data = resp.json()
        assert data["total"] >= 1


class TestGetReview:
    def test_get_review(self, client, sample_review):
        create_resp = client.post("/api/reviews", json=sample_review)
        review_id = create_resp.json()["id"]
        resp = client.get(f"/api/reviews/{review_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == review_id

    def test_get_review_not_found(self, client):
        resp = client.get("/api/reviews/99999")
        assert resp.status_code == 404


class TestUpdateReview:
    def test_update_review(self, client, sample_review):
        create_resp = client.post("/api/reviews", json=sample_review)
        review_id = create_resp.json()["id"]
        resp = client.put(
            f"/api/reviews/{review_id}",
            json={"title": "수정된 제목", "rating": 3},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "수정된 제목"
        assert data["rating"] == 3

    def test_update_review_not_found(self, client):
        resp = client.put("/api/reviews/99999", json={"title": "수정"})
        assert resp.status_code == 404


class TestDeleteReview:
    def test_delete_review(self, client, sample_review):
        create_resp = client.post("/api/reviews", json=sample_review)
        review_id = create_resp.json()["id"]
        resp = client.delete(f"/api/reviews/{review_id}")
        assert resp.status_code == 200
        assert resp.json()["detail"] == "삭제되었습니다"
        # 삭제 확인
        get_resp = client.get(f"/api/reviews/{review_id}")
        assert get_resp.status_code == 404

    def test_delete_review_not_found(self, client):
        resp = client.delete("/api/reviews/99999")
        assert resp.status_code == 404


class TestVisibility:
    def test_toggle_visibility(self, client, sample_review):
        create_resp = client.post("/api/reviews", json=sample_review)
        review_id = create_resp.json()["id"]
        # 숨김 처리
        resp = client.patch(
            f"/api/reviews/{review_id}/visibility",
            json={"is_visible": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_visible"] is False
        # 다시 노출
        resp = client.patch(
            f"/api/reviews/{review_id}/visibility",
            json={"is_visible": True},
        )
        assert resp.json()["is_visible"] is True


class TestExcelUpload:
    def _make_xlsx(self, rows: list[list]) -> BytesIO:
        """테스트용 엑셀 파일을 생성한다."""
        wb = Workbook()
        ws = wb.active
        ws.append(["상품번호", "상품명", "작성자명", "별점(1~5)", "리뷰제목", "리뷰내용"])
        for row in rows:
            ws.append(row)
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    def test_excel_upload_success(self, client):
        xlsx = self._make_xlsx([
            ["P001", "상품A", "작성자1", 5, "좋아요", "정말 좋습니다"],
            ["P002", "상품B", "작성자2", 4, "괜찮아요", "무난합니다"],
        ])
        resp = client.post(
            "/api/reviews/excel-upload",
            files={"file": ("reviews.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success_count"] == 2
        assert data["fail_count"] == 0

    def test_excel_upload_with_errors(self, client):
        xlsx = self._make_xlsx([
            ["P001", "상품A", "작성자1", 5, "좋아요", "정말 좋습니다"],
            ["", "", "", "abc", "", ""],  # 모든 필드 오류
        ])
        resp = client.post(
            "/api/reviews/excel-upload",
            files={"file": ("reviews.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        data = resp.json()
        assert data["success_count"] == 1
        assert data["fail_count"] == 1
        assert len(data["errors"]) == 1

    def test_excel_upload_invalid_file(self, client):
        resp = client.post(
            "/api/reviews/excel-upload",
            files={"file": ("reviews.txt", BytesIO(b"not excel"), "text/plain")},
        )
        assert resp.status_code == 400

    def test_excel_template_download(self, client):
        resp = client.get("/api/reviews/excel-template")
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]


class TestStats:
    def test_get_stats(self, client, sample_review):
        client.post("/api/reviews", json=sample_review)
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_reviews" in data
        assert "visible_reviews" in data
        assert "average_rating" in data
        assert "total_products" in data
        assert data["total_reviews"] >= 1
