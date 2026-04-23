/**
 * Campus Buzz - Record loading and pagination
 */

/**
 * Load records with pagination
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
 * Render the current page
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
                📅 {escapeHtml(r.event_date)} &amp;nbsp;|&amp;nbsp; 📍{escapeHtml(r.location)} &nbsp;|&nbsp; 👤 ${escapeHtml(r.organiser)}
            </div>
            <div class="record-meta" style="margin-top:4px;">
                Category: <strong>${escapeHtml(r.category || 'N/A')}</strong> &nbsp;|&nbsp;
                Priority: <strong>${escapeHtml(r.priority || 'N/A')}</strong>
            </div>
            {r.note ? `&lt;div class=&quot;record-meta&quot; style=&quot;margin-top:4px;color:#666;&quot;&gt;📝{escapeHtml(r.note)}</div>` : ''}
            <span class="record-status status-{r.status}&quot;&gt;{escapeHtml(r.status)}</span>
        </div>
    `).join('');

    attachRecordClickHandlers();
}

/**
 * Render pagination controls
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

    // Previous page
    html += `<button class="page-btn" onclick="goToPage({currentPage - 1})&quot;{currentPage === 1 ? 'disabled' : ''}>&lt;</button>`;

    // Page buttons (show up to 5 pages: 1 ... 3 4 5 ... 10)
    if (totalPages <= 5) {
        for (let i = 1; i <= totalPages; i++) {
            html += pageBtn(i);
        }
    } else {
        // First page
        html += pageBtn(1);

        // Left ellipsis
        if (currentPage > 3) {
            html += '<span class="page-ellipsis">...</span>';
        }

        // Middle pages
        const start = Math.max(2, currentPage - 1);
        const end = Math.min(totalPages - 1, currentPage + 1);
        for (let i = start; i <= end; i++) {
            html += pageBtn(i);
        }

        // Right ellipsis
        if (currentPage < totalPages - 2) {
            html += '<span class="page-ellipsis">...</span>';
        }

        // Last page
        html += pageBtn(totalPages);
    }

    // Next page
    html += `<button class="page-btn" onclick="goToPage({currentPage + 1})&quot;{currentPage === totalPages ? 'disabled' : ''}>&gt;</button>`;

    container.innerHTML = html;
}

/**
 * Build page button HTML
 */
function pageBtn(num) {
    return `<button class="page-btn {num === currentPage ? &#39;active&#39; : &#39;&#39;}&quot; onclick=&quot;goToPage({num})">${num}</button>`;
}

/**
 * Go to a specific page
 */
function goToPage(num) {
    const totalPages = Math.ceil(allRecords.length / CONFIG.PAGE_SIZE);
    if (num < 1 || num > totalPages) return;
    currentPage = num;
    renderPage(num);
    renderPagination();
}

/**
 * Set up refresh button
 */
function setupRefreshButton() {
    document.getElementById('refresh-btn').addEventListener('click', loadRecords);
}
