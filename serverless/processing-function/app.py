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
    Required fields: title, description, location, event_date, organiser
    Returns: (is_complete, message)
    """
    title = record.get('title', '').strip()
    description = record.get('description', '').strip()
    location = record.get('location', '').strip()
    event_date = record.get('event_date', '').strip()
    organiser = record.get('organiser', '').strip()
    
    # All fields are required
    missing_fields = []
    if not title:
        missing_fields.append('title')
    if not description:
        missing_fields.append('description')
    if not location:
        missing_fields.append('location')
    if not event_date:
        missing_fields.append('event_date')
    if not organiser:
        missing_fields.append('organiser')
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, "All fields complete"


def classify_event(title, description):
    """
    Classify event based on keywords in title and description
    Priority order: OPPORTUNITY > ACADEMIC > SOCIAL > GENERAL
    
    Returns: (category, priority)
    """
    text = f"{title} {description}".lower()
    
    # Check OPPORTUNITY keywords (highest priority)
    if any(keyword in text for keyword in ['career', 'internship', 'recruitment']):
        return 'OPPORTUNITY', 'HIGH'
    
    # Check ACADEMIC keywords
    if any(keyword in text for keyword in ['workshop', 'seminar', 'lecture']):
        return 'ACADEMIC', 'MEDIUM'
    
    # Check SOCIAL keywords
    if any(keyword in text for keyword in ['club', 'society', 'social']):
        return 'SOCIAL', 'NORMAL'
    
    # Default to GENERAL
    return 'GENERAL', 'NORMAL'


def apply_processing_rules(record):
    """
    Apply project rules and calculate result
    Priority order:
    1. Completeness check (all required fields) - INCOMPLETE
    2. Date format validation - NEEDS REVISION
    3. Description length check (min 40 characters) - NEEDS REVISION
    4. Keyword classification & priority assignment - APPROVED
    """
    title = record.get('title', '')
    description = record.get('description', '').strip()
    event_date = record.get('event_date', '').strip()
    
    # Rule 1: Check completeness (highest priority)
    is_complete, completeness_msg = check_record_completeness(record)
    
    if not is_complete:
        return {
            'result': 'INCOMPLETE',
            'status': 'INCOMPLETE',
            'category': '',
            'priority': '',
            'note': f'Incomplete submission: {completeness_msg}.',
            'processed_by': 'processing-function'
        }
    
    # Rule 2: Check date format
    if event_date:
        is_valid_date, date_error = validate_date_format(event_date)
        if not is_valid_date:
            return {
                'result': 'NEEDS REVISION',
                'status': 'NEEDS REVISION',
                'category': '',
                'priority': '',
                'note': f'Date format error: {date_error}',
                'processed_by': 'processing-function'
            }
    
    # Rule 3: Check description length (minimum 40 characters)
    if len(description) < 40:
        return {
            'result': 'NEEDS REVISION',
            'status': 'NEEDS REVISION',
            'category': '',
            'priority': '',
            'note': f'Description too short: {len(description)} characters. Minimum required: 40 characters.',
            'processed_by': 'processing-function'
        }
    
    # Rule 4: Classify event and assign priority
    category, priority = classify_event(title, description)
    
    # All checks passed - APPROVED
    return {
        'result': 'APPROVED',
        'status': 'APPROVED',
        'category': category,
        'priority': priority,
        'note': f'Event classified as {category} with {priority} priority.',
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
