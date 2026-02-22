/**
 * 카페24 스태프 리뷰 위젯 (Staff Review Widget)
 *
 * 사용법:
 *   <div id="staff-review-widget" data-product-id="{$product_no}"></div>
 *   <link rel="stylesheet" href="https://서버/static/widget.css">
 *   <script src="https://서버/static/widget.js" data-server="https://서버"></script>
 *
 * 모든 로직은 IIFE 내부에 캡슐화되어 전역 스코프를 오염시키지 않는다.
 */
(function() {
    'use strict';

    // ── 설정 ──────────────────────────────────────────────────
    var currentScript = document.currentScript;

    var SRW = {
        serverUrl: (currentScript && currentScript.getAttribute('data-server')) || '',
        productNo: '',
        container: null,
        page: 1,
        perPage: 5,
        data: null,
        sort: 'latest',
        photoOnly: false,
        contentMaxLength: 150,
        initialLoaded: false
    };

    // ── 아바타 색상 팔레트 ────────────────────────────────────
    var AVATAR_COLORS = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ];

    function getAvatarColor(name) {
        if (!name) return AVATAR_COLORS[0];
        var hash = 0;
        for (var i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
        }
        return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
    }

    // ── 초기화 ────────────────────────────────────────────────
    function init() {
        // 컨테이너 탐색
        SRW.container = document.getElementById('staff-review-widget');
        if (!SRW.container) {
            return; // 컨테이너가 없으면 조용히 종료
        }

        // 컨테이너의 data-product-id 속성에서 상품번호 가져오기
        var containerProductId = SRW.container.getAttribute('data-product-id');
        if (containerProductId) {
            SRW.productNo = containerProductId;
        }

        // 상품번호가 없으면 렌더링하지 않음
        if (!SRW.productNo) {
            return;
        }

        // 위젯 기본 클래스 부여
        SRW.container.classList.add('srw-widget');

        // 첫 페이지 로드
        loadReviews(1);
    }

    // ── API 호출 ──────────────────────────────────────────────
    function loadReviews(page) {
        SRW.page = page;

        // 첫 로드: 전체 위젯에 로딩 표시
        // 이후 로드: 리뷰 목록 영역에만 로딩 표시
        if (!SRW.initialLoaded) {
            SRW.container.innerHTML = renderLoading();
        } else {
            // 리뷰 목록 영역에만 로딩 표시
            var reviewList = SRW.container.querySelector('#srw-review-list');
            if (reviewList) {
                reviewList.innerHTML = renderLoading();
            }
            // 페이지네이션 영역 비우기
            var paginationArea = SRW.container.querySelector('#srw-pagination-area');
            if (paginationArea) {
                paginationArea.innerHTML = '';
            }
        }

        var url = SRW.serverUrl + '/api/widget/reviews/' + encodeURIComponent(SRW.productNo)
            + '?page=' + page
            + '&per_page=' + SRW.perPage
            + '&sort=' + encodeURIComponent(SRW.sort)
            + '&photo_only=' + (SRW.photoOnly ? 'true' : 'false');

        fetch(url)
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                SRW.data = data;

                if (!SRW.initialLoaded) {
                    // 첫 로드: 전체 위젯 렌더링
                    renderWidget(data);
                    SRW.initialLoaded = true;
                } else {
                    // 이후 로드: 리뷰 목록 + 페이지네이션만 갱신
                    updateReviewListArea(data);
                }
            })
            .catch(function(error) {
                console.warn('[StaffReviewWidget] 리뷰 로드 실패:', error);
                if (!SRW.initialLoaded) {
                    renderError();
                } else {
                    // 부분 에러 표시
                    var reviewList = SRW.container.querySelector('#srw-review-list');
                    if (reviewList) {
                        reviewList.innerHTML = '<div class="srw-error"><span class="srw-error-text">리뷰를 불러올 수 없습니다.</span></div>';
                    }
                }
            });
    }

    // ── 전체 위젯 렌더링 ──────────────────────────────────────
    function renderWidget(data) {
        if (!data || data.total_reviews === 0) {
            SRW.container.innerHTML = renderEmpty();
            return;
        }

        var html = '';
        html += renderSummarySection(data);
        html += renderPhotoGalleryStrip(data);
        html += renderFilterBar(data);
        html += '<div class="srw-review-list" id="srw-review-list">';
        for (var i = 0; i < data.items.length; i++) {
            html += renderReviewCard(data.items[i]);
        }
        html += '</div>';
        html += '<div id="srw-pagination-area">' + renderPagination(data) + '</div>';

        SRW.container.innerHTML = html;

        // 이벤트 바인딩
        bindEvents();
    }

    // ── 부분 갱신: 리뷰 목록 + 페이지네이션만 ─────────────────
    function updateReviewListArea(data) {
        // 리뷰 목록 갱신
        var reviewList = SRW.container.querySelector('#srw-review-list');
        if (reviewList) {
            var listHtml = '';
            if (data.items && data.items.length > 0) {
                for (var i = 0; i < data.items.length; i++) {
                    listHtml += renderReviewCard(data.items[i]);
                }
            } else {
                listHtml = '<div class="srw-empty"><span class="srw-empty-text">조건에 맞는 리뷰가 없습니다.</span></div>';
            }
            reviewList.innerHTML = listHtml;
        }

        // 페이지네이션 갱신
        var paginationArea = SRW.container.querySelector('#srw-pagination-area');
        if (paginationArea) {
            paginationArea.innerHTML = renderPagination(data);
        }

        // 필터 탭의 active 상태 갱신
        updateFilterTabState();

        // 정렬 드롭다운 상태 갱신
        var sortSelect = SRW.container.querySelector('.srw-sort-select');
        if (sortSelect) {
            sortSelect.value = SRW.sort;
        }

        // 이벤트 바인딩 (부분 영역)
        bindReviewListEvents();
        bindPaginationEvents();
    }

    // ── 요약 섹션 (평균 별점 + 분포 차트) ─────────────────────
    function renderSummarySection(data) {
        var avg = data.average_rating || 0;
        var total = data.total_reviews || 0;
        var dist = data.rating_distribution || {};

        var displayAvg = avg.toFixed(1);

        // 분포 바 너비 계산을 위해 최대값 구하기
        var maxCount = 0;
        for (var s = 5; s >= 1; s--) {
            var count = dist['star_' + s] || 0;
            if (count > maxCount) {
                maxCount = count;
            }
        }

        var html = '<div class="srw-summary">';

        // 왼쪽: 큰 점수 + 별 + 리뷰 수
        html += '  <div class="srw-summary-left">';
        html += '    <div class="srw-summary-score">' + displayAvg + '</div>';
        html += '    <div class="srw-stars srw-summary-stars">' + renderStars(avg) + '</div>';
        html += '    <div class="srw-summary-count">' + total + '개 리뷰</div>';
        html += '  </div>';

        // 오른쪽: 별점 분포 차트
        html += '  <div class="srw-summary-right">';
        for (var star = 5; star >= 1; star--) {
            var starCount = dist['star_' + star] || 0;
            var barWidth = maxCount > 0 ? ((starCount / maxCount) * 100) : 0;
            html += '    <div class="srw-dist-row">';
            html += '      <span class="srw-dist-label">' + star + '</span>';
            html += '      <div class="srw-dist-bar-bg">';
            html += '        <div class="srw-dist-bar-fill" style="width: ' + barWidth.toFixed(1) + '%"></div>';
            html += '      </div>';
            html += '      <span class="srw-dist-count">' + starCount + '</span>';
            html += '    </div>';
        }
        html += '  </div>';

        html += '</div>';
        return html;
    }

    // ── 포토 갤러리 스트립 ────────────────────────────────────
    function renderPhotoGalleryStrip(data) {
        var photoUrls = data.all_photo_urls || [];
        if (photoUrls.length === 0) {
            return '';
        }

        var photoCount = data.photo_review_count || photoUrls.length;

        var html = '<div class="srw-photo-gallery">';
        html += '  <div class="srw-gallery-title">포토리뷰 <span>' + photoCount + '</span></div>';
        html += '  <div class="srw-gallery-strip">';

        for (var i = 0; i < photoUrls.length; i++) {
            var fullUrl = SRW.serverUrl + '/uploads/' + photoUrls[i];
            html += '    <img class="srw-gallery-thumb" '
                + 'src="' + escapeAttr(fullUrl) + '" '
                + 'alt="포토리뷰 이미지" '
                + 'data-full-url="' + escapeAttr(fullUrl) + '" '
                + 'loading="lazy">';
        }

        html += '  </div>';
        html += '</div>';
        return html;
    }

    // ── 필터 바 (탭 + 정렬) ──────────────────────────────────
    function renderFilterBar(data) {
        var total = data.total_reviews || 0;
        var photoCount = data.photo_review_count || 0;

        var allActiveClass = !SRW.photoOnly ? ' srw-active' : '';
        var photoActiveClass = SRW.photoOnly ? ' srw-active' : '';

        var html = '<div class="srw-filter-bar">';
        html += '  <div class="srw-filter-tabs">';
        html += '    <button class="srw-filter-tab' + allActiveClass + '" data-filter="all">전체 리뷰 ' + total + '</button>';
        html += '    <button class="srw-filter-tab' + photoActiveClass + '" data-filter="photo">포토 리뷰 ' + photoCount + '</button>';
        html += '  </div>';
        html += '  <select class="srw-sort-select">';
        html += '    <option value="latest"' + (SRW.sort === 'latest' ? ' selected' : '') + '>최신순</option>';
        html += '    <option value="rating_high"' + (SRW.sort === 'rating_high' ? ' selected' : '') + '>별점 높은순</option>';
        html += '    <option value="rating_low"' + (SRW.sort === 'rating_low' ? ' selected' : '') + '>별점 낮은순</option>';
        html += '  </select>';
        html += '</div>';
        return html;
    }

    // ── 필터 탭 활성 상태 갱신 ────────────────────────────────
    function updateFilterTabState() {
        var tabs = SRW.container.querySelectorAll('.srw-filter-tab');
        for (var i = 0; i < tabs.length; i++) {
            var filter = tabs[i].getAttribute('data-filter');
            if ((filter === 'all' && !SRW.photoOnly) || (filter === 'photo' && SRW.photoOnly)) {
                tabs[i].classList.add('srw-active');
            } else {
                tabs[i].classList.remove('srw-active');
            }
        }
    }

    // ── 별점 렌더링 ──────────────────────────────────────────
    function renderStars(rating) {
        var html = '';
        for (var i = 1; i <= 5; i++) {
            if (rating >= i) {
                // 꽉 찬 별
                html += '<span class="srw-star srw-star-filled" aria-hidden="true">&#9733;</span>';
            } else if (rating >= i - 0.5) {
                // 반 별 (하프스타): 겹침 기법으로 표현
                html += '<span class="srw-star srw-star-half" aria-hidden="true">';
                html += '<span class="srw-star-half-filled">&#9733;</span>';
                html += '<span class="srw-star-half-empty">&#9733;</span>';
                html += '</span>';
            } else {
                // 빈 별
                html += '<span class="srw-star srw-star-empty" aria-hidden="true">&#9734;</span>';
            }
        }
        return html;
    }

    // ── 리뷰 카드 ────────────────────────────────────────────
    function renderReviewCard(review) {
        var author = review.author || '';
        var avatarChar = author.length > 0 ? author.charAt(0) : '?';
        var avatarColor = getAvatarColor(author);
        var content = review.content || '';
        var isTruncated = content.length > SRW.contentMaxLength;
        var displayContent = isTruncated ? content.substring(0, SRW.contentMaxLength) + '...' : content;

        var html = '<div class="srw-review-card">';

        // 헤더: 아바타 + 작성자 정보
        html += '  <div class="srw-card-header">';
        html += '    <div class="srw-avatar" style="background-color: ' + escapeAttr(avatarColor) + '">' + escapeHtml(avatarChar) + '</div>';
        html += '    <div class="srw-author-info">';
        html += '      <span class="srw-review-author">' + escapeHtml(author) + '</span>';

        // STAFF PICK 뱃지 (작성자 이름 옆)
        if (review.is_staff_pick) {
            html += '      <span class="srw-badge">STAFF PICK</span>';
        }

        html += '      <span class="srw-review-date">' + formatDate(review.created_at) + '</span>';
        html += '    </div>';
        html += '  </div>';

        // 별점
        html += '  <div class="srw-stars srw-review-stars">' + renderStars(review.rating || 0) + '</div>';

        // 제목
        if (review.title) {
            html += '  <div class="srw-review-title">' + escapeHtml(review.title) + '</div>';
        }

        // 본문 (잘림 처리)
        if (content) {
            html += '  <div class="srw-review-content' + (isTruncated ? ' srw-content-collapsed' : '') + '"'
                + (isTruncated ? ' data-full-text="' + escapeAttr(content) + '"' : '')
                + '>' + escapeHtml(displayContent) + '</div>';
            if (isTruncated) {
                html += '  <button class="srw-more-btn">더보기</button>';
            }
        }

        // 이미지 썸네일
        if (review.images && review.images.length > 0) {
            html += '  <div class="srw-review-images">';
            for (var j = 0; j < review.images.length; j++) {
                var img = review.images[j];
                var imageUrl = SRW.serverUrl + '/uploads/' + img.file_path;
                html += '    <img class="srw-thumbnail" '
                    + 'src="' + escapeAttr(imageUrl) + '" '
                    + 'alt="' + escapeAttr(img.original_name || '리뷰 이미지') + '" '
                    + 'data-full-url="' + escapeAttr(imageUrl) + '" '
                    + 'loading="lazy">';
            }
            html += '  </div>';
        }

        html += '</div>';
        return html;
    }

    // ── 페이지네이션 ─────────────────────────────────────────
    function renderPagination(data) {
        var total = data.total || 0;
        var perPage = data.per_page || SRW.perPage;
        var currentPage = data.page || 1;
        var totalPages = Math.ceil(total / perPage);

        if (totalPages <= 1) {
            return '';
        }

        var html = '<div class="srw-pagination">';

        // 이전 버튼
        html += '<button class="srw-page-btn srw-page-prev" '
            + 'data-page="' + (currentPage - 1) + '"'
            + (currentPage <= 1 ? ' disabled' : '')
            + ' aria-label="이전 페이지">'
            + '&#9664;'
            + '</button>';

        // 페이지 번호 (최대 5개 표시)
        var startPage = Math.max(1, currentPage - 2);
        var endPage = Math.min(totalPages, startPage + 4);
        startPage = Math.max(1, endPage - 4);

        for (var p = startPage; p <= endPage; p++) {
            var activeClass = (p === currentPage) ? ' srw-page-active' : '';
            html += '<button class="srw-page-btn srw-page-number' + activeClass + '" '
                + 'data-page="' + p + '"'
                + (p === currentPage ? ' aria-current="page"' : '')
                + '>' + p + '</button>';
        }

        // 다음 버튼
        html += '<button class="srw-page-btn srw-page-next" '
            + 'data-page="' + (currentPage + 1) + '"'
            + (currentPage >= totalPages ? ' disabled' : '')
            + ' aria-label="다음 페이지">'
            + '&#9654;'
            + '</button>';

        html += '</div>';
        return html;
    }

    // ── 상태 렌더링 (로딩 / 빈 상태 / 에러) ──────────────────
    function renderLoading() {
        return '<div class="srw-loading">'
            + '<div class="srw-spinner"></div>'
            + '<span class="srw-loading-text">리뷰를 불러오는 중...</span>'
            + '</div>';
    }

    function renderEmpty() {
        return '<div class="srw-empty">'
            + '<span class="srw-empty-text">아직 등록된 리뷰가 없습니다.</span>'
            + '</div>';
    }

    function renderError() {
        SRW.container.innerHTML = '<div class="srw-error">'
            + '<span class="srw-error-text">리뷰를 불러올 수 없습니다.</span>'
            + '</div>';
    }

    // ── 라이트박스 ───────────────────────────────────────────
    function openLightbox(imageUrl) {
        // 기존 라이트박스 제거
        closeLightbox();

        var overlay = document.createElement('div');
        overlay.className = 'srw-lightbox';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-label', '이미지 보기');

        var img = document.createElement('img');
        img.className = 'srw-lightbox-img';
        img.src = imageUrl;
        img.alt = '리뷰 이미지';

        var closeBtn = document.createElement('button');
        closeBtn.className = 'srw-lightbox-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.setAttribute('aria-label', '닫기');

        overlay.appendChild(img);
        overlay.appendChild(closeBtn);
        document.body.appendChild(overlay);

        // 닫기 이벤트
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            closeLightbox();
        });

        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                closeLightbox();
            }
        });

        // ESC 키
        document.addEventListener('keydown', handleLightboxKeydown);

        // body 스크롤 방지
        document.body.style.overflow = 'hidden';
    }

    function closeLightbox() {
        var existing = document.querySelector('.srw-lightbox');
        if (existing) {
            existing.parentNode.removeChild(existing);
            document.body.style.overflow = '';
            document.removeEventListener('keydown', handleLightboxKeydown);
        }
    }

    function handleLightboxKeydown(e) {
        if (e.key === 'Escape' || e.keyCode === 27) {
            closeLightbox();
        }
    }

    // ── 이벤트 바인딩 (전체) ──────────────────────────────────
    function bindEvents() {
        if (!SRW.container) return;

        // 필터 탭 클릭
        bindFilterTabEvents();

        // 정렬 드롭다운 변경
        bindSortSelectEvents();

        // 갤러리 썸네일 클릭 -> 라이트박스
        bindGalleryEvents();

        // 리뷰 목록 내부 이벤트
        bindReviewListEvents();

        // 페이지네이션 이벤트
        bindPaginationEvents();
    }

    // ── 필터 탭 이벤트 ────────────────────────────────────────
    function bindFilterTabEvents() {
        var tabs = SRW.container.querySelectorAll('.srw-filter-tab');
        for (var i = 0; i < tabs.length; i++) {
            tabs[i].addEventListener('click', function(e) {
                var filter = e.currentTarget.getAttribute('data-filter');
                if (filter === 'photo') {
                    SRW.photoOnly = true;
                } else {
                    SRW.photoOnly = false;
                }
                // 탭 활성 상태 즉시 갱신
                updateFilterTabState();
                loadReviews(1);
            });
        }
    }

    // ── 정렬 드롭다운 이벤트 ──────────────────────────────────
    function bindSortSelectEvents() {
        var sortSelect = SRW.container.querySelector('.srw-sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', function(e) {
                SRW.sort = e.target.value;
                loadReviews(1);
            });
        }
    }

    // ── 갤러리 이벤트 ─────────────────────────────────────────
    function bindGalleryEvents() {
        var galleryThumbs = SRW.container.querySelectorAll('.srw-gallery-thumb');
        for (var i = 0; i < galleryThumbs.length; i++) {
            galleryThumbs[i].addEventListener('click', function(e) {
                var fullUrl = e.currentTarget.getAttribute('data-full-url');
                if (fullUrl) {
                    openLightbox(fullUrl);
                }
            });
        }
    }

    // ── 리뷰 목록 이벤트 (썸네일 + 더보기) ────────────────────
    function bindReviewListEvents() {
        // 이미지 썸네일 클릭 -> 라이트박스
        var thumbnails = SRW.container.querySelectorAll('#srw-review-list .srw-thumbnail');
        for (var i = 0; i < thumbnails.length; i++) {
            thumbnails[i].addEventListener('click', function(e) {
                var fullUrl = e.currentTarget.getAttribute('data-full-url');
                if (fullUrl) {
                    openLightbox(fullUrl);
                }
            });
        }

        // "더보기" 버튼 클릭 -> 전체 내용 표시
        var moreBtns = SRW.container.querySelectorAll('#srw-review-list .srw-more-btn');
        for (var j = 0; j < moreBtns.length; j++) {
            moreBtns[j].addEventListener('click', function(e) {
                var btn = e.currentTarget;
                var contentEl = btn.previousElementSibling;
                if (contentEl && contentEl.classList.contains('srw-content-collapsed')) {
                    var fullText = contentEl.getAttribute('data-full-text');
                    if (fullText) {
                        contentEl.textContent = fullText;
                    }
                    contentEl.classList.remove('srw-content-collapsed');
                    btn.style.display = 'none';
                }
            });
        }
    }

    // ── 페이지네이션 이벤트 ───────────────────────────────────
    function bindPaginationEvents() {
        var pageButtons = SRW.container.querySelectorAll('.srw-page-btn');
        for (var i = 0; i < pageButtons.length; i++) {
            pageButtons[i].addEventListener('click', function(e) {
                var btn = e.currentTarget;
                if (btn.disabled) return;
                var page = parseInt(btn.getAttribute('data-page'), 10);
                if (page && page > 0) {
                    loadReviews(page);
                    // 위젯 상단으로 스크롤
                    SRW.container.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        }
    }

    // ── 유틸리티 ─────────────────────────────────────────────
    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function escapeAttr(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function formatDate(dateStr) {
        if (!dateStr) return '';
        // ISO 형식에서 날짜 부분만 추출
        var date = new Date(dateStr);
        if (isNaN(date.getTime())) return dateStr;

        var year = date.getFullYear();
        var month = ('0' + (date.getMonth() + 1)).slice(-2);
        var day = ('0' + date.getDate()).slice(-2);
        return year + '-' + month + '-' + day;
    }

    // ── DOM 준비 후 초기화 ───────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
