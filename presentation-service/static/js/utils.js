/**
 * Campus Buzz - 工具函数
 */

/**
 * 显示消息提示
 */
function showMessage(type, text) {
    const div = document.getElementById('submit-message');
    div.className = `message ${type}`;
    div.textContent = text;
    div.style.display = 'block';
}

/**
 * 重置提交按钮
 */
function resetSubmitButton() {
    const btn = document.getElementById('submit-btn');
    btn.disabled = false;
    btn.textContent = 'Submit Event';
}

/**
 * HTML 转义，防止 XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
