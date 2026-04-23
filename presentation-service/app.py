"""
Campus Buzz - Presentation Service
===================================
Role: Container-based service for receiving submissions and showing final results
Tech stack: Python Flask (page rendering + API proxy)
Port: 5000

Responsibilities:
  1. Render frontend pages (HTML/CSS/JS)
  2. Proxy API requests to the Workflow Service
  3. Return processing results to the user
"""

import os
import time
import logging
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory

# ============================================================
# App setup
# ============================================================
app = Flask(__name__, static_folder='static', template_folder='templates')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger('presentation-service')

# Service URLs loaded at startup
WORKFLOW_SERVICE_URL = os.environ.get('WORKFLOW_SERVICE_URL', 'http://workflow-service:5001')
DATA_SERVICE_URL = os.environ.get('DATA_SERVICE_URL', 'http://data-service:5002')

# Request timeout settings (seconds)
REQUEST_TIMEOUT_SUBMIT = int(os.environ.get('REQUEST_TIMEOUT_SUBMIT', '15'))
REQUEST_TIMEOUT_QUERY = int(os.environ.get('REQUEST_TIMEOUT_QUERY', '10'))


# ============================================================
# Helper functions
# ============================================================

def proxy_request(method, url, timeout=10):
    """
    Shared proxy request helper

    Args:
        method: HTTP method ('GET' or 'POST')
        url: Target URL
        timeout: Timeout in seconds

    Returns:
        tuple: (response_json, status_code)
    """
    start_time = time.time()
    try:
        if method == 'POST':
            # Validate request body
            if not request.is_json:
                logger.warning("[Proxy] Request Content-Type is not application/json")
                return {'error': 'Content-Type must be application/json'}, 400

            json_data = request.get_json(silent=True)
            if json_data is None:
                logger.warning("[Proxy] Failed to parse JSON request body")
                return {'error': 'Invalid JSON body'}, 400

            resp = requests.post(url, json=json_data, timeout=timeout)
        else:
            resp = requests.get(url, timeout=timeout)

        elapsed = time.time() - start_time

        # Try to parse response as JSON
        try:
            response_data = resp.json()
        except ValueError:
            logger.error(f"[Proxy] Upstream service returned a non-JSON response: {resp.status_code}")
            return {'error': 'Internal service error'}, 502

        # Log successful request
        logger.info(f"[Proxy] {method} {url} - {resp.status_code} ({elapsed:.2f}s)")

        return response_data, resp.status_code

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        logger.error(f"[Proxy] Request timed out: {method} {url} ({elapsed:.2f}s)")
        return {'error': f'Service timeout after {timeout}s'}, 504

    except requests.exceptions.ConnectionError as e:
        elapsed = time.time() - start_time
        logger.error(f"[Proxy] Connection failed: {method} {url} - {str(e)} ({elapsed:.2f}s)")
        return {'error': 'Service unavailable'}, 503

    except requests.RequestException as e:
        elapsed = time.time() - start_time
        logger.error(f"[Proxy] Request failed: {method} {url} - {str(e)} ({elapsed:.2f}s)")
        return {'error': 'Internal proxy error'}, 500


# ============================================================
# Page routes
# ============================================================

@app.route('/')
def index():
    """Main page - shows the submission form and record history"""
    return render_template('index.html')


# ============================================================
# API proxy routes (Frontend -> Presentation -> Workflow -> Data)
# ============================================================

@app.route('/api/submit', methods=['POST'])
def proxy_submit():
    """Forward submission request to the Workflow Service"""
    url = f'{WORKFLOW_SERVICE_URL}/api/submit'
    response_data, status_code = proxy_request('POST', url, REQUEST_TIMEOUT_SUBMIT)
    return jsonify(response_data), status_code


@app.route('/api/status/<int:record_id>', methods=['GET'])
def proxy_status(record_id):
    """Forward status request to the Workflow Service"""
    url = f'{WORKFLOW_SERVICE_URL}/api/status/{record_id}'
    response_data, status_code = proxy_request('GET', url, REQUEST_TIMEOUT_QUERY)
    return jsonify(response_data), status_code


@app.route('/api/records', methods=['GET'])
def proxy_records():
    """Forward record list request to the Data Service"""
    url = f'{DATA_SERVICE_URL}/api/records'
    response_data, status_code = proxy_request('GET', url, REQUEST_TIMEOUT_QUERY)
    return jsonify(response_data), status_code


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'presentation-service',
        'workflow_service': WORKFLOW_SERVICE_URL,
        'data_service': DATA_SERVICE_URL
    })


# ============================================================
# Entry point
# ============================================================
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV', 'production') != 'production'

    logger.info("[Presentation Service] Starting up...")
    logger.info(f"[Presentation Service] Environment: {'development' if debug_mode else 'production'}")
    logger.info(f"[Presentation Service] Workflow Service URL: {WORKFLOW_SERVICE_URL}")
    logger.info(f"[Presentation Service] Data Service URL: {DATA_SERVICE_URL}")
    logger.info("[Presentation Service] Listening on port: 5000")

    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
