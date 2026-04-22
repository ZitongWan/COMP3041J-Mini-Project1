# Alibaba Cloud FC 3.0 - Submission Event Function
# Pure Python implementation

import json
import logging
import os
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger()

# Environment variables
DATA_SERVICE_URL = os.environ.get('DATA_SERVICE_URL', 'http://localhost:5002')
PROCESSING_FN_URL = os.environ.get('PROCESSING_FN_URL', 'http://localhost:5003')


def parse_fc3_event(event):
    """
    Parse FC3 HTTP trigger event format
    FC3 event may be str or bytes type
    """
    if isinstance(event, str):
        fc_event = json.loads(event) if event.strip() else {}
    elif isinstance(event, bytes):
        fc_event = json.loads(event.decode('utf-8')) if event.strip() else {}
    else:
        fc_event = event or {}
    return fc_event


def process_logic(data):
    """Business logic"""
    headers = {'Content-Type': 'application/json'}
    
    record_id = data.get('record_id')
    action = data.get('action', 'process_submission')
    
    logger.info(f"[Event] Received request: record_id={record_id}, action={action}")
    
    if not record_id:
        return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'Missing record_id parameter'})}
    
    try:
        # 1. Get record details from Data Service
        record_resp = requests.get(f'{DATA_SERVICE_URL}/api/records/{record_id}', timeout=10)
        record_resp.raise_for_status()
        record = record_resp.json()
        logger.info(f"[Event] Record retrieved successfully: record_id={record_id}")
        
        # 2. Call Processing Function to process
        process_resp = requests.post(
            PROCESSING_FN_URL,
            json={
                'record_id': record_id,
                'action': action,
                'record': record
            },
            timeout=25,
            headers={'Content-Type': 'application/json'}
        )
        process_result = process_resp.json() if process_resp.text else {}
        
        if process_resp.status_code != 200:
            logger.warning(f"[Event] Processing Function returned non-200: {process_resp.status_code}")
        
        logger.info(f"[Event] Processing Function executed: record_id={record_id}")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Event processing triggered',
                'record_id': record_id,
                'processing_result': process_result
            })
        }
        
    except requests.RequestException as e:
        logger.error(f"[Event] Request failed: {e}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': f'Request failed: {str(e)}'})}
    except Exception as e:
        logger.error(f"[Event] Unexpected error: {e}", exc_info=True)
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}


def handler(event, context):
    """
    Alibaba Cloud FC 3.0 Standard Entry Point
    """
    try:
        fc_event = parse_fc3_event(event)
        body_str = fc_event.get('body', '')
        
        if body_str:
            data = json.loads(body_str)
        else:
            # Try to parse event directly (sync invocation may pass business data directly)
            data = fc_event if isinstance(fc_event, dict) else json.loads(str(fc_event))
        
        return process_logic(data)
    except json.JSONDecodeError as e:
        logger.error(f"[Handler] JSON parse error: {e}")
        return {'statusCode': 400, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': f'Invalid JSON: {str(e)}'})}
    except Exception as e:
        logger.error(f"[Handler] Unexpected error: {e}", exc_info=True)
        return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': str(e)})}
