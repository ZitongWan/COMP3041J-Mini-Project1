"""
Campus Buzz - Result Update Function (结果更新函数)
===================================================
角色：Serverless 函数 - 用计算结果更新存储的记录
平台：阿里云函数计算 FC 3.0 (HTTP触发器)

职责：
  1. 接收 Processing Function 计算出的结果
  2. 调用 Data Service 更新对应记录的状态、分类、优先级和备注
  3. 返回更新后的完整记录

这是事件驱动流程的终点：
  Processing Function → [HTTP触发] → Result Update Function → [调用] → Data Service
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
logger = logging.getLogger('result-update-function')

# Data Service 地址
DATA_SERVICE_URL = os.environ.get('DATA_SERVICE_URL', 'http://data-service:5002')


# ============================================================
# 核心处理逻辑
# ============================================================

def process_logic(data):
    """
    提取核心处理逻辑，供 handler 和 Flask 路由共同调用
    """
    record_id = data.get('record_id')
    if not record_id:
        return {'statusCode': 400, 'body': json.dumps({'error': '缺少 record_id 参数'})}

    status = data.get('status')
    category = data.get('category', '')
    priority = data.get('priority', '')
    note = data.get('note', '')

    logger.info(f"[更新] 收到结果更新请求: record_id={record_id}, status={status}, "
                 f"category={category}, priority={priority}")

    # ---- 调用 Data Service 更新记录 ----
    try:
        update_resp = requests.put(
            f'{DATA_SERVICE_URL}/api/records/{record_id}',
            json={
                'status': status,
                'category': category,
                'priority': priority,
                'note': note
            },
            timeout=10
        )
        update_resp.raise_for_status()
        updated_record = update_resp.json()
        logger.info(f"[更新] 记录更新成功: record_id={record_id}, new_status={status}")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': '记录更新成功',
                'record_id': record_id,
                'updated_record': updated_record
            })
        }
    except requests.RequestException as e:
        logger.error(f"[更新] 调用 Data Service 失败: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'数据服务不可用: {str(e)}'})
        }


# ============================================================
# 阿里云函数计算 FC 标准 Handler 入口
# ============================================================

def handler(event, context):
    """
    阿里云函数计算 FC 3.0 标准入口
    FC3 HTTP 触发器的 event 参数是 JSON 字符串（str 类型），内容为：
      {"version":"v1","rawPath":"/","body":"{...业务JSON...}","isBase64Encoded":false}
    需要先解析 event 字符串，再从 body 字段提取业务数据（body 本身也是 JSON 字符串）
    """
    try:
        # ---- event 是 JSON 字符串，解析得到 FC3 事件对象 ----
        if isinstance(event, str):
            fc_event = json.loads(event)
        elif isinstance(event, bytes):
            fc_event = json.loads(event.decode('utf-8'))
        else:
            fc_event = event

        logger.info(f"[Handler] fc_event keys={list(fc_event.keys())}")

        # ---- 从 fc_event['body'] 中提取业务数据 ----
        body_str = fc_event.get('body', '')
        if not body_str:
            logger.error("[Handler] body 为空")
            return {'statusCode': 400, 'body': json.dumps({'error': '请求体为空'})}

        # body_str 是 JSON 字符串，再次解析
        data = json.loads(body_str)
        logger.info(f"[Handler] data={data}")

        record_id = data.get('record_id')
        if not record_id:
            logger.error(f"[Handler] 缺少 record_id，data={data}")
            return {'statusCode': 400, 'body': json.dumps({'error': '缺少 record_id 参数'})}

        return process_logic(data)
    except json.JSONDecodeError as e:
        logger.error(f"[Handler] JSON 解析错误: {e}")
        return {'statusCode': 400, 'body': json.dumps({'error': f'无效的 JSON 格式: {e}'})}
    except Exception as e:
        logger.error(f"[Handler] 未预期的错误: {e}", exc_info=True)
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


# ============================================================
# HTTP 触发器入口（保留，用于本地测试）
# ============================================================

@app.route('/', methods=['POST'])
def handle_result_update():
    """更新处理结果 - HTTP 触发器入口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        result = process_logic(data)
        return json.loads(result['body']), result['statusCode']
    except Exception as e:
        logger.error(f"[更新] 未预期的错误: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'healthy', 'function': 'result-update-function'})


# ============================================================
# 启动入口（本地开发/测试用）
# ============================================================
if __name__ == '__main__':
    logger.info("[Result Update Function] 启动中...")
    logger.info(f"[Result Update Function] Data Service URL: {DATA_SERVICE_URL}")
    app.run(host='0.0.0.0', port=9003, debug=True)
