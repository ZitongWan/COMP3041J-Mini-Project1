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
import time
import logging
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory

# ============================================================
# 应用初始化
# ============================================================
app = Flask(__name__, static_folder='static', template_folder='templates')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger('presentation-service')

# 服务地址配置（启动时读取）
WORKFLOW_SERVICE_URL = os.environ.get('WORKFLOW_SERVICE_URL', 'http://workflow-service:5001')
DATA_SERVICE_URL = os.environ.get('DATA_SERVICE_URL', 'http://data-service:5002')

# 超时配置（秒）
REQUEST_TIMEOUT_SUBMIT = int(os.environ.get('REQUEST_TIMEOUT_SUBMIT', '15'))
REQUEST_TIMEOUT_QUERY = int(os.environ.get('REQUEST_TIMEOUT_QUERY', '10'))


# ============================================================
# 辅助函数
# ============================================================

def proxy_request(method, url, timeout=10):
    """
    通用代理请求函数
    
    Args:
        method: HTTP 方法 ('GET' 或 'POST')
        url: 目标 URL
        timeout: 超时时间（秒）
    
    Returns:
        tuple: (response_json, status_code)
    """
    start_time = time.time()
    try:
        if method == 'POST':
            # 验证请求体
            if not request.is_json:
                logger.warning(f"[代理] 请求 Content-Type 不是 application/json")
                return {'error': 'Content-Type must be application/json'}, 400
            
            json_data = request.get_json(silent=True)
            if json_data is None:
                logger.warning(f"[代理] 无法解析 JSON 请求体")
                return {'error': 'Invalid JSON body'}, 400
            
            resp = requests.post(url, json=json_data, timeout=timeout)
        else:
            resp = requests.get(url, timeout=timeout)
        
        elapsed = time.time() - start_time
        
        # 尝试解析响应
        try:
            response_data = resp.json()
        except ValueError:
            logger.error(f"[代理] 目标服务返回非 JSON 响应: {resp.status_code}")
            return {'error': 'Internal service error'}, 502
        
        # 记录成功请求
        logger.info(f"[代理] {method} {url} - {resp.status_code} ({elapsed:.2f}s)")
        
        return response_data, resp.status_code
    
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        logger.error(f"[代理] 请求超时: {method} {url} ({elapsed:.2f}s)")
        return {'error': f'Service timeout after {timeout}s'}, 504
    
    except requests.exceptions.ConnectionError as e:
        elapsed = time.time() - start_time
        logger.error(f"[代理] 连接失败: {method} {url} - {str(e)} ({elapsed:.2f}s)")
        return {'error': f'Service unavailable'}, 503
    
    except requests.RequestException as e:
        elapsed = time.time() - start_time
        logger.error(f"[代理] 请求异常: {method} {url} - {str(e)} ({elapsed:.2f}s)")
        return {'error': f'Internal proxy error'}, 500


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
    url = f'{WORKFLOW_SERVICE_URL}/api/submit'
    response_data, status_code = proxy_request('POST', url, REQUEST_TIMEOUT_SUBMIT)
    return jsonify(response_data), status_code


@app.route('/api/status/<int:record_id>', methods=['GET'])
def proxy_status(record_id):
    """代理状态查询到 Workflow Service"""
    url = f'{WORKFLOW_SERVICE_URL}/api/status/{record_id}'
    response_data, status_code = proxy_request('GET', url, REQUEST_TIMEOUT_QUERY)
    return jsonify(response_data), status_code


@app.route('/api/records', methods=['GET'])
def proxy_records():
    """代理记录列表查询到 Data Service"""
    url = f'{DATA_SERVICE_URL}/api/records'
    response_data, status_code = proxy_request('GET', url, REQUEST_TIMEOUT_QUERY)
    return jsonify(response_data), status_code


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'service': 'presentation-service',
        'workflow_service': WORKFLOW_SERVICE_URL,
        'data_service': DATA_SERVICE_URL
    })


# ============================================================
# 启动入口
# ============================================================
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV', 'production') != 'production'
    
    logger.info(f"[Presentation Service] 启动中...")
    logger.info(f"[Presentation Service] 环境: {'development' if debug_mode else 'production'}")
    logger.info(f"[Presentation Service] Workflow Service URL: {WORKFLOW_SERVICE_URL}")
    logger.info(f"[Presentation Service] Data Service URL: {DATA_SERVICE_URL}")
    logger.info(f"[Presentation Service] 监听端口: 5000")
    
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
