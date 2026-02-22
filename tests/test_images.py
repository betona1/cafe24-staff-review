"""이미지 업로드/삭제 API 테스트."""

from io import BytesIO


def _create_test_image(name: str = "test.jpg", size: int = 100) -> tuple:
    """테스트용 JPEG 이미지 파일을 생성한다."""
    # 최소 JPEG 헤더 + 패딩
    content = b"\xff\xd8\xff\xe0" + b"\x00" * (size - 4)
    return (name, BytesIO(content), "image/jpeg")


class TestImageUpload:
    def test_upload_image(self, client, sample_review):
        # 리뷰 생성
        resp = client.post("/api/reviews", json=sample_review)
        review_id = resp.json()["id"]
        # 이미지 업로드
        resp = client.post(
            f"/api/reviews/{review_id}/images",
            files={"files": _create_test_image()},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 1
        assert data[0]["review_id"] == review_id
        assert data[0]["original_name"] == "test.jpg"

    def test_upload_multiple_images(self, client, sample_review):
        resp = client.post("/api/reviews", json=sample_review)
        review_id = resp.json()["id"]
        files = [
            ("files", _create_test_image("img1.jpg")),
            ("files", _create_test_image("img2.png")),
        ]
        # content_type을 png로 바꿔야 하지만 간단히 jpeg으로 통일
        resp = client.post(f"/api/reviews/{review_id}/images", files=files)
        assert resp.status_code == 201
        assert len(resp.json()) == 2

    def test_upload_to_nonexistent_review(self, client):
        resp = client.post(
            "/api/reviews/99999/images",
            files={"files": _create_test_image()},
        )
        assert resp.status_code == 404

    def test_upload_invalid_file_type(self, client, sample_review):
        resp = client.post("/api/reviews", json=sample_review)
        review_id = resp.json()["id"]
        resp = client.post(
            f"/api/reviews/{review_id}/images",
            files={"files": ("test.txt", BytesIO(b"hello"), "text/plain")},
        )
        assert resp.status_code == 400

    def test_upload_exceeds_max_count(self, client, sample_review):
        resp = client.post("/api/reviews", json=sample_review)
        review_id = resp.json()["id"]
        # 5개 업로드 (최대)
        for i in range(5):
            client.post(
                f"/api/reviews/{review_id}/images",
                files={"files": _create_test_image(f"img{i}.jpg")},
            )
        # 6번째 → 에러
        resp = client.post(
            f"/api/reviews/{review_id}/images",
            files={"files": _create_test_image("overflow.jpg")},
        )
        assert resp.status_code == 400


class TestImageDelete:
    def test_delete_image(self, client, sample_review):
        # 리뷰 + 이미지 생성
        resp = client.post("/api/reviews", json=sample_review)
        review_id = resp.json()["id"]
        resp = client.post(
            f"/api/reviews/{review_id}/images",
            files={"files": _create_test_image()},
        )
        image_id = resp.json()[0]["id"]
        # 이미지 삭제
        resp = client.delete(f"/api/images/{image_id}")
        assert resp.status_code == 200
        assert resp.json()["detail"] == "삭제되었습니다"

    def test_delete_image_not_found(self, client):
        resp = client.delete("/api/images/99999")
        assert resp.status_code == 404
