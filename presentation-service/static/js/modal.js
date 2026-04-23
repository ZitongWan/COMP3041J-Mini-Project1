/**
 * Campus Buzz - 详情弹窗管理
 */

/**
 * 打开详情弹窗
 */
function openRecordModal(record) {
    currentModalRecord = record;  // 保存当前记录
    
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

    document.getElementById('record-modal').style.display = 'flex';
}

/**
 * 关闭详情弹窗
 */
function closeRecordModal() {
    document.getElementById('record-modal').style.display = 'none';
    currentModalRecord = null;  // 清空缓存
}

/**
 * 编辑并重新提交
 */
function editAndResubmit() {
    if (!currentModalRecord) return;
    
    const record = currentModalRecord;
    
    // 关闭弹窗
    closeRecordModal();
    
    // 隐藏结果区域
    document.getElementById('result-section').style.display = 'none';
    
    // 显示表单区域
    const submitSection = document.getElementById('submit-section');
    submitSection.style.display = 'block';
    
    // 填充表单数据
    populateForm(record);
    
    // 重置提交按钮
    resetSubmitButton();
    
    // 滚动到表单顶部
    submitSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // 提示用户
    showMessage('info', 'Form populated with selected record. Modify and submit to create a new version.');
}

/**
 * 点击历史记录卡片 → 打开详情弹窗
 */
function attachRecordClickHandlers() {
    document.querySelectorAll('.record-item').forEach(card => {
        card.addEventListener('click', () => {
            const id = parseInt(card.dataset.id);
            fetchRecordAndShow(id);
        });
    });
}

/**
 * 获取记录并显示弹窗
 */
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

/**
 * 设置弹窗事件监听器
 */
function setupModalEventListeners() {
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
    
    // 编辑并重新提交按钮
    document.getElementById('edit-record-btn').addEventListener('click', editAndResubmit);
}
