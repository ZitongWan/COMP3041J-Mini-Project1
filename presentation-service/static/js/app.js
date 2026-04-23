/**
 * Campus Buzz - Presentation Service frontend logic
 *
 * Responsibilities:
 *   1. Handle form submission and call the Workflow Service
 *   2. Poll for processing results
 *   3. Display submission history
 */

// ============================================================
// Initial page setup
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    loadRecords();
    setupFormHandler();
    setupDescCounter();
    setupRefreshButton();
    setupModalEventListeners();
});
