/**
 * Campus Buzz - 表单处理逻辑
 */

/**
 * 设置表单提交处理器
 */
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
            const resp = await fetch(`${CONFIG.WORKFLOW_URL}/submit`, {
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

/**
 * 设置描述字符计数器
 */
function setupDescCounter() {
    const desc = document.getElementById('description');
    const counter = document.getElementById('desc-counter');

    desc.addEventListener('input', () => {
        const len = desc.value.trim().length;
        counter.textContent = `${len} / 40 characters minimum`;
        counter.className = len >= 40 ? 'valid' : '';
    });
}

/**
 * 填充表单数据
 */
function populateForm(record) {
    document.getElementById('title').value = record.title || '';
    document.getElementById('description').value = record.description || '';
    document.getElementById('location').value = record.location || '';
    document.getElementById('event_date').value = record.event_date || '';
    document.getElementById('organiser').value = record.organiser || '';

    // 更新字符计数器
    const desc = document.getElementById('description');
    const counter = document.getElementById('desc-counter');
    const len = desc.value.trim().length;
    counter.textContent = `${len} / 40 characters minimum`;
    counter.className = len >= 40 ? 'valid' : '';
}
