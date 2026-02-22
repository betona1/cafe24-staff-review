"""쿠팡 상품 리뷰 크롤링 → 엑셀 파일 + 이미지 다운로드 스크립트.

Xvfb + undetected_chromedriver를 사용하여 쿠팡 Akamai 봇 감지를 우회한다.

사용법:
    xvfb-run -a python scripts/crawl_coupang.py <쿠팡_상품_URL> <카페24_상품번호> [--pages 5] [--images]

예시:
    xvfb-run -a python scripts/crawl_coupang.py https://www.coupang.com/vp/products/7854738100 12022 --pages 10 --images
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import undetected_chromedriver as uc
from curl_cffi import requests as curl_requests
from openpyxl import Workbook

CHROME_PATH = "/home/joacham/cafe24app/chrome-linux64/chrome"


def extract_product_id(url: str) -> str:
    """쿠팡 URL에서 상품 ID를 추출한다."""
    match = re.search(r"/products/(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"itemId=(\d+)", url)
    if match:
        return match.group(1)
    raise ValueError(f"URL에서 상품 ID를 추출할 수 없습니다: {url}")


def _create_driver():
    """봇 감지를 우회하는 Chrome 드라이버를 생성한다."""
    options = uc.ChromeOptions()
    options.binary_location = CHROME_PATH
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=ko-KR")
    return uc.Chrome(options=options)


def _extract_reviews_from_page(driver) -> list[dict]:
    """현재 페이지에 로드된 리뷰를 추출한다 (이미지 URL 포함)."""
    return driver.execute_script(r'''
        const helpBtns = document.querySelectorAll('.js_reviewArticleHelpfulContainer');
        const results = [];

        for (let i = 0; i < helpBtns.length; i++) {
            const article = helpBtns[i].closest('article');
            if (!article) continue;

            const r = {};

            // 헤더: article > div(첫째) > div(둘째=정보컬럼)
            const headerDiv = article.children[0];
            if (headerDiv && headerDiv.children[1]) {
                const infoCol = headerDiv.children[1];
                const lines = infoCol.children;

                // 라인 0: 작성자명 (span[data-member-id])
                if (lines[0]) {
                    const authorSpan = lines[0].querySelector('span[data-member-id]');
                    r.author = authorSpan
                        ? authorSpan.textContent.trim().replace(/\u00a0/g, '')
                        : '';
                }

                // 라인 1: 별점 (full-star 아이콘 수) + 날짜
                if (lines[1]) {
                    const fullStars = lines[1].querySelectorAll('i.twc-bg-full-star');
                    const halfStars = lines[1].querySelectorAll('i.twc-bg-half-star');
                    r.rating = fullStars.length + (halfStars.length > 0 ? 1 : 0);
                    if (r.rating === 0) r.rating = 5;

                    // 날짜: 텍스트에서 YYYY.MM.DD 패턴 추출
                    const lineText = lines[1].textContent.trim();
                    const dateMatch = lineText.match(/(\d{4}\.\d{2}\.\d{2})/);
                    r.date = dateMatch ? dateMatch[1] : '';
                }
            }

            // 제목: twc-font-bold + twc-text-bluegray-900 클래스 div
            const allDivs = article.querySelectorAll('div');
            r.title = '';
            for (const div of allDivs) {
                if (div.className.includes('twc-font-bold') &&
                    div.className.includes('twc-text-bluegray-900') &&
                    !div.querySelector('svg, img, button') &&
                    div.textContent.trim().length < 200) {
                    r.title = div.textContent.trim();
                    break;
                }
            }

            // 내용: twc-break-all 클래스 div
            r.content = '';
            for (const div of allDivs) {
                if (div.className.includes('twc-break-all')) {
                    r.content = div.textContent.trim();
                    break;
                }
            }

            // 이미지 URL 추출
            r.images = [];
            const imgs = article.querySelectorAll('img');
            for (const img of imgs) {
                const src = img.src || img.getAttribute('data-src') || '';
                // 리뷰 이미지만 (아바타, 아이콘 제외)
                if (src && src.includes('coupangcdn.com') &&
                    !src.includes('profile') && !src.includes('icon') &&
                    !src.includes('badge') && !src.includes('thumbnail/image')) {
                    // 썸네일 → 원본 크기로 변환
                    let fullUrl = src;
                    // /thumbnails/remote/q89/ → 고품질
                    fullUrl = fullUrl.replace(/\/q\d+\//, '/q89/');
                    // 크기 제한 제거 (있는 경우)
                    fullUrl = fullUrl.replace(/\/resize\/\d+x\d+\//, '/');
                    r.images.push(fullUrl);
                }
            }

            if (r.content) {
                results.push(r);
            }
        }

        return results;
    ''') or []


def download_images(
    reviews: list[dict],
    output_dir: str,
) -> dict[int, list[str]]:
    """리뷰 이미지를 다운로드한다.

    Returns:
        {리뷰인덱스: [로컬파일경로, ...]} 매핑
    """
    image_map: dict[int, list[str]] = {}
    total_images = sum(len(r.get("images", [])) for r in reviews)

    if total_images == 0:
        print("다운로드할 이미지가 없습니다.")
        return image_map

    os.makedirs(output_dir, exist_ok=True)
    print(f"\n이미지 다운로드 중... (총 {total_images}장 → {output_dir}/)")

    session = curl_requests.Session(impersonate="safari")
    downloaded = 0
    failed = 0

    for idx, review in enumerate(reviews):
        urls = review.get("images", [])
        if not urls:
            continue

        review_dir = os.path.join(output_dir, f"review_{idx + 1:03d}")
        os.makedirs(review_dir, exist_ok=True)
        image_map[idx] = []

        for img_idx, img_url in enumerate(urls):
            # 확장자 추출
            parsed = urlparse(img_url)
            ext = Path(parsed.path).suffix or ".jpg"
            if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
                ext = ".jpg"

            filename = f"img_{img_idx + 1:02d}{ext}"
            filepath = os.path.join(review_dir, filename)

            try:
                resp = session.get(img_url, timeout=15)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                    image_map[idx].append(filepath)
                    downloaded += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        if (idx + 1) % 10 == 0:
            print(f"  {idx + 1}/{len(reviews)} 리뷰 처리 완료...")

    session.close()
    print(f"이미지 다운로드 완료: 성공 {downloaded}장, 실패 {failed}장")
    return image_map


def crawl_reviews(url: str, max_pages: int = 5) -> tuple[list[dict], str]:
    """쿠팡 리뷰를 크롤링한다."""
    reviews: list[dict] = []
    product_name = ""

    driver = _create_driver()
    try:
        print(f"상품 페이지 로딩 중: {url}")
        driver.get(url)

        # Akamai 챌린지 통과 대기
        print("Akamai 챌린지 대기 (12초)...")
        time.sleep(12)

        title = driver.title
        if "Access Denied" in title:
            print("봇 감지됨. 추가 대기 후 재시도...")
            time.sleep(10)
            driver.refresh()
            time.sleep(10)
            title = driver.title

        if "Access Denied" in title:
            print("접근 거부됨. 쿠팡 봇 감지를 통과하지 못했습니다.")
            return [], ""

        print(f"페이지 로드 완료: {title}")

        # 상품명 추출
        try:
            product_name = driver.execute_script(r'''
                const selectors = [
                    'h1.prod-buy-header__title',
                    '.prod-buy-header__title',
                    'h2.prod-buy-header__title',
                    'h1',
                ];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.textContent.trim()) {
                        return el.textContent.trim();
                    }
                }
                const title = document.title;
                if (title && !title.includes('Access Denied')) {
                    return title.split(' - ')[0].trim();
                }
                return '';
            ''') or ""
            if product_name:
                print(f"상품명: {product_name}")
        except Exception:
            pass

        # 리뷰 섹션으로 스크롤
        print("리뷰 섹션으로 스크롤...")
        for pct in [0.3, 0.5, 0.7]:
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {pct})")
            time.sleep(0.5)
        time.sleep(2)

        # 페이지별 크롤링
        for page_num in range(1, max_pages + 1):
            print(f"\n  리뷰 페이지 {page_num}/{max_pages} 크롤링 중...")

            page_reviews = _extract_reviews_from_page(driver)
            page_img_count = sum(len(r.get("images", [])) for r in page_reviews)
            print(f"    → {len(page_reviews)}개 리뷰 추출 (이미지 {page_img_count}장)")

            if not page_reviews:
                print("    리뷰가 없습니다. 종료.")
                break

            # 중복 제거
            existing_contents = {r.get("content", "")[:50] for r in reviews}
            new_reviews = [
                r for r in page_reviews
                if r.get("content", "")[:50] not in existing_contents
            ]

            if not new_reviews and page_num > 1:
                print("    새 리뷰 없음 (중복). 종료.")
                break

            reviews.extend(new_reviews)
            print(f"    새 리뷰 {len(new_reviews)}개 추가 (총 {len(reviews)}개)")

            # 다음 페이지 이동
            if page_num < max_pages:
                next_page = page_num + 1
                clicked = driver.execute_script(f'''
                    const allButtons = document.querySelectorAll('button');
                    for (const btn of allButtons) {{
                        if (btn.textContent.trim() === '{next_page}' &&
                            btn.className.includes('twc-inline-flex')) {{
                            btn.scrollIntoView({{block: 'center'}});
                            btn.click();
                            return true;
                        }}
                    }}
                    return false;
                ''')

                if not clicked:
                    print("    다음 페이지 버튼 없음. 종료.")
                    break

                time.sleep(3)

    finally:
        driver.quit()

    print(f"\n총 {len(reviews)}개 리뷰 크롤링 완료")
    total_imgs = sum(len(r.get("images", [])) for r in reviews)
    print(f"총 이미지 URL: {total_imgs}개")
    return reviews, product_name


def save_to_excel(
    reviews: list[dict],
    cafe24_product_no: str,
    product_name: str,
    output_path: str,
) -> None:
    """크롤링한 리뷰를 엑셀 파일로 저장한다."""
    wb = Workbook()
    ws = wb.active
    ws.title = "리뷰"
    ws.append(["상품번호", "상품명", "작성자명", "별점(1~5)", "리뷰제목", "리뷰내용", "작성일(YYYY-MM-DD)"])

    for r in reviews:
        date_str = r.get("date", "")
        date_str = date_str.replace(".", "-").strip()
        if len(date_str) > 10:
            date_str = date_str[:10]

        rating = min(max(int(r.get("rating", 5)), 1), 5)

        ws.append([
            cafe24_product_no,
            product_name,
            r.get("author", "구매자") or "구매자",
            rating,
            r.get("title", ""),
            r.get("content", ""),
            date_str,
        ])

    wb.save(output_path)
    print(f"엑셀 저장 완료: {output_path} ({len(reviews)}개 리뷰)")


def main():
    parser = argparse.ArgumentParser(
        description="쿠팡 리뷰 크롤링 → 엑셀 + 이미지 다운로드\n\n"
                    "주의: xvfb-run -a 로 실행해야 합니다.\n"
                    "예: xvfb-run -a python scripts/crawl_coupang.py URL PRODUCT_NO --images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="쿠팡 상품 URL")
    parser.add_argument("product_no", help="카페24 상품번호")
    parser.add_argument("--pages", type=int, default=5, help="크롤링할 리뷰 페이지 수 (기본: 5)")
    parser.add_argument("--output", default=None, help="출력 엑셀 파일 경로")
    parser.add_argument("--images", action="store_true", help="리뷰 이미지도 다운로드")
    parser.add_argument("--image-dir", default=None, help="이미지 저장 디렉토리")
    args = parser.parse_args()

    product_id = extract_product_id(args.url)
    print(f"쿠팡 상품 ID: {product_id}")

    reviews, product_name = crawl_reviews(args.url, max_pages=args.pages)

    if not reviews:
        print("크롤링된 리뷰가 없습니다.")
        sys.exit(1)

    # 엑셀 저장
    output = args.output or f"coupang_reviews_{product_id}.xlsx"
    save_to_excel(reviews, args.product_no, product_name, output)

    # 이미지 다운로드
    if args.images:
        image_dir = args.image_dir or f"coupang_images_{product_id}"
        image_map = download_images(reviews, image_dir)

        # 이미지 매핑 정보 저장 (업로드 스크립트용)
        if image_map:
            import json
            mapping_path = os.path.join(image_dir, "_mapping.json")
            mapping_data = []
            for idx, paths in image_map.items():
                review = reviews[idx]
                mapping_data.append({
                    "review_index": idx + 1,
                    "author": review.get("author", ""),
                    "content_preview": review.get("content", "")[:50],
                    "images": paths,
                })
            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(mapping_data, f, ensure_ascii=False, indent=2)
            print(f"이미지 매핑 정보: {mapping_path}")

    print(f"\n=== 완료 ===")
    print(f"엑셀 파일: {output}")
    if args.images:
        print(f"이미지 폴더: {image_dir}")
    print(f"\n다음 단계:")
    print(f"  1. 관리자 /admin → 엑셀 업로드 → {output}")
    if args.images:
        print(f"  2. 이미지 업로드:")
        print(f"     xvfb-run -a python scripts/upload_images.py {image_dir} --server <서버URL>")


if __name__ == "__main__":
    main()
