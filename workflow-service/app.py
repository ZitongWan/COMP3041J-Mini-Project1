"""
Campus Buzz - Workflow Service (工作流服务)
=========================================
角色：容器服务 - 创建初始提交记录并启动后台处理
技术栈：Python Flask + requests
端口：5001

职责：
  1. 接收 Presentation Service 转发的表单数据
  2. 调用 Data Service 创建初始提交记录（状态: PENDING）
  3. 触发 Submission Event Function 启动后台处理流程

API端点：
  POST /api/submit     - 提交校园活动
  GET  /api/status/<id> - 查询处理状态
"""

import os
import json
import logging
import requests
from flask import Flask, request, jsonify

# ============================================================
# 应用初始化
# ============================================================
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger('workflow-service')

# 从环境变量读取各服务的地址（Docker Compose 中通过服务名解析）
DATA_SERVICE_URL = os.environ.get('DATA_SERVICE_URL', 'http://data-service:5002')
# 阿里云 FC 函数的 HTTP 触发器地址（部署后配置）
SUBMISSION_EVENT_FN_URL = os.environ.get('SUBMISSION_EVENT_FN_URL', 'http://localhost:9001')


# ============================================================
# API 路由
# ============================================================

@app.route('/api/submit', methods=['POST'])
def submit_event():
    """提交校园活动 - 核心工作流入口
    
    处理流程：
      1. 接收表单数据
      2. 调用 Data Service 创建记录（状态: PENDING）
      3. 触发 Submission Event Function 启动后台处理
      4. 返回记录ID和当前状态
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    logger.info(f"[提交] 收到新的校园活动提交: title={data.get('title', 'N/A')}")

    # ---- 步骤1: 调用 Data Service 创建初始记录 ----
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
        logger.info(f"[提交] 记录创建成功, id={record_id}, status=PENDING")
    except requests.RequestException as e:
        logger.error(f"[提交] 调用 Data Service 失败: {e}")
        return jsonify({'error': f'数据服务不可用: {str(e)}'}), 503

    # ---- 步骤2: 触发 Submission Event Function ----
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
        logger.info(f"[提交] Submission Event Function 触发成功, record_id={record_id}")
    except requests.RequestException as e:
        logger.warning(f"[提交] Submission Event Function 触发失败: {e}，记录已保存但处理待重试")
        event_result = {'status': 'trigger_failed', 'error': str(e)}

    # ---- 步骤3: 返回结果 ----
    return jsonify({
        'message': '提交已接收，正在后台处理中',
        'record_id': record_id,
        'status': 'PENDING',
        'event_trigger': event_result
    }), 202


@app.route('/api/status/<int:record_id>', methods=['GET'])
def get_status(record_id):
    """查询提交记录的处理状态"""
    try:
        resp = requests.get(
            f'{DATA_SERVICE_URL}/api/records/{record_id}',
            timeout=10
        )
        if resp.status_code == 404:
            return jsonify({'error': '记录不存在'}), 404
        resp.raise_for_status()
        record = resp.json()
        return jsonify(record)
    except requests.RequestException as e:
        logger.error(f"[查询] 调用 Data Service 失败: {e}")
        return jsonify({'error': f'数据服务不可用: {str(e)}'}), 503


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'healthy', 'service': 'workflow-service'})


# ============================================================
# 启动入口
# ============================================================
if __name__ == '__main__':
    logger.info(f"[Workflow Service] 启动中...")
    logger.info(f"[Workflow Service] Data Service URL: {DATA_SERVICE_URL}")
    logger.info(f"[Workflow Service] Submission Event FN URL: {SUBMISSION_EVENT_FN_URL}")
    app.run(host='0.0.0.0', port=5001, debug=True)
