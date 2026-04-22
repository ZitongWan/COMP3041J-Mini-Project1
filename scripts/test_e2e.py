"""
Campus Buzz - 端到端测试脚本
============================
测试完整的混合云工作流：
  用户提交 → Workflow → FC事件函数 → FC处理函数 → FC结果更新函数 → Data Service

使用方法：
  python scripts/test_e2e.py

前置条件：
  - 3个容器服务已启动（docker-compose up）
  - 3个FC函数已部署到阿里云
"""

import requests
import sys
import time
import json

# ============================================================
# 配置
# ============================================================
BASE_URL = "http://localhost:5000"  # Presentation Service 地址
POLL_INTERVAL = 3   # 轮询间隔（秒）
MAX_POLL_COUNT = 20  # 最大轮询次数


def test_health():
    """测试所有服务的健康检查"""
    print("\n" + "=" * 60)
    print("  步骤1: 健康检查")
    print("=" * 60)

    services = {
        'Presentation Service': f'{BASE_URL}/health',
        'Workflow Service': 'http://localhost:5001/health',
        'Data Service': 'http://localhost:5002/health',
    }

    all_healthy = True
    for name, url in services.items():
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                print(f"  ✅ {name}: 正常")
            else:
                print(f"  ❌ {name}: HTTP {resp.status_code}")
                all_healthy = False
        except requests.RequestException as e:
            print(f"  ❌ {name}: 无法连接 ({e})")
            all_healthy = False

    return all_healthy


def test_submit_approved():
    """测试正常提交（应通过所有规则，状态为 APPROVED）"""
    print("\n" + "=" * 60)
    print("  步骤2: 提交合规活动（预期 APPROVED）")
    print("=" * 60)

    payload = {
        "title": "Career Fair 2026",
        "description": "Annual career fair with over 50 top companies participating in recruitment and networking sessions.",
        "location": "Main Hall, Building A",
        "event_date": "2026-05-15",
        "organiser": "Career Center"
    }

    try:
        resp = requests.post(f'{BASE_URL}/api/submit', json=payload, timeout=15)
        result = resp.json()
        print(f"  提交响应: HTTP {resp.status_code}")
        print(f"  Record ID: {result.get('record_id', 'N/A')}")
        print(f"  Status: {result.get('status', 'N/A')}")

        record_id = result.get('record_id')
        if not record_id:
            print("  ❌ 未获取到 record_id")
            return None

        return poll_status(record_id, "APPROVED")

    except requests.RequestException as e:
        print(f"  ❌ 提交请求失败: {e}")
        return False


def test_submit_incomplete():
    """测试缺少必填项（预期 INCOMPLETE）"""
    print("\n" + "=" * 60)
    print("  步骤3: 提交不完整活动（预期 INCOMPLETE）")
    print("=" * 60)

    payload = {
        "title": "",  # 空标题
        "description": "Some description here that is long enough",
        "location": "Room 101",
        "event_date": "2026-06-01",
        "organiser": "Student Union"
    }

    try:
        resp = requests.post(f'{BASE_URL}/api/submit', json=payload, timeout=15)
        result = resp.json()
        record_id = result.get('record_id')
        if not record_id:
            print("  ❌ 未获取到 record_id")
            return False

        return poll_status(record_id, "INCOMPLETE")

    except requests.RequestException as e:
        print(f"  ❌ 提交请求失败: {e}")
        return False


def test_submit_needs_revision():
    """测试日期格式错误（预期 NEEDS REVISION）"""
    print("\n" + "=" * 60)
    print("  步骤4: 提交日期格式错误的活动（预期 NEEDS REVISION）")
    print("=" * 60)

    payload = {
        "title": "Club Social Night",
        "description": "A fun social night organized by the student society for all members to gather and enjoy.",
        "location": "Student Center",
        "event_date": "2026/06/15",  # 错误格式
        "organiser": "Social Club"
    }

    try:
        resp = requests.post(f'{BASE_URL}/api/submit', json=payload, timeout=15)
        result = resp.json()
        record_id = result.get('record_id')
        if not record_id:
            print("  ❌ 未获取到 record_id")
            return False

        return poll_status(record_id, "NEEDS REVISION")

    except requests.RequestException as e:
        print(f"  ❌ 提交请求失败: {e}")
        return False


def poll_status(record_id, expected_status):
    """轮询处理结果"""
    print(f"  轮询 record_id={record_id}，预期状态: {expected_status}")

    for i in range(MAX_POLL_COUNT):
        try:
            resp = requests.get(f'{BASE_URL}/api/status/{record_id}', timeout=10)
            record = resp.json()
            status = record.get('status', 'UNKNOWN')

            if status != 'PENDING':
                if status == expected_status:
                    print(f"  ✅ 状态匹配! record_id={record_id}, status={status}")
                    print(f"     Category: {record.get('category', 'N/A')}")
                    print(f"     Priority: {record.get('priority', 'N/A')}")
                    print(f"     Note: {record.get('note', 'N/A')}")
                    return True
                else:
                    print(f"  ❌ 状态不匹配: 期望={expected_status}, 实际={status}")
                    return False

        except requests.RequestException:
            pass

        time.sleep(POLL_INTERVAL)

    print(f"  ❌ 超时: record_id={record_id} 在 {MAX_POLL_COUNT * POLL_INTERVAL} 秒内未完成处理")
    return False


def test_records_list():
    """测试获取记录列表"""
    print("\n" + "=" * 60)
    print("  步骤5: 获取记录列表")
    print("=" * 60)

    try:
        resp = requests.get(f'{BASE_URL}/api/records', timeout=10)
        records = resp.json()
        print(f"  ✅ 获取到 {len(records)} 条记录")
        for r in records[:3]:
            print(f"     - [{r.get('status', '?')}] {r.get('title', 'N/A')}")
        return True
    except requests.RequestException as e:
        print(f"  ❌ 获取记录失败: {e}")
        return False


# ============================================================
# 主测试流程
# ============================================================
if __name__ == '__main__':
    print("\n🐝 Campus Buzz - 端到端测试")
    print("确保容器服务已启动（docker-compose up）且 FC 函数已部署")

    results = []

    # 健康检查
    results.append(("健康检查", test_health()))

    # 功能测试
    results.append(("APPROVED 提交", test_submit_approved()))
    results.append(("INCOMPLETE 提交", test_submit_incomplete()))
    results.append(("NEEDS REVISION 提交", test_submit_needs_revision()))
    results.append(("记录列表", test_records_list()))

    # 汇总
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {name}")

    print(f"\n  通过: {passed}/{total}")

    if passed == total:
        print("\n🎉 所有测试通过！混合云架构运行正常。")
    else:
        print("\n⚠️  部分测试失败，请检查 FC 函数部署和容器服务状态。")

    sys.exit(0 if passed == total else 1)
