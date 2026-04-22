"""
Campus Buzz - Data Service (数据服务)
=====================================
角色：容器服务 - 存储和检索提交记录
技术栈：Python Flask + SQLite
端口：5002

提供的API端点：
  POST /api/records        - 创建新提交记录
  GET  /api/records         - 获取所有提交记录
  GET  /api/records/<id>    - 获取单条提交记录
  PUT  /api/records/<id>    - 更新提交记录（处理结果回写）
"""

import sqlite3
import json
import os
from datetime import datetime
from flask import Flask, request, jsonify, g

# ============================================================
# 应用初始化
# ============================================================
app = Flask(__name__)

# 数据库文件路径（Docker 容器中挂载到持久卷）
DATABASE = os.environ.get('DATABASE_PATH', '/data/campus_buzz.db')


def get_db():
    """获取数据库连接（每个请求一个连接）"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # 让查询结果可以用列名访问
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """请求结束时关闭数据库连接"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """初始化数据库表结构"""
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
# API 路由
# ============================================================

@app.route('/api/records', methods=['POST'])
def create_record():
    """创建新的提交记录
    
    请求体示例：
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
        return jsonify({'error': '请求体不能为空'}), 400

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

    # 返回创建的记录
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
    """获取所有提交记录"""
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
    """获取单条提交记录"""
    db = get_db()
    record = db.execute('SELECT * FROM submissions WHERE id = ?', (record_id,)).fetchone()

    if record is None:
        return jsonify({'error': '记录不存在'}), 404

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
    """更新提交记录（处理结果回写）
    
    请求体示例：
    {
        "status": "APPROVED",
        "category": "OPPORTUNITY",
        "priority": "HIGH",
        "note": "All checks passed. Category: OPPORTUNITY (keyword: career). Priority: HIGH."
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    db = get_db()
    record = db.execute('SELECT * FROM submissions WHERE id = ?', (record_id,)).fetchone()

    if record is None:
        return jsonify({'error': '记录不存在'}), 404

    now = datetime.utcnow().isoformat()

    # 只更新允许修改的字段
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

    # 返回更新后的记录
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
    """健康检查端点"""
    return jsonify({'status': 'healthy', 'service': 'data-service'})


# ============================================================
# 启动入口
# ============================================================
if __name__ == '__main__':
    # 确保数据目录存在
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    # 初始化数据库
    init_db()
    print("[Data Service] 数据库初始化完成")
    print(f"[Data Service] 数据库路径: {DATABASE}")
    # 启动服务
    app.run(host='0.0.0.0', port=5002, debug=True)
