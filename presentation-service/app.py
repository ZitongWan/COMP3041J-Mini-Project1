"""
Campus Buzz - Presentation Service (展示服务)
=============================================
角色：容器服务 - 接收用户提交并展示最终结果
技术栈：Python Flask（提供页面渲染 + API反向代理）
端口：5000

职责：
  1. 渲染前端页面（HTML/CSS/JS）
  2. 反向代理 API 请求到 Workflow Service
  3. 展示处理结果给用户
"""

import os
import logging
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory

# ============================================================
# 应用初始化
# ============================================================
app = Flask(__name__, static_folder='static', template_folder='templates')
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger('presentation-service')

# Workflow Service 地址
WORKFLOW_SERVICE_URL = os.environ.get('WORKFLOW_SERVICE_URL', 'http://workflow-service:5001')


# ============================================================
# 页面路由
# ============================================================

@app.route('/')
def index():
    """首页 - 展示提交表单和历史记录"""
    return render_template('index.html')


# ============================================================
# API 反向代理（前端 → Presentation → Workflow → Data）
# ============================================================

@app.route('/api/submit', methods=['POST'])
def proxy_submit():
    """代理提交请求到 Workflow Service"""
    try:
        resp = requests.post(
            f'{WORKFLOW_SERVICE_URL}/api/submit',
            json=request.get_json(),
            timeout=15
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as e:
        logger.error(f"[代理] 提交请求转发失败: {e}")
        return jsonify({'error': f'Workflow Service 不可用: {str(e)}'}), 503


@app.route('/api/status/<int:record_id>', methods=['GET'])
def proxy_status(record_id):
    """代理状态查询到 Workflow Service"""
    try:
        resp = requests.get(
            f'{WORKFLOW_SERVICE_URL}/api/status/{record_id}',
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as e:
        logger.error(f"[代理] 状态查询转发失败: {e}")
        return jsonify({'error': f'Workflow Service 不可用: {str(e)}'}), 503


@app.route('/api/records', methods=['GET'])
def proxy_records():
    """代理记录列表查询到 Data Service"""
    data_service_url = os.environ.get('DATA_SERVICE_URL', 'http://data-service:5002')
    try:
        resp = requests.get(
            f'{data_service_url}/api/records',
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as e:
        logger.error(f"[代理] 记录查询转发失败: {e}")
        return jsonify({'error': f'Data Service 不可用: {str(e)}'}), 503


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'healthy', 'service': 'presentation-service'})


# ============================================================
# 启动入口
# ============================================================
if __name__ == '__main__':
    logger.info(f"[Presentation Service] 启动中...")
    logger.info(f"[Presentation Service] Workflow Service URL: {WORKFLOW_SERVICE_URL}")
    app.run(host='0.0.0.0', port=5000, debug=True)
