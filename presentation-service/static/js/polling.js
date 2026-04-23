/**
 * Campus Buzz - Polling logic for processing results
 */

/**
 * Poll for processing result
 */
async function pollResult(recordId) {
    let pollCount = 0;

    const poll = async () => {
        pollCount++;

        try {
            const resp = await fetch(`
C
O
N
F
I
G
.
W
O
R
K
F
L
O
W
U
R
L
/
s
t
a
t
u
s
/
CONFIG.WORKFLOW 
U
​
 RL/status/{recordId}`);
            const record = await resp.json();

            if (record.status && record.status !== 'PENDING') {
                // Processing complete, show result
                displayResult(record);
                return;
            }

            if (pollCount < CONFIG.MAX_POLL_COUNT) {
                setTimeout(poll, CONFIG.POLL_INTERVAL);
            } else {
                showMessage(
                    'info',
                    `Processing is taking longer than expected. Record ID: ${recordId}. You can check the result in the history below.`
                );
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

    // Delay first poll by 1 second
    setTimeout(poll, 1000);
}

/**
 * Display processing result
 */
function displayResult(record) {
    // Hide form section
    document.getElementById('submit-section').style.display = 'none';

    // Show result section
    const resultSection = document.getElementById('result-section');
    resultSection.style.display = 'block';

    // Update status badge
    const statusBadge = document.getElementById('result-status');
    statusBadge.textContent = record.status;
    statusBadge.className = `status-badge status-${record.status}`;

    // Fill result details
    document.getElementById('result-id').textContent = record.id;
    document.getElementById('result-category').textContent = record.category || 'N/A';
    document.getElementById('result-priority').textContent = record.priority || 'N/A';
    document.getElementById('result-note').textContent = record.note || 'No additional notes.';

    // "New submission" button
    document.getElementById('new-submission-btn').addEventListener('click', () => {
        resultSection.style.display = 'none';
        document.getElementById('submit-section').style.display = 'block';
        document.getElementById('event-form').reset();
        document.getElementById('desc-counter').textContent = '0 / 40 characters minimum';
        document.getElementById('desc-counter').className = '';
        resetSubmitButton();

        // Refresh history list
        loadRecords();
    });

    // Refresh history list
    loadRecords();
}
