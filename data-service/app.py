"""
Campus Buzz - Data Service
==========================
Role: Backend service for storing and retrieving submissions
Tech stack: Python Flask + SQLite
Port: 5002

Available API endpoints:
  POST /api/records        - Create a new submission record
  GET  /api/records        - Get all submission records
  GET  /api/records/<id>   - Get a single submission record
  PUT  /api/records/<id>   - Update a submission record (for processing results)
"""

import sqlite3
import json
import os
from datetime import datetime
from flask import Flask, request, jsonify, g

# ============================================================
# App initialization
# ============================================================
app = Flask(__name__)

# Database file path (mounted to persistent volume in Docker)
DATABASE = os.environ.get('DATABASE_PATH', '/data/campus_buzz.db')


def get_db():
    """Get database connection (one per request)"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # Allow accessing columns by name
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Close database connection when request ends"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database tables if they don't exist"""
    db = sqlite3.connect(DATABASE)
    db.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            location TEXT,
            event_date TEXT,
            organiser TEXT,
            status TEXT DEFAULT 'PENDING',
            category TEXT DEFAULT '',
            priority TEXT DEFAULT '',
            note TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    db.commit()
    db.close()


# ============================================================
# API Routes
# ============================================================

@app.route('/api/records', methods=['POST'])
def create_record():
    """Create a new submission record
    
    Example request body:
    {
        "title": "Career Fair 2026",
        "description": "Annual career fair with top companies...",
        "location": "Main Hall",
        "event_date": "2026-05-01",
        "organiser": "Career Center"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body cannot be empty'}), 400

    now = datetime.utcnow().isoformat()
    db = get_db()

    cursor = db.execute('''
        INSERT INTO submissions (title, description, location, event_date, organiser, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?)
    ''', (
        data.get('title', ''),
        data.get('description', ''),
        data.get('location', ''),
        data.get('event_date', ''),
        data.get('organiser', ''),
        now,
        now
    ))

    db.commit()

    # Return the created record
    record_id = cursor.lastrowid
    record = db.execute('SELECT * FROM submissions WHERE id = ?', (record_id,)).fetchone()

    return jsonify({
        'id': record['id'],
        'title': record['title'],
        'description': record['description'],
        'location': record['location'],
        'event_date': record['event_date'],
        'organiser': record['organiser'],
        'status': record['status'],
        'category': record['category'],
        'priority': record['priority'],
        'note': record['note'],
        'created_at': record['created_at'],
        'updated_at': record['updated_at']
    }), 201


@app.route('/api/records', methods=['GET'])
def get_records():
    """Get all submission records"""
    db = get_db()
    records = db.execute('SELECT * FROM submissions ORDER BY created_at DESC').fetchall()

    result = []
    for r in records:
        result.append({
            'id': r['id'],
            'title': r['title'],
            'description': r['description'],
            'location': r['location'],
            'event_date': r['event_date'],
            'organiser': r['organiser'],
            'status': r['status'],
            'category': r['category'],
            'priority': r['priority'],
            'note': r['note'],
            'created_at': r['created_at'],
            'updated_at': r['updated_at']
        })

    return jsonify(result)


@app.route('/api/records/<int:record_id>', methods=['GET'])
def get_record(record_id):
    """Get a single submission record by ID"""
    db = get_db()
    record = db.execute('SELECT * FROM submissions WHERE id = ?', (record_id,)).fetchone()

    if record is None:
        return jsonify({'error': 'Record not found'}), 404

    return jsonify({
        'id': record['id'],
        'title': record['title'],
        'description': record['description'],
        'location': record['location'],
        'event_date': record['event_date'],
        'organiser': record['organiser'],
        'status': record['status'],
        'category': record['category'],
        'priority': record['priority'],
        'note': record['note'],
        'created_at': record['created_at'],
        'updated_at': record['updated_at']
    })


@app.route('/api/records/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    """Update a submission record (for processing result writeback)
    
    Example request body:
    {
        "status": "APPROVED",
        "category": "OPPORTUNITY",
        "priority": "HIGH",
        "note": "All checks passed. Category: OPPORTUNITY (keyword: career). Priority: HIGH."
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body cannot be empty'}), 400

    db = get_db()
    record = db.execute('SELECT * FROM submissions WHERE id = ?', (record_id,)).fetchone()

    if record is None:
        return jsonify({'error': 'Record not found'}), 404

    now = datetime.utcnow().isoformat()

    # Only update the fields that are allowed to change
    status = data.get('status', record['status'])
    category = data.get('category', record['category'])
    priority = data.get('priority', record['priority'])
    note = data.get('note', record['note'])

    db.execute('''
        UPDATE submissions 
        SET status = ?, category = ?, priority = ?, note = ?, updated_at = ?
        WHERE id = ?
    ''', (status, category, priority, note, now, record_id))

    db.commit()

    # Return the updated record
    updated = db.execute('SELECT * FROM submissions WHERE id = ?', (record_id,)).fetchone()
    return jsonify({
        'id': updated['id'],
        'title': updated['title'],
        'description': updated['description'],
        'location': updated['location'],
        'event_date': updated['event_date'],
        'organiser': updated['organiser'],
        'status': updated['status'],
        'category': updated['category'],
        'priority': updated['priority'],
        'note': updated['note'],
        'created_at': updated['created_at'],
        'updated_at': updated['updated_at']
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'data-service'})


# ============================================================
# Startup
# ============================================================
if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    # Initialize database schema
    init_db()
    print("[Data Service] Database initialized")
    print(f"[Data Service] Database path: {DATABASE}")
    # Start the Flask server
    app.run(host='0.0.0.0', port=5002, debug=True)
