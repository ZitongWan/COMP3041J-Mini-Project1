"""
Campus Buzz - Processing Function (处理函数)
=============================================
角色：Serverless 函数 - 应用项目规则并计算结果
平台：阿里云函数计算 FC 3.0 (HTTP触发器)
"""

import os, re, json, logging, requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger()

RESULT_UPDATE_FN_URL = os.environ.get('RESULT_UPDATE_FN_URL', 'http://localhost:9003')

CATEGORY_KEYWORDS = [
    {'category': 'OPPORTUNITY', 'priority': 'HIGH', 'keywords': ['career', 'internship', 'recruitment']},
    {'category': 'ACADEMIC', 'priority': 'MEDIUM', 'keywords': ['workshop', 'seminar', 'lecture']},
    {'category': 'SOCIAL', 'priority': 'NORMAL', 'keywords': ['club', 'society', 'social']}
]
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
REQUIRED_FIELDS = ['title', 'description', 'location', 'event_date', 'organiser']


def process_submission(data):
    missing = [f for f in REQUIRED_FIELDS if not data.get(f, '').strip()]
    if missing:
        return {'status': 'INCOMPLETE', 'category': '', 'priority': '',
                 'note': f'Missing required field(s): {", ".join(missing)}.'}

    date_ok = bool(DATE_PATTERN.match(data.get('event_date', '').strip()))
    desc_ok = len(data.get('description', '').strip()) >= 40

    if not date_ok or not desc_ok:
        issues = []
        if not date_ok:
            issues.append('Date format is invalid (must be YYYY-MM-DD)')
        if not desc_ok:
            issues.append(f'Description is too short ({len(data.get("description","").strip())}/40)')
        cat, pri = assign_category(data)
        return {'status': 'NEEDS REVISION', 'category': cat, 'priority': pri,
                'note': f'{"; ".join(issues)}. Category: {cat}. Priority: {pri}.'}

    cat, pri = assign_category(data)
    return {'status': 'APPROVED', 'category': cat, 'priority': pri,
            'note': f'All checks passed. Category: {cat}. Priority: {pri}.'}


def assign_category(data):
    text = (data.get('title', '') + ' ' + data.get('description', '')).lower()
    for c in CATEGORY_KEYWORDS:
        for kw in c['keywords']:
            if kw.lower() in text:
                return c['category'], c['priority']
    return 'GENERAL', 'NORMAL'


def handler(event, context):
    """
    FC3 HTTP 触发器调用此函数
    event 是 JSON 字符串: {"version":"v1","rawPath":"/","body":"{...}","isBase64Encoded":false}
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
            return {'statusCode': 400, 'body': json.dumps({'error': '请求体为空'})}

        # body_str 是 JSON 字符串，再次解析
        data = json.loads(body_str)
        logger.info(f"[Handler] data={data}")

        record_id = data.get('record_id')
        if not record_id:
            return {'statusCode': 400, 'body': json.dumps({'error': '缺少 record_id 参数'})}

        result = process_submission(data)

        # 调用 Result Update Function
        try:
            update_resp = requests.post(RESULT_UPDATE_FN_URL,
                json={'record_id': record_id, 'status': result['status'],
                      'category': result['category'], 'priority': result['priority'],
                      'note': result['note']}, timeout=10)
            update_resp.raise_for_status()
            update_result = update_resp.json()
            return {'statusCode': 200, 'body': json.dumps({
                'record_id': record_id, 'result': result,
                'update_status': 'success', 'updated_record': update_result})}
        except requests.RequestException as e:
            logger.error(f"[Handler] 调用 Result Update 失败: {e}")
            return {'statusCode': 500, 'body': json.dumps({
                'error': f'结果更新失败: {str(e)}', 'computed_result': result})}
    except Exception as e:
        logger.error(f"[Handler] 错误: {e}", exc_info=True)
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
    srv = wsgiref.simple_server.make_server('0.0.0.0', 9002, app)
    srv.serve_forever()
