"""
Campus Buzz - Submission Event Function (提交事件函数)
=====================================================
角色：Serverless 函数 - 将新提交事件转换为处理请求
平台：阿里云函数计算 FC 3.0 (HTTP触发器)
"""

import os, json, logging, requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger()

DATA_SERVICE_URL = os.environ.get('DATA_SERVICE_URL', 'http://data-service:5002')
PROCESSING_FN_URL = os.environ.get('PROCESSING_FN_URL', 'http://localhost:9001')


def parse_fc3_event(event):
    """
    解析 FC3 HTTP 触发器传入的 event
    event 是 JSON 字符串: {"version":"v1","rawPath":"/","body":"{...}","isBase64Encoded":false}
    """
    if isinstance(event, str):
        fc_event = json.loads(event)
    elif isinstance(event, bytes):
        fc_event = json.loads(event.decode('utf-8'))
    else:
        fc_event = event

    body_str = fc_event.get('body', '')
    if body_str:
        return json.loads(body_str)
    return {}


def process_logic(data):
    record_id = data.get('record_id')
    action = data.get('action', '')
    if not record_id:
        return {'statusCode': 400, 'body': json.dumps({'error': '缺少 record_id 参数'})}

    logger.info(f"[事件] 收到提交事件: record_id={record_id}, action={action}")

    # 从 Data Service 获取完整记录
    try:
        resp = requests.get(f'{DATA_SERVICE_URL}/api/records/{record_id}', timeout=10)
        resp.raise_for_status()
        record = resp.json()
        logger.info(f"[事件] 成功获取记录: title={record.get('title', 'N/A')}")
    except requests.RequestException as e:
        logger.error(f"[事件] 获取记录失败: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': f'无法获取记录: {str(e)}'})}

    # 调用 Processing Function
    try:
        process_resp = requests.post(PROCESSING_FN_URL, json={
            'record_id': record_id,
            'title': record.get('title', ''),
            'description': record.get('description', ''),
            'location': record.get('location', ''),
            'event_date': record.get('event_date', ''),
            'organiser': record.get('organiser', '')
        }, timeout=15)
        process_resp.raise_for_status()
        result = process_resp.json()
        logger.info(f"[事件] Processing Function 执行完成: record_id={record_id}")
        return {'statusCode': 200, 'body': json.dumps({
            'message': '事件处理已触发', 'record_id': record_id, 'processing_result': result})}
    except requests.RequestException as e:
        logger.error(f"[事件] 调用 Processing Function 失败: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': f'处理函数调用失败: {str(e)}'})}


def handler(event, context):
    """FC3 HTTP 触发器入口：event 是 JSON 字符串"""
    try:
        data = parse_fc3_event(event)
        return process_logic(data)
    except Exception as e:
        logger.error(f"[事件] 错误: {e}", exc_info=True)
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


if __name__ == '__main__':
    import wsgiref.simple_server
    def app(environ, start_response):
        path = environ.get('PATH_INFO', '/')
        method = environ.get('REQUEST_METHOD', 'GET')
        logger.info(f"[WSGI] {method} {path}")
        if method == 'GET' and path == '/health':
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps({'status': 'healthy'}).encode()]
        if method == 'POST' and path == '/':
            clen = int(environ.get('CONTENT_LENGTH', 0) or 0)
            body = environ['wsgi.input'].read(clen)
            result = handler(body.decode('utf-8'), None)
            sc = '200 OK' if result['statusCode'] == 200 else f'{result["statusCode"]} Error'
            start_response(sc, [('Content-Type', 'application/json')])
            return [result['body'].encode()]
        start_response('404', [('Content-Type', 'application/json')])
        return [json.dumps({'error': 'not found'}).encode()]
    srv = wsgiref.simple_server.make_server('0.0.0.0', 9001, app)
    srv.serve_forever()
