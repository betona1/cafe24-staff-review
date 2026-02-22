"""위젯 API 테스트."""


class TestWidgetReviews:
    def test_get_widget_reviews(self, client, sample_review):
        # 리뷰 생성
        client.post("/api/reviews", json=sample_review)
        resp = client.get(f"/api/widget/reviews/{sample_review['product_no']}")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "average_rating" in data
        assert "total_reviews" in data
        assert data["total_reviews"] >= 1

    def test_widget_only_visible_reviews(self, client):
        # 노출 리뷰 생성
        resp = client.post(
            "/api/reviews",
            json={
                "product_no": "WIDGET_VIS",
                "author": "작성자A",
                "rating": 5,
                "content": "노출 리뷰",
            },
        )
        visible_id = resp.json()["id"]

        # 숨김 리뷰 생성
        resp = client.post(
            "/api/reviews",
            json={
                "product_no": "WIDGET_VIS",
                "author": "작성자B",
                "rating": 1,
                "content": "숨김 리뷰",
            },
        )
        hidden_id = resp.json()["id"]
        client.patch(
            f"/api/reviews/{hidden_id}/visibility",
            json={"is_visible": False},
        )

        # 위젯 API 조회
        resp = client.get("/api/widget/reviews/WIDGET_VIS")
        data = resp.json()
        review_ids = [item["id"] for item in data["items"]]
        assert visible_id in review_ids
        assert hidden_id not in review_ids

    def test_widget_empty_product(self, client):
        resp = client.get("/api/widget/reviews/NONEXISTENT_PRODUCT")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_reviews"] == 0
        assert data["items"] == []

    def test_widget_pagination(self, client):
        # 6개 리뷰 생성 (per_page=5이면 2페이지)
        for i in range(6):
            client.post(
                "/api/reviews",
                json={
                    "product_no": "WIDGET_PAGE",
                    "author": f"작성자{i}",
                    "rating": 4,
                    "content": f"리뷰 {i}",
                },
            )

        # 1페이지
        resp = client.get("/api/widget/reviews/WIDGET_PAGE?page=1&per_page=5")
        data = resp.json()
        assert len(data["items"]) == 5
        assert data["total_reviews"] == 6

        # 2페이지
        resp = client.get("/api/widget/reviews/WIDGET_PAGE?page=2&per_page=5")
        data = resp.json()
        assert len(data["items"]) == 1

    def test_widget_average_rating(self, client):
        # 별점이 다른 리뷰 생성
        for rating in [5, 4, 3]:
            client.post(
                "/api/reviews",
                json={
                    "product_no": "WIDGET_AVG",
                    "author": "작성자",
                    "rating": rating,
                    "content": f"별점 {rating}",
                },
            )

        resp = client.get("/api/widget/reviews/WIDGET_AVG")
        data = resp.json()
        assert data["average_rating"] == 4.0
