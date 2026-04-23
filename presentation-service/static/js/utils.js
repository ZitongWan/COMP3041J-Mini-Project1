/**
 * Campus Buzz - Utility functions
 */

/**
 * Show a message to the user
 */
function showMessage(type, text) {
    const div = document.getElementById('submit-message');
    div.className = `message ${type}`;
    div.textContent = text;
    div.style.display = 'block';
}

/**
 * Reset submit button to default state
 */
function resetSubmitButton() {
    const btn = document.getElementById('submit-btn');
    btn.disabled = false;
    btn.textContent = 'Submit Event';
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
