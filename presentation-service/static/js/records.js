/**
 * Campus Buzz - 历史记录加载和分页
 */

/**
 * 加载历史记录（带分页）
 */
async function loadRecords() {
    const listDiv = document.getElementById('records-list');
    listDiv.innerHTML = '<div class="loading">Loading records...</div>';

    try {
        const resp = await fetch(`${CONFIG.WORKFLOW_URL}/records`);
        const records = await resp.json();

        allRecords = records;
        currentPage = 1;

        if (records.length === 0) {
            listDiv.innerHTML = '<p style="text-align:center;color:#888;">No submissions yet.</p>';
            document.getElementById('pagination').style.display = 'none';
            return;
        }

        renderPage(1);
        renderPagination();
    } catch (err) {
        listDiv.innerHTML = '<p style="text-align:center;color:#e74c3c;">Failed to load records.</p>';
        document.getElementById('pagination').style.display = 'none';
    }
}

/**
 * 渲染当前页
 */
function renderPage(page) {
    const listDiv = document.getElementById('records-list');
    const start = (page - 1) * CONFIG.PAGE_SIZE;
    const end = start + CONFIG.PAGE_SIZE;
    const pageRecords = allRecords.slice(start, end);

    listDiv.innerHTML = pageRecords.map(r => `
        <div class="record-item" data-id="${r.id}">
            <div class="record-title">${escapeHtml(r.title)}</div>
            <div class="record-meta">
                📅 ${escapeHtml(r.event_date)} &nbsp;|&nbsp; 📍 ${escapeHtml(r.location)} &nbsp;|&nbsp; 👤 ${escapeHtml(r.organiser)}
            </div>
            <div class="record-meta" style="margin-top:4px;">
                Category: <strong>${escapeHtml(r.category || 'N/A')}</strong> &nbsp;|&nbsp;
                Priority: <strong>${escapeHtml(r.priority || 'N/A')}</strong>
            </div>
            ${r.note ? `<div class="record-meta" style="margin-top:4px;color:#666;">📝 ${escapeHtml(r.note)}</div>` : ''}
            <span class="record-status status-${r.status}">${escapeHtml(r.status)}</span>
        </div>
    `).join('');

    attachRecordClickHandlers();
}

/**
 * 渲染分页导航
 */
function renderPagination() {
    const container = document.getElementById('pagination');
    const totalPages = Math.ceil(allRecords.length / CONFIG.PAGE_SIZE);

    if (totalPages <= 1) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'flex';

    let html = '';

    // 上一页
    html += `<button class="page-btn" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>&lt;</button>`;

    // 页码按钮（最多显示5个：1 ... 3 4 5 ... 10）
    if (totalPages <= 5) {
        for (let i = 1; i <= totalPages; i++) {
            html += pageBtn(i);
        }
    } else {
        // 第一页
        html += pageBtn(1);
        // 左侧省略号
        if (currentPage > 3) {
            html += '<span class="page-ellipsis">...</span>';
        }
        // 中间页
        const start = Math.max(2, currentPage - 1);
        const end = Math.min(totalPages - 1, currentPage + 1);
        for (let i = start; i <= end; i++) {
            html += pageBtn(i);
        }
        // 右侧省略号
        if (currentPage < totalPages - 2) {
            html += '<span class="page-ellipsis">...</span>';
        }
        // 最后一页
        html += pageBtn(totalPages);
    }

    // 下一页
    html += `<button class="page-btn" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>&gt;</button>`;

    container.innerHTML = html;
}

/**
 * 生成页码按钮 HTML
 */
function pageBtn(num) {
    return `<button class="page-btn ${num === currentPage ? 'active' : ''}" onclick="goToPage(${num})">${num}</button>`;
}

/**
 * 跳转到指定页
 */
function goToPage(num) {
    const totalPages = Math.ceil(allRecords.length / CONFIG.PAGE_SIZE);
    if (num < 1 || num > totalPages) return;
    currentPage = num;
    renderPage(num);
    renderPagination();
}

/**
 * 设置刷新按钮
 */
function setupRefreshButton() {
    document.getElementById('refresh-btn').addEventListener('click', loadRecords);
}
