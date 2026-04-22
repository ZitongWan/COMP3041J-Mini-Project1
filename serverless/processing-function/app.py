# Alibaba Cloud FC 3.0 - Processing Function
# Pure Python implementation

import json
import logging
import os
import re
import requests
import random
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger()

# Environment variables
RESULT_UPDATE_FN_URL = os.environ.get('RESULT_UPDATE_FN_URL', 'http://localhost:5004')


def parse_fc3_event(event):
    """Parse FC3 HTTP trigger event format"""
    if isinstance(event, str):
        fc_event = json.loads(event) if event.strip() else {}
    elif isinstance(event, bytes):
        fc_event = json.loads(event.decode('utf-8')) if event.strip() else {}
    else:
        fc_event = event or {}
    return fc_event


def validate_date_format(date_str):
    """
    Validate date format - must be YYYY-MM-DD
    Returns: (is_valid, error_message)
    """
    if not date_str:
        return True, None  # Empty date is allowed (completeness check handles this)
    
    # Check format YYYY-MM-DD using regex
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False, f"Invalid date format: '{date_str}'. Expected format: YYYY-MM-DD"
    
    # Check if it's a valid date
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True, None
    except ValueError:
        return False, f"Invalid date: '{date_str}' is not a valid calendar date"


def check_record_completeness(record):
    """
    Check if the record is complete
    Required fields: title
    Optional fields: description, location, event_date, organiser
    """
    title = record.get('title', '').strip()
    description = record.get('description', '').strip()
    location = record.get('location', '').strip()
    event_date = record.get('event_date', '').strip()
    organiser = record.get('organiser', '').strip()
    
    # Title is required
    if not title:
        return False, "Title is required"
    
    # Check if all fields are filled
    all_filled = bool(description and location and event_date and organiser)
    return all_filled, "Complete" if all_filled else "Missing optional fields"


def apply_processing_rules(record):
    """
    Apply project rules and calculate result
    """
    title = record.get('title', '')
    description = record.get('description', '')
    category = record.get('category', '')
    priority = record.get('priority', '')
    event_date = record.get('event_date', '').strip()
    
    # Check completeness first
    is_complete, completeness_msg = check_record_completeness(record)
    
    if not is_complete:
        # Return INCOMPLETE status
        return {
            'result': 'INCOMPLETE',
            'status': 'INCOMPLETE',
            'category': '',
            'priority': 'LOW',
            'note': f'Incomplete submission: {completeness_msg}. Please provide all required information.',
            'processed_by': 'processing-function'
        }
    
    # Check date format if date is provided
    if event_date:
        is_valid_date, date_error = validate_date_format(event_date)
        if not is_valid_date:
            return {
                'result': 'NEEDS REVISION',
                'status': 'NEEDS REVISION',
                'category': '',
                'priority': 'NORMAL',
                'note': f'Date format error: {date_error}',
                'processed_by': 'processing-function'
            }
    
    # Calculate score
    score = random.randint(60, 100)
    
    # Apply business rules based on title keywords
    if 'exam' in title.lower() or 'test' in title.lower():
        result = 'APPROVED'
        note = 'Academic event - approved'
        category = 'Academic'
    elif 'party' in title.lower() or 'social' in title.lower():
        result = 'APPROVED'
        note = 'Social event - approved'
        category = 'Social'
    elif 'career' in title.lower() or 'job' in title.lower():
        result = 'APPROVED'
        note = 'Career opportunity - approved'
        category = 'Opportunity'
    else:
        result = 'APPROVED'
        note = 'Event approved after review'
        category = category or 'General'
    
    return {
        'result': result,
        'status': result,
        'category': category,
        'priority': priority or 'NORMAL',
        'note': note,
        'score': score,
        'processed_by': 'processing-function'
    }


def process_logic(data):
    """Business logic"""
    headers = {'Content-Type': 'application/json'}
    
    record_id = data.get('record_id')
    record = data.get('record', {})
    action = data.get('action', 'process_submission')
    
    logger.info(f"[Processing] Received request: record_id={record_id}, action={action}")
    
    if not record_id:
        return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'Missing record_id parameter'})}
    
    try:
        # Apply processing rules
        processing_result = apply_processing_rules(record)
        logger.info(f"[Processing] Rules applied: record_id={record_id}, result={processing_result['result']}")
        
        # Call Result Update Function to update the result
        update_resp = requests.post(
            RESULT_UPDATE_FN_URL,
            json={
                'record_id': record_id,
                'status': processing_result['status'],
                'category': processing_result['category'],
                'priority': processing_result['priority'],
                'note': processing_result['note']
            },
            timeout=20,
            headers={'Content-Type': 'application/json'}
        )
        
        if update_resp.status_code == 200:
            logger.info(f"[Processing] Result update successful: record_id={record_id}")
        else:
            logger.warning(f"[Processing] Result update failed: record_id={record_id}, status={update_resp.status_code}")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Processing complete',
                'record_id': record_id,
                'processing_result': processing_result
            })
        }
        
    except requests.RequestException as e:
        logger.error(f"[Processing] Request failed: {e}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': f'Request failed: {str(e)}'})}
    except Exception as e:
        logger.error(f"[Processing] Unexpected error: {e}", exc_info=True)
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
        
        return process_logic(data)
    except json.JSONDecodeError as e:
        logger.error(f"[Handler] JSON parse error: {e}")
        return {'statusCode': 400, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': f'Invalid JSON: {str(e)}'})}
    except Exception as e:
        logger.error(f"[Handler] Unexpected error: {e}", exc_info=True)
        return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': str(e)})}
