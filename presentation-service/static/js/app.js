/**
 * Campus Buzz - Presentation Service 前端逻辑
 * 
 * 职责：
 *   1. 处理表单提交，调用 Workflow Service
 *   2. 轮询处理结果
 *   3. 展示提交历史
 */

// ============================================================
// 配置
// ============================================================
const WORKFLOW_URL = '/api';  // 通过 Presentation Service 反向代理
const POLL_INTERVAL = 2000;   // 轮询间隔（毫秒）
const MAX_POLL_COUNT = 30;    // 最大轮询次数
const PAGE_SIZE = 5;          // 每页显示记录数

let allRecords = [];          // 缓存所有记录（用于分页）
let currentPage = 1;

// ============================================================
// 页面加载初始化
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    loadRecords();
    setupFormHandler();
    setupDescCounter();
    setupRefreshButton();
});

// ============================================================
// 表单提交处理
// ============================================================
function setupFormHandler() {
    const form = document.getElementById('event-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = document.getElementById('submit-btn');
        const messageDiv = document.getElementById('submit-message');
        
        // 收集表单数据
        const formData = {
            title: document.getElementById('title').value.trim(),
            description: document.getElementById('description').value.trim(),
            location: document.getElementById('location').value.trim(),
            event_date: document.getElementById('event_date').value.trim(),
            organiser: document.getElementById('organiser').value.trim()
        };
        
        // 禁用提交按钮
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
        messageDiv.style.display = 'none';
        
        try {
            // 调用 Workflow Service 提交
            const resp = await fetch(`${WORKFLOW_URL}/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            const result = await resp.json();
            
            if (resp.ok) {
                showMessage('info', `Submission received! Record ID: ${result.record_id}. Processing in background...`);
                
                // 开始轮询处理结果
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
// 描述字符计数器
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
// 轮询处理结果
// ============================================================
async function pollResult(recordId) {
    let pollCount = 0;
    
    const poll = async () => {
        pollCount++;
        
        try {
            const resp = await fetch(`${WORKFLOW_URL}/status/${recordId}`);
            const record = await resp.json();
            
            if (record.status && record.status !== 'PENDING') {
                // 处理完成，显示结果
                displayResult(record);
                return;
            }
            
            if (pollCount < MAX_POLL_COUNT) {
                setTimeout(poll, POLL_INTERVAL);
            } else {
                showMessage('info', `Processing is taking longer than expected. Record ID: ${recordId}. You can check the result in the history below.`);
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
    
    // 首次轮询延迟1秒
    setTimeout(poll, 1000);
}

// ============================================================
// 显示处理结果
// ============================================================
function displayResult(record) {
    // 隐藏表单区域
    document.getElementById('submit-section').style.display = 'none';
    
    // 显示结果区域
    const resultSection = document.getElementById('result-section');
    resultSection.style.display = 'block';
    
    // 设置状态徽章
    const statusBadge = document.getElementById('result-status');
    statusBadge.textContent = record.status;
    statusBadge.className = `status-badge status-${record.status}`;
    
    // 填充详情
    document.getElementById('result-id').textContent = record.id;
    document.getElementById('result-category').textContent = record.category || 'N/A';
    document.getElementById('result-priority').textContent = record.priority || 'N/A';
    document.getElementById('result-note').textContent = record.note || 'No additional notes.';
    
    // "新提交"按钮
    document.getElementById('new-submission-btn').addEventListener('click', () => {
        resultSection.style.display = 'none';
        document.getElementById('submit-section').style.display = 'block';
        document.getElementById('event-form').reset();
        document.getElementById('desc-counter').textContent = '0 / 40 characters minimum';
        document.getElementById('desc-counter').className = '';
        resetSubmitButton();
        // 刷新历史记录
        loadRecords();
    });
    
    // 刷新历史记录
    loadRecords();
}

// ============================================================
// 加载历史记录（带分页）
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

// 渲染当前页
function renderPage(page) {
    const listDiv = document.getElementById('records-list');
    const start = (page - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
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

// 渲染分页导航
function renderPagination() {
    const container = document.getElementById('pagination');
    const totalPages = Math.ceil(allRecords.length / PAGE_SIZE);

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

function pageBtn(num) {
    return `<button class="page-btn ${num === currentPage ? 'active' : ''}" onclick="goToPage(${num})">${num}</button>`;
}

function goToPage(num) {
    const totalPages = Math.ceil(allRecords.length / PAGE_SIZE);
    if (num < 1 || num > totalPages) return;
    currentPage = num;
    renderPage(num);
    renderPagination();
}

// ============================================================
// 工具函数
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
// 详情弹窗
// ============================================================
function openRecordModal(record) {
    const modal = document.getElementById('record-modal');

    // 填充字段
    document.getElementById('modal-id').textContent = record.id || 'N/A';
    document.getElementById('modal-title').textContent = record.title || 'N/A';
    document.getElementById('modal-desc').textContent = record.description || 'N/A';
    document.getElementById('modal-location').textContent = record.location || 'N/A';
    document.getElementById('modal-date').textContent = record.event_date || 'N/A';
    document.getElementById('modal-organiser').textContent = record.organiser || 'N/A';
    document.getElementById('modal-category').textContent = record.category || 'N/A';
    document.getElementById('modal-priority').textContent = record.priority || 'N/A';
    document.getElementById('modal-note').textContent = record.note || 'No additional notes.';

    // 状态徽章
    const badge = document.getElementById('modal-status');
    badge.textContent = record.status || 'N/A';
    badge.className = `status-badge status-${record.status}`;

    modal.style.display = 'flex';
}

function closeRecordModal() {
    document.getElementById('record-modal').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    // 点击 X 关闭
    document.getElementById('modal-close').addEventListener('click', closeRecordModal);
    // 点击遮罩关闭
    document.getElementById('record-modal').addEventListener('click', (e) => {
        if (e.target.id === 'record-modal') closeRecordModal();
    });
    // ESC 键关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeRecordModal();
    });
});

// ============================================================
// 点击历史记录卡片 → 打开详情弹窗
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
