/**
 * Campus Buzz - Detail modal management
 */

/**
 * Open the detail modal
 */
function openRecordModal(record) {
    currentModalRecord = record;  // Keep track of the current record

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

    document.getElementById('record-modal').style.display = 'flex';
}

/**
 * Close the detail modal
 */
function closeRecordModal() {
    document.getElementById('record-modal').style.display = 'none';
    currentModalRecord = null;  // Clear cached record
}

/**
 * Edit and resubmit
 */
function editAndResubmit() {
    if (!currentModalRecord) return;

    const record = currentModalRecord;

    // Close modal
    closeRecordModal();

    // Hide result section
    document.getElementById('result-section').style.display = 'none';

    // Show form section
    const submitSection = document.getElementById('submit-section');
    submitSection.style.display = 'block';

    // Fill form with existing data
    populateForm(record);

    // Reset submit button
    resetSubmitButton();

    // Scroll back to form
    submitSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Let user know what's happening
    showMessage('info', 'Form populated with selected record. Modify and submit to create a new version.');
}

/**
 * Open modal when a history card is clicked
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
 * Fetch record details and open modal
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
 * Set up modal event listeners
 */
function setupModalEventListeners() {
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

    // Edit and resubmit button
    document.getElementById('edit-record-btn').addEventListener('click', editAndResubmit);
}
