"""위젯 API 테스트."""

import io


def _upload_image(client, review_id: int, filename: str = "test.png") -> dict:
    """리뷰에 테스트용 PNG 이미지를 업로드하고 응답 데이터를 반환한다."""
    image_file = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    resp = client.post(
        f"/api/reviews/{review_id}/images",
        files=[("files", (filename, image_file, "image/png"))],
    )
    assert resp.status_code == 201, f"이미지 업로드 실패: {resp.text}"
    return resp.json()


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


class TestWidgetRatingDistribution:
    def test_rating_distribution(self, client):
        """별점 분포가 올바르게 계산되는지 검증한다."""
        # 5점 2개, 3점 1개, 1점 1개 생성
        ratings = [5, 5, 3, 1]
        for i, rating in enumerate(ratings):
            client.post(
                "/api/reviews",
                json={
                    "product_no": "WIDGET_DIST",
                    "author": f"분포작성자{i}",
                    "rating": rating,
                    "content": f"별점 분포 테스트 {rating}점",
                },
            )

        resp = client.get("/api/widget/reviews/WIDGET_DIST")
        assert resp.status_code == 200
        data = resp.json()

        dist = data["rating_distribution"]
        assert dist["star_5"] == 2
        assert dist["star_4"] == 0
        assert dist["star_3"] == 1
        assert dist["star_2"] == 0
        assert dist["star_1"] == 1


class TestWidgetPhotoReviewCount:
    def test_photo_review_count(self, client):
        """포토리뷰 수가 올바르게 계산되는지 검증한다."""
        review_ids = []
        # 리뷰 3개 생성
        for i in range(3):
            resp = client.post(
                "/api/reviews",
                json={
                    "product_no": "WIDGET_PHOTO",
                    "author": f"포토작성자{i}",
                    "rating": 4,
                    "content": f"포토 리뷰 테스트 {i}",
                },
            )
            assert resp.status_code == 201
            review_ids.append(resp.json()["id"])

        # 첫 번째, 두 번째 리뷰에만 이미지 업로드 (2개가 포토리뷰)
        _upload_image(client, review_ids[0], "photo1.png")
        _upload_image(client, review_ids[1], "photo2.png")

        resp = client.get("/api/widget/reviews/WIDGET_PHOTO")
        assert resp.status_code == 200
        data = resp.json()

        assert data["photo_review_count"] == 2
        assert data["total_reviews"] == 3


class TestWidgetPhotoOnlyFilter:
    def test_photo_only_filter(self, client):
        """photo_only=true 필터가 포토리뷰만 반환하는지 검증한다."""
        review_ids = []
        # 리뷰 4개 생성
        for i in range(4):
            resp = client.post(
                "/api/reviews",
                json={
                    "product_no": "WIDGET_PHOTO_FILTER",
                    "author": f"필터작성자{i}",
                    "rating": 3 + (i % 3),
                    "content": f"포토 필터 테스트 {i}",
                },
            )
            assert resp.status_code == 201
            review_ids.append(resp.json()["id"])

        # 리뷰 0, 2에만 이미지 업로드
        _upload_image(client, review_ids[0], "filter1.png")
        _upload_image(client, review_ids[2], "filter2.png")

        # photo_only=true로 조회
        resp = client.get(
            "/api/widget/reviews/WIDGET_PHOTO_FILTER?photo_only=true"
        )
        assert resp.status_code == 200
        data = resp.json()

        # 포토리뷰만 반환되어야 함
        returned_ids = [item["id"] for item in data["items"]]
        assert review_ids[0] in returned_ids
        assert review_ids[2] in returned_ids
        assert review_ids[1] not in returned_ids
        assert review_ids[3] not in returned_ids

        # total은 필터링된 수 (2개)
        assert data["total"] == 2

        # total_reviews는 전체 리뷰 수 (4개, 필터 무관)
        assert data["total_reviews"] == 4

        # photo_only=false(기본)로 조회하면 전체 반환
        resp_all = client.get("/api/widget/reviews/WIDGET_PHOTO_FILTER")
        data_all = resp_all.json()
        assert data_all["total"] == 4
        assert len(data_all["items"]) == 4


class TestWidgetSorting:
    def test_sort_rating_high(self, client):
        """rating_high 정렬 시 높은 별점이 먼저 나오는지 검증한다."""
        ratings = [2, 5, 1, 4, 3]
        for i, rating in enumerate(ratings):
            client.post(
                "/api/reviews",
                json={
                    "product_no": "WIDGET_SORT_HIGH",
                    "author": f"정렬작성자H{i}",
                    "rating": rating,
                    "content": f"정렬 테스트 높은순 {rating}점",
                },
            )

        resp = client.get(
            "/api/widget/reviews/WIDGET_SORT_HIGH?sort=rating_high&per_page=50"
        )
        assert resp.status_code == 200
        data = resp.json()
        items = data["items"]

        assert len(items) == 5
        # 첫 번째 아이템이 가장 높은 별점
        assert items[0]["rating"] == 5
        # 내림차순 정렬 확인
        ratings_returned = [item["rating"] for item in items]
        assert ratings_returned == sorted(ratings_returned, reverse=True)

    def test_sort_rating_low(self, client):
        """rating_low 정렬 시 낮은 별점이 먼저 나오는지 검증한다."""
        ratings = [4, 1, 5, 2, 3]
        for i, rating in enumerate(ratings):
            client.post(
                "/api/reviews",
                json={
                    "product_no": "WIDGET_SORT_LOW",
                    "author": f"정렬작성자L{i}",
                    "rating": rating,
                    "content": f"정렬 테스트 낮은순 {rating}점",
                },
            )

        resp = client.get(
            "/api/widget/reviews/WIDGET_SORT_LOW?sort=rating_low&per_page=50"
        )
        assert resp.status_code == 200
        data = resp.json()
        items = data["items"]

        assert len(items) == 5
        # 첫 번째 아이템이 가장 낮은 별점
        assert items[0]["rating"] == 1
        # 오름차순 정렬 확인
        ratings_returned = [item["rating"] for item in items]
        assert ratings_returned == sorted(ratings_returned)


class TestWidgetAllPhotoUrls:
    def test_all_photo_urls(self, client):
        """all_photo_urls에 포토리뷰의 이미지 경로가 포함되는지 검증한다."""
        review_ids = []
        # 리뷰 3개 생성
        for i in range(3):
            resp = client.post(
                "/api/reviews",
                json={
                    "product_no": "WIDGET_PHOTO_URLS",
                    "author": f"URL작성자{i}",
                    "rating": 5,
                    "content": f"포토 URL 테스트 {i}",
                },
            )
            assert resp.status_code == 201
            review_ids.append(resp.json()["id"])

        # 리뷰 0, 1에 이미지 업로드
        img_data_0 = _upload_image(client, review_ids[0], "url_test_0.png")
        img_data_1 = _upload_image(client, review_ids[1], "url_test_1.png")

        uploaded_paths = [img_data_0[0]["file_path"], img_data_1[0]["file_path"]]

        resp = client.get("/api/widget/reviews/WIDGET_PHOTO_URLS")
        assert resp.status_code == 200
        data = resp.json()

        all_photo_urls = data["all_photo_urls"]
        assert len(all_photo_urls) == 2
        # 업로드된 이미지 경로가 모두 포함되어야 함
        for path in uploaded_paths:
            assert path in all_photo_urls

    def test_all_photo_urls_empty_when_no_images(self, client):
        """이미지가 없는 상품의 all_photo_urls는 빈 리스트여야 한다."""
        client.post(
            "/api/reviews",
            json={
                "product_no": "WIDGET_NO_PHOTOS",
                "author": "작성자",
                "rating": 4,
                "content": "이미지 없는 리뷰",
            },
        )

        resp = client.get("/api/widget/reviews/WIDGET_NO_PHOTOS")
        assert resp.status_code == 200
        data = resp.json()

        assert data["all_photo_urls"] == []
        assert data["photo_review_count"] == 0
