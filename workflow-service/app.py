"""
Campus Buzz - Workflow Service
================================
Role: Creates submission records and triggers background processing
Tech stack: Python Flask + requests
Port: 5001

Responsibilities:
  1. Accept form data forwarded from the Presentation Service
  2. Create an initial record in the Data Service (status: PENDING)
  3. Trigger the Submission Event Function to start processing

API endpoints:
  POST /api/submit       - Submit a campus event
  GET  /api/status/<id>  - Check processing status
"""

import os
import json
import logging
import requests
from flask import Flask, request, jsonify

# ============================================================
# App setup
# ============================================================
app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger('workflow-service')

# Service URLs (resolved via Docker networking)
DATA_SERVICE_URL = os.environ.get(
    'DATA_SERVICE_URL',
    'http://data-service:5002'
)

# HTTP trigger URL for the FC Submission Event Function
SUBMISSION_EVENT_FN_URL = os.environ.get(
    'SUBMISSION_EVENT_FN_URL',
    'http://localhost:9001'
)


# ============================================================
# API routes
# ============================================================

@app.route('/api/submit', methods=['POST'])
def submit_event():
    """Main workflow entry point

    Flow:
      1. Receive form data
      2. Create a record in Data Service (PENDING)
      3. Trigger Submission Event Function
      4. Return record ID and current status
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body cannot be empty'}), 400

    logger.info(f"[Submit] New event received: title={data.get('title', 'N/A')}")

    # ---- Step 1: Create record in Data Service ----
    try:
        create_resp = requests.post(
            f'{DATA_SERVICE_URL}/api/records',
            json={
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'location': data.get('location', ''),
                'event_date': data.get('event_date', ''),
                'organiser': data.get('organiser', '')
            },
            timeout=10
        )
        create_resp.raise_for_status()
        record = create_resp.json()
        record_id = record['id']
        logger.info(f"[Submit] Record created successfully, id={record_id}, status=PENDING")
    except requests.RequestException as e:
        logger.error(f"[Submit] Failed to call Data Service: {e}")
        return jsonify({'error': f'Data Service unavailable: {str(e)}'}), 503

    # ---- Step 2: Trigger Submission Event Function ----
    try:
        event_resp = requests.post(
            SUBMISSION_EVENT_FN_URL,
            json={
                'record_id': record_id,
                'action': 'process_submission'
            },
            timeout=10
        )
        event_resp.raise_for_status()
        event_result = event_resp.json()
        logger.info(f"[Submit] Submission Event Function triggered, record_id={record_id}")
    except requests.RequestException as e:
        logger.warning(
            f"[Submit] Failed to trigger Submission Event Function: {e}. "
            f"Record is saved but processing may need retry."
        )
        event_result = {'status': 'trigger_failed', 'error': str(e)}

    # ---- Step 3: Return response ----
    return jsonify({
        'message': 'Submission received. Processing in background.',
        'record_id': record_id,
        'status': 'PENDING',
        'event_trigger': event_result
    }), 202


@app.route('/api/status/<int:record_id>', methods=['GET'])
def get_status(record_id):
    """Fetch processing status for a record"""
    try:
        resp = requests.get(
            f'{DATA_SERVICE_URL}/api/records/{record_id}',
            timeout=10
        )
        if resp.status_code == 404:
            return jsonify({'error': 'Record not found'}), 404

        resp.raise_for_status()
        record = resp.json()
        return jsonify(record)

    except requests.RequestException as e:
        logger.error(f"[Status] Failed to call Data Service: {e}")
        return jsonify({'error': f'Data Service unavailable: {str(e)}'}), 503


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check"""
    return jsonify({'status': 'healthy', 'service': 'workflow-service'})


# ============================================================
# Entry point
# ============================================================
if __name__ == '__main__':
    logger.info("[Workflow Service] Starting up...")
    logger.info(f"[Workflow Service] Data Service URL: {DATA_SERVICE_URL}")
    logger.info(f"[Workflow Service] Submission Event FN URL: {SUBMISSION_EVENT_FN_URL}")

    app.run(host='0.0.0.0', port=5001, debug=True)
