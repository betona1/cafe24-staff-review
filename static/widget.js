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
        productNo: (currentScript && currentScript.getAttribute('data-product-no')) || '',
        container: null,
        page: 1,
        perPage: 5,
        data: null
    };

    // ── 초기화 ────────────────────────────────────────────────
    function init() {
        // 컨테이너 탐색
        SRW.container = document.getElementById('staff-review-widget');
        if (!SRW.container) {
            return; // 컨테이너가 없으면 조용히 종료
        }

        // 컨테이너의 data-product-id 속성에서 상품번호 가져오기 (우선)
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

        // 로딩 표시
        SRW.container.innerHTML = renderLoading();

        var url = SRW.serverUrl + '/api/widget/reviews/' + encodeURIComponent(SRW.productNo)
            + '?page=' + page
            + '&per_page=' + SRW.perPage;

        fetch(url)
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                SRW.data = data;
                renderWidget(data);
            })
            .catch(function(error) {
                console.warn('[StaffReviewWidget] 리뷰 로드 실패:', error);
                renderError();
            });
    }

    // ── 전체 위젯 렌더링 ──────────────────────────────────────
    function renderWidget(data) {
        if (!data || !data.items || data.total_reviews === 0) {
            SRW.container.innerHTML = renderEmpty();
            return;
        }

        var html = '';
        html += renderHeader(data);
        html += '<div class="srw-review-list">';
        for (var i = 0; i < data.items.length; i++) {
            html += renderReviewCard(data.items[i]);
        }
        html += '</div>';
        html += renderPagination(data);

        SRW.container.innerHTML = html;

        // 이벤트 바인딩
        bindEvents();
    }

    // ── 헤더 (평균 별점 + 리뷰 수) ───────────────────────────
    function renderHeader(data) {
        var avg = data.average_rating || 0;
        var total = data.total_reviews || 0;
        var displayAvg = avg.toFixed(1);

        var html = '<div class="srw-header">';
        html += '  <div class="srw-header-rating">';
        html += '    <span class="srw-stars">' + renderStars(avg) + '</span>';
        html += '    <span class="srw-rating-number">' + displayAvg + '</span>';
        html += '  </div>';
        html += '  <div class="srw-header-count">';
        html += '    <span class="srw-review-count-label">' + escapeHtml('리뷰') + ' </span>';
        html += '    <span class="srw-review-count-number">' + total + '</span>';
        html += '    <span class="srw-review-count-unit">' + escapeHtml('개') + '</span>';
        html += '  </div>';
        html += '</div>';
        return html;
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
        var html = '<div class="srw-review-card">';

        // 메타: 별점 + 작성자 + 날짜 + 뱃지
        html += '  <div class="srw-review-meta">';
        html += '    <span class="srw-stars srw-review-stars">' + renderStars(review.rating || 0) + '</span>';
        html += '    <span class="srw-review-author">' + escapeHtml(review.author || '') + '</span>';
        html += '    <span class="srw-review-date">' + formatDate(review.created_at) + '</span>';

        // STAFF PICK 뱃지
        if (review.is_staff_pick) {
            html += '    <span class="srw-badge">STAFF PICK</span>';
        }

        html += '  </div>';

        // 제목
        if (review.title) {
            html += '  <div class="srw-review-title">' + escapeHtml(review.title) + '</div>';
        }

        // 본문
        if (review.content) {
            html += '  <div class="srw-review-content">' + escapeHtml(review.content) + '</div>';
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
            + '<span class="srw-loading-text">' + escapeHtml('리뷰를 불러오는 중...') + '</span>'
            + '</div>';
    }

    function renderEmpty() {
        return '<div class="srw-empty">'
            + '<span class="srw-empty-text">' + escapeHtml('아직 등록된 리뷰가 없습니다.') + '</span>'
            + '</div>';
    }

    function renderError() {
        SRW.container.innerHTML = '<div class="srw-error">'
            + '<span class="srw-error-text">' + escapeHtml('리뷰를 불러올 수 없습니다.') + '</span>'
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

    // ── 이벤트 바인딩 ────────────────────────────────────────
    function bindEvents() {
        if (!SRW.container) return;

        // 페이지네이션 버튼
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

        // 이미지 썸네일 클릭 -> 라이트박스
        var thumbnails = SRW.container.querySelectorAll('.srw-thumbnail');
        for (var j = 0; j < thumbnails.length; j++) {
            thumbnails[j].addEventListener('click', function(e) {
                var fullUrl = e.currentTarget.getAttribute('data-full-url');
                if (fullUrl) {
                    openLightbox(fullUrl);
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
