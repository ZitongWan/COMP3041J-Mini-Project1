# Alibaba Cloud FC 3.0 - Result Update Function
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


def parse_fc3_event(event):
    """Parse FC3 HTTP trigger event format"""
    if isinstance(event, str):
        fc_event = json.loads(event) if event.strip() else {}
    elif isinstance(event, bytes):
        fc_event = json.loads(event.decode('utf-8')) if event.strip() else {}
    else:
        fc_event = event or {}
    return fc_event


def update_logic(data):
    """Business logic"""
    headers = {'Content-Type': 'application/json'}
    
    record_id = data.get('record_id')
    status = data.get('status')
    category = data.get('category', '')
    priority = data.get('priority', '')
    note = data.get('note', '')
    
    logger.info(f"[Update] Received request: record_id={record_id}, status={status}")
    
    if not record_id:
        return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'Missing record_id parameter'})}
    
    try:
        # Call Data Service to update record
        update_data = {}
        if status:
            update_data['status'] = status
        if category:
            update_data['category'] = category
        if priority:
            update_data['priority'] = priority
        if note:
            update_data['note'] = note
            
        update_resp = requests.put(
            f'{DATA_SERVICE_URL}/api/records/{record_id}',
            json=update_data,
            timeout=10
        )
        update_resp.raise_for_status()
        updated_record = update_resp.json()
        
        logger.info(f"[Update] Record updated successfully: record_id={record_id}, new_status={status}")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Record updated successfully',
                'record_id': record_id,
                'updated_record': updated_record
            })
        }
        
    except requests.RequestException as e:
        logger.error(f"[Update] Request failed: {e}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': f'Data service unavailable: {str(e)}'})}
    except Exception as e:
        logger.error(f"[Update] Unexpected error: {e}", exc_info=True)
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
            data = fc_event if isinstance(fc_event, dict) else json.loads(str(fc_event))
        
        return update_logic(data)
    except json.JSONDecodeError as e:
        logger.error(f"[Handler] JSON parse error: {e}")
        return {'statusCode': 400, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': f'Invalid JSON: {str(e)}'})}
    except Exception as e:
        logger.error(f"[Handler] Unexpected error: {e}", exc_info=True)
        return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': str(e)})}
