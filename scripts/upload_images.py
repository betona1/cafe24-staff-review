"""크롤링한 이미지를 리뷰 서버에 업로드하는 스크립트.

crawl_coupang.py로 다운로드한 이미지를 리뷰 API에 업로드한다.
리뷰 내용 앞 50자를 기준으로 매칭하여 해당 리뷰에 이미지를 연결한다.

사용법:
    python scripts/upload_images.py <이미지_디렉토리> --server <서버URL>

예시:
    python scripts/upload_images.py coupang_images_7854738100 --server https://web-production-b52f6.up.railway.app
    python scripts/upload_images.py coupang_images_7854738100 --server http://localhost:8000
"""

import argparse
import json
import os
import sys

import httpx


def load_mapping(image_dir: str) -> list[dict]:
    """이미지 매핑 정보를 로드한다."""
    mapping_path = os.path.join(image_dir, "_mapping.json")
    if not os.path.exists(mapping_path):
        print(f"매핑 파일을 찾을 수 없습니다: {mapping_path}")
        print("crawl_coupang.py --images 로 먼저 크롤링하세요.")
        sys.exit(1)

    with open(mapping_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_review_id(client: httpx.Client, server: str, content_preview: str) -> int | None:
    """리뷰 내용으로 서버에서 리뷰 ID를 찾는다."""
    # 검색 키워드: 내용의 처음 20자
    search_term = content_preview[:20].strip()
    if not search_term:
        return None

    resp = client.get(
        f"{server}/api/reviews",
        params={"search": search_term, "per_page": 5},
    )
    if resp.status_code != 200:
        return None

    data = resp.json()
    for item in data.get("items", []):
        # 내용 앞부분이 일치하는 리뷰 찾기
        if item.get("content", "")[:40] == content_preview[:40]:
            return item["id"]

    return None


def upload_images(image_dir: str, server: str) -> None:
    """이미지를 서버에 업로드한다."""
    mapping = load_mapping(image_dir)

    if not mapping:
        print("업로드할 이미지가 없습니다.")
        return

    total_images = sum(len(m["images"]) for m in mapping)
    print(f"업로드 대상: {len(mapping)}개 리뷰, {total_images}장 이미지")
    print(f"서버: {server}")
    print()

    uploaded = 0
    skipped = 0
    failed = 0

    client = httpx.Client(timeout=30)

    for entry in mapping:
        review_idx = entry["review_index"]
        author = entry["author"]
        content_preview = entry["content_preview"]
        image_paths = entry["images"]

        if not image_paths:
            continue

        # 서버에서 리뷰 ID 찾기
        review_id = find_review_id(client, server, content_preview)

        if review_id is None:
            print(f"  리뷰 #{review_idx} ({author}): 서버에서 찾을 수 없음 → 건너뜀")
            skipped += len(image_paths)
            continue

        # 이미지 업로드
        for img_path in image_paths:
            if not os.path.exists(img_path):
                failed += 1
                continue

            filename = os.path.basename(img_path)
            try:
                with open(img_path, "rb") as f:
                    resp = client.post(
                        f"{server}/api/reviews/{review_id}/images",
                        files={"file": (filename, f, "image/jpeg")},
                    )

                if resp.status_code == 200:
                    uploaded += 1
                else:
                    print(f"    {filename}: HTTP {resp.status_code} - {resp.text[:100]}")
                    failed += 1
            except Exception as e:
                print(f"    {filename}: 오류 - {e}")
                failed += 1

        print(f"  리뷰 #{review_idx} ({author}, ID={review_id}): {len(image_paths)}장 업로드")

    client.close()

    print(f"\n=== 업로드 완료 ===")
    print(f"성공: {uploaded}장")
    print(f"건너뜀: {skipped}장 (리뷰 매칭 실패)")
    print(f"실패: {failed}장")


def main():
    parser = argparse.ArgumentParser(
        description="크롤링한 이미지를 리뷰 서버에 업로드",
    )
    parser.add_argument("image_dir", help="이미지 디렉토리 (crawl_coupang.py로 생성)")
    parser.add_argument(
        "--server",
        required=True,
        help="리뷰 서버 URL (예: https://web-production-b52f6.up.railway.app)",
    )
    args = parser.parse_args()

    upload_images(args.image_dir, args.server.rstrip("/"))


if __name__ == "__main__":
    main()
