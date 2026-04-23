/**
 * Campus Buzz - Presentation Service 前端逻辑
 * 
 * 职责：
 *   1. 处理表单提交，调用 Workflow Service
 *   2. 轮询处理结果
 *   3. 展示提交历史
 */

// ============================================================
// 页面加载初始化
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    loadRecords();
    setupFormHandler();
    setupDescCounter();
    setupRefreshButton();
    setupModalEventListeners();
});