"""
Campus Buzz - Presentation Service
===================================
Role: Handles user input and displays results
Tech stack: Python Flask (page rendering + API proxy)
Port: 5000

Responsibilities:
  1. Serve frontend pages (HTML/CSS/JS)
  2. Proxy API requests to the Workflow Service
  3. Return processed results to the user
"""

import os
import logging
import requests
from flask import Flask, render_template, request, jsonify

# ============================================================
# App setup
# ============================================================
app = Flask(__name__, static_folder='static', template_folder='templates')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger('presentation-service')

# Base URL for the Workflow Service
WORKFLOW_SERVICE_URL = os.environ.get(
    'WORKFLOW_SERVICE_URL',
    'http://workflow-service:5001'
)


# ============================================================
# Page routes
# ============================================================
@app.route('/')
def index():
    """Main page - form + history view"""
    return render_template('index.html')


# ============================================================
# API proxy layer (Frontend → Presentation → Workflow/Data)
# ============================================================

@app.route('/api/submit', methods=['POST'])
def proxy_submit():
    """Forward submission request to Workflow Service"""
    try:
        resp = requests.post(
            f'{WORKFLOW_SERVICE_URL}/api/submit',
            json=request.get_json(),
            timeout=15
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as e:
        logger.error(f"[Proxy] Failed to forward submit request: {e}")
        return jsonify({'error': f'Workflow Service unavailable: {str(e)}'}), 503


@app.route('/api/status/<int:record_id>', methods=['GET'])
def proxy_status(record_id):
    """Forward status check to Workflow Service"""
    try:
        resp = requests.get(
            f'{WORKFLOW_SERVICE_URL}/api/status/{record_id}',
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as e:
        logger.error(f"[Proxy] Failed to forward status request: {e}")
        return jsonify({'error': f'Workflow Service unavailable: {str(e)}'}), 503


@app.route('/api/records', methods=['GET'])
def proxy_records():
    """Fetch records from Data Service"""
    data_service_url = os.environ.get(
        'DATA_SERVICE_URL',
        'http://data-service:5002'
    )

    try:
        resp = requests.get(
            f'{data_service_url}/api/records',
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as e:
        logger.error(f"[Proxy] Failed to fetch records: {e}")
        return jsonify({'error': f'Data Service unavailable: {str(e)}'}), 503


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'presentation-service'})


# ============================================================
# Entry point
# ============================================================
if __name__ == '__main__':
    logger.info("[Presentation Service] Starting up...")
    logger.info(f"[Presentation Service] Workflow Service URL: {WORKFLOW_SERVICE_URL}")

    app.run(host='0.0.0.0', port=5000, debug=True)
