/**
 * Campus Buzz - Presentation Service frontend logic
 *
 * What this file does:
 *   1. Handles form submission and sends data to the Workflow Service
 *   2. Polls for processing results
 *   3. Loads and displays submission history
 */

// ============================================================
// Config
// ============================================================
const WORKFLOW_URL = '/api';   // Routed through the Presentation Service proxy
const POLL_INTERVAL = 2000;    // Polling interval in milliseconds
const MAX_POLL_COUNT = 30;     // Max number of polling attempts
const PAGE_SIZE = 5;           // Records shown per page

let allRecords = [];           // Cache all records for pagination
let currentPage = 1;

// ============================================================
// Initial page setup
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    loadRecords();
    setupFormHandler();
    setupDescCounter();
    setupRefreshButton();
});

// ============================================================
// Form submission
// ============================================================
function setupFormHandler() {
    const form = document.getElementById('event-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = document.getElementById('submit-btn');
        const messageDiv = document.getElementById('submit-message');

        // Collect form values
        const formData = {
            title: document.getElementById('title').value.trim(),
            description: document.getElementById('description').value.trim(),
            location: document.getElementById('location').value.trim(),
            event_date: document.getElementById('event_date').value.trim(),
            organiser: document.getElementById('organiser').value.trim()
        };

        // Lock the button while the request is running
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
        messageDiv.style.display = 'none';

        try {
            // Send submission to the Workflow Service
            const resp = await fetch(`${WORKFLOW_URL}/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const result = await resp.json();

            if (resp.ok) {
                showMessage('info', `Submission received! Record ID: ${result.record_id}. Processing in background...`);

                // Start polling for the final result
                pollResult(result.record_id);
            } else {
                showMessage('error', result.error || 'Submission failed. Please try again.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Event';
            }
        } catch (err) {
            showMessage('error', 'Network error. Please check if the service is running.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Event';
        }
    });
}

// ============================================================
// Description counter
// ============================================================
function setupDescCounter() {
    const desc = document.getElementById('description');
    const counter = document.getElementById('desc-counter');

    desc.addEventListener('input', () => {
        const len = desc.value.trim().length;
        counter.textContent = `${len} / 40 characters minimum`;
        counter.className = len >= 40 ? 'valid' : '';
    });
}

// ============================================================
// Poll for processing result
// ============================================================
async function pollResult(recordId) {
    let pollCount = 0;

    const poll = async () => {
        pollCount++;

        try {
            const resp = await fetch(`WORKFLOWURL/status/{WORKFLOW_URL}/status/WORKFLOWU​RL/status/{recordId}`);
            const record = await resp.json();

            if (record.status && record.status !== 'PENDING') {
                // Done processing, show the result
                displayResult(record);
                return;
            }

            if (pollCount < MAX_POLL_COUNT) {
                setTimeout(poll, POLL_INTERVAL);
            } else {
                showMessage(
                    'info',
                    `Processing is taking longer than expected. Record ID: ${recordId}. You can check the result in the history below.`
                );
                resetSubmitButton();
            }
        } catch (err) {
            if (pollCount < MAX_POLL_COUNT) {
                setTimeout(poll, POLL_INTERVAL);
            } else {
                showMessage('error', 'Failed to retrieve processing result.');
                resetSubmitButton();
            }
        }
    };

    // Wait a second before the first poll
    setTimeout(poll, 1000);
}

// ============================================================
// Show processing result
// ============================================================
function displayResult(record) {
    // Hide the form section
    document.getElementById('submit-section').style.display = 'none';

    // Show the result section
    const resultSection = document.getElementById('result-section');
    resultSection.style.display = 'block';

    // Update status badge
    const statusBadge = document.getElementById('result-status');
    statusBadge.textContent = record.status;
    statusBadge.className = `status-badge status-${record.status}`;

    // Fill in result details
    document.getElementById('result-id').textContent = record.id;
    document.getElementById('result-category').textContent = record.category || 'N/A';
    document.getElementById('result-priority').textContent = record.priority || 'N/A';
    document.getElementById('result-note').textContent = record.note || 'No additional notes.';

    // Reset the page for a new submission
    document.getElementById('new-submission-btn').addEventListener('click', () => {
        resultSection.style.display = 'none';
        document.getElementById('submit-section').style.display = 'block';
        document.getElementById('event-form').reset();
        document.getElementById('desc-counter').textContent = '0 / 40 characters minimum';
        document.getElementById('desc-counter').className = '';
        resetSubmitButton();

        // Refresh history after going back
        loadRecords();
    });

    // Refresh history after result comes back
    loadRecords();
}

// ============================================================
// Load submission history with pagination
// ============================================================
async function loadRecords() {
    const listDiv = document.getElementById('records-list');
    listDiv.innerHTML = '<div class="loading">Loading records...</div>';

    try {
        const resp = await fetch(`${WORKFLOW_URL}/records`);
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

// Render one page of records
function renderPage(page) {
    const listDiv = document.getElementById('records-list');
    const start = (page - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
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

// Render pagination controls
function renderPagination() {
    const container = document.getElementById('pagination');
    const totalPages = Math.ceil(allRecords.length / PAGE_SIZE);

    if (totalPages <= 1) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'flex';

    let html = '';

    // Previous page
    html += `<button class="page-btn" onclick="goToPage({currentPage - 1})&quot;{currentPage === 1 ? 'disabled' : ''}>&lt;</button>`;

    // Page buttons
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

function pageBtn(num) {
    return `<button class="page-btn {num === currentPage ? &#39;active&#39; : &#39;&#39;}&quot; onclick=&quot;goToPage({num})">${num}</button>`;
}

function goToPage(num) {
    const totalPages = Math.ceil(allRecords.length / PAGE_SIZE);
    if (num < 1 || num > totalPages) return;
    currentPage = num;
    renderPage(num);
    renderPagination();
}

// ============================================================
// Helpers
// ============================================================
function showMessage(type, text) {
    const div = document.getElementById('submit-message');
    div.className = `message ${type}`;
    div.textContent = text;
    div.style.display = 'block';
}

function resetSubmitButton() {
    const btn = document.getElementById('submit-btn');
    btn.disabled = false;
    btn.textContent = 'Submit Event';
}

function setupRefreshButton() {
    document.getElementById('refresh-btn').addEventListener('click', loadRecords);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================
// Record detail modal
// ============================================================
function openRecordModal(record) {
    const modal = document.getElementById('record-modal');

    // Fill modal fields
    document.getElementById('modal-id').textContent = record.id || 'N/A';
    document.getElementById('modal-title').textContent = record.title || 'N/A';
    document.getElementById('modal-desc').textContent = record.description || 'N/A';
    document.getElementById('modal-location').textContent = record.location || 'N/A';
    document.getElementById('modal-date').textContent = record.event_date || 'N/A';
    document.getElementById('modal-organiser').textContent = record.organiser || 'N/A';
    document.getElementById('modal-category').textContent = record.category || 'N/A';
    document.getElementById('modal-priority').textContent = record.priority || 'N/A';
    document.getElementById('modal-note').textContent = record.note || 'No additional notes.';

    // Update status badge
    const badge = document.getElementById('modal-status');
    badge.textContent = record.status || 'N/A';
    badge.className = `status-badge status-${record.status}`;

    modal.style.display = 'flex';
}

function closeRecordModal() {
    document.getElementById('record-modal').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    // Close on X click
    document.getElementById('modal-close').addEventListener('click', closeRecordModal);

    // Close when clicking outside the modal content
    document.getElementById('record-modal').addEventListener('click', (e) => {
        if (e.target.id === 'record-modal') closeRecordModal();
    });

    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeRecordModal();
    });
});

// ============================================================
// Open modal when a history card is clicked
// ============================================================
function attachRecordClickHandlers() {
    document.querySelectorAll('.record-item').forEach(card => {
        card.addEventListener('click', () => {
            const id = parseInt(card.dataset.id);
            fetchRecordAndShow(id);
        });
    });
}

async function fetchRecordAndShow(id) {
    try {
        const resp = await fetch(`/api/status/${id}`);
        if (!resp.ok) return;
        const record = await resp.json();
        openRecordModal(record);
    } catch (e) {
        console.error('Failed to load record:', e);
    }
}
