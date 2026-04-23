/**
 * Campus Buzz - Configuration constants
 */

const CONFIG = {
    WORKFLOW_URL: '/api',      // Routed through the Presentation Service proxy
    POLL_INTERVAL: 2000,       // Polling interval (ms)
    MAX_POLL_COUNT: 30,        // Max polling attempts
    PAGE_SIZE: 5               // Records per page
};

// Global state
let allRecords = [];           // Cached records (used for pagination)
let currentPage = 1;
let currentModalRecord = null; // Currently displayed record in modal
