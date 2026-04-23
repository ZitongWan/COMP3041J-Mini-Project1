/**
 * Campus Buzz - 轮询处理结果
 */

/**
 * 轮询处理结果
 */
async function pollResult(recordId) {
    let pollCount = 0;
    
    const poll = async () => {
        pollCount++;
        
        try {
            const resp = await fetch(`${CONFIG.WORKFLOW_URL}/status/${recordId}`);
            const record = await resp.json();
            
            if (record.status && record.status !== 'PENDING') {
                // 处理完成，显示结果
                displayResult(record);
                return;
            }
            
            if (pollCount < CONFIG.MAX_POLL_COUNT) {
                setTimeout(poll, CONFIG.POLL_INTERVAL);
            } else {
                showMessage('info', `Processing is taking longer than expected. Record ID: ${recordId}. You can check the result in the history below.`);
                resetSubmitButton();
            }
        } catch (err) {
            if (pollCount < CONFIG.MAX_POLL_COUNT) {
                setTimeout(poll, CONFIG.POLL_INTERVAL);
            } else {
                showMessage('error', 'Failed to retrieve processing result.');
                resetSubmitButton();
            }
        }
    };
    
    // 首次轮询延迟1秒
    setTimeout(poll, 1000);
}

/**
 * 显示处理结果
 */
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
