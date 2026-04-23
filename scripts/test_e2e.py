"""
Campus Buzz - End-to-End Test Script
====================================
Tests the full hybrid cloud workflow:

  User submission
    → Workflow Service
    → FC submission event function
    → FC processing function
    → FC result update function
    → Data Service

Usage:
  python scripts/test_e2e.py

Before you run it:
  - All 3 container services should already be up (docker-compose up)
  - All 3 FC functions should be deployed to Alibaba Cloud
"""

import requests
import sys
import time
import json

# ============================================================
# Config
# ============================================================
BASE_URL = "http://localhost:5000"  # Presentation Service base URL
POLL_INTERVAL = 3   # Poll every 3 seconds
MAX_POLL_COUNT = 20  # Max polling attempts


def test_health():
    """Check health endpoints for all local services"""
    print("\n" + "=" * 60)
    print("  Step 1: Health checks")
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
                print(f"  ✅ {name}: healthy")
            else:
                print(f"  ❌ {name}: HTTP {resp.status_code}")
                all_healthy = False
        except requests.RequestException as e:
            print(f"  ❌ {name}: unreachable ({e})")
            all_healthy = False

    return all_healthy


def test_submit_approved():
    """Submit a valid event and expect APPROVED"""
    print("\n" + "=" * 60)
    print("  Step 2: Submit a valid event (expect APPROVED)")
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
        print(f"  Submit response: HTTP {resp.status_code}")
        print(f"  Record ID: {result.get('record_id', 'N/A')}")
        print(f"  Status: {result.get('status', 'N/A')}")

        record_id = result.get('record_id')
        if not record_id:
            print("  ❌ record_id was not returned")
            return None

        return poll_status(record_id, "APPROVED")

    except requests.RequestException as e:
        print(f"  ❌ Submit request failed: {e}")
        return False


def test_submit_incomplete():
    """Submit an incomplete event and expect INCOMPLETE"""
    print("\n" + "=" * 60)
    print("  Step 3: Submit an incomplete event (expect INCOMPLETE)")
    print("=" * 60)

    payload = {
        "title": "",  # Missing title
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
            print("  ❌ record_id was not returned")
            return False

        return poll_status(record_id, "INCOMPLETE")

    except requests.RequestException as e:
        print(f"  ❌ Submit request failed: {e}")
        return False


def test_submit_needs_revision():
    """Submit an event with a bad date format and expect NEEDS REVISION"""
    print("\n" + "=" * 60)
    print("  Step 4: Submit an event with an invalid date format (expect NEEDS REVISION)")
    print("=" * 60)

    payload = {
        "title": "Club Social Night",
        "description": "A fun social night organized by the student society for all members to gather and enjoy.",
        "location": "Student Center",
        "event_date": "2026/06/15",  # Wrong format
        "organiser": "Social Club"
    }

    try:
        resp = requests.post(f'{BASE_URL}/api/submit', json=payload, timeout=15)
        result = resp.json()
        record_id = result.get('record_id')
        if not record_id:
            print("  ❌ record_id was not returned")
            return False

        return poll_status(record_id, "NEEDS REVISION")

    except requests.RequestException as e:
        print(f"  ❌ Submit request failed: {e}")
        return False


def poll_status(record_id, expected_status):
    """Poll until the record leaves PENDING or times out"""
    print(f"  Polling record_id={record_id}, expected status: {expected_status}")

    for i in range(MAX_POLL_COUNT):
        try:
            resp = requests.get(f'{BASE_URL}/api/status/{record_id}', timeout=10)
            record = resp.json()
            status = record.get('status', 'UNKNOWN')

            if status != 'PENDING':
                if status == expected_status:
                    print(f"  ✅ Status matched: record_id={record_id}, status={status}")
                    print(f"     Category: {record.get('category', 'N/A')}")
                    print(f"     Priority: {record.get('priority', 'N/A')}")
                    print(f"     Note: {record.get('note', 'N/A')}")
                    return True
                else:
                    print(f"  ❌ Status mismatch: expected={expected_status}, got={status}")
                    return False

        except requests.RequestException:
            pass

        time.sleep(POLL_INTERVAL)

    print(f"  ❌ Timed out: record_id={record_id} did not finish within {MAX_POLL_COUNT * POLL_INTERVAL} seconds")
    return False


def test_records_list():
    """Fetch the record list and print a few samples"""
    print("\n" + "=" * 60)
    print("  Step 5: Fetch record list")
    print("=" * 60)

    try:
        resp = requests.get(f'{BASE_URL}/api/records', timeout=10)
        records = resp.json()
        print(f"  ✅ Retrieved {len(records)} records")
        for r in records[:3]:
            print(f"     - [{r.get('status', '?')}] {r.get('title', 'N/A')}")
        return True
    except requests.RequestException as e:
        print(f"  ❌ Failed to fetch records: {e}")
        return False


# ============================================================
# Main test flow
# ============================================================
if __name__ == '__main__':
    print("\n🐝 Campus Buzz - End-to-End Test")
    print("Make sure the container services are running (docker-compose up) and the FC functions are deployed.")

    results = []

    # Health checks
    results.append(("Health checks", test_health()))

    # Functional tests
    results.append(("APPROVED submission", test_submit_approved()))
    results.append(("INCOMPLETE submission", test_submit_incomplete()))
    results.append(("NEEDS REVISION submission", test_submit_needs_revision()))
    results.append(("Record list", test_records_list()))

    # Summary
    print("\n" + "=" * 60)
    print("  Test summary")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {name}")

    print(f"\n  Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! The hybrid cloud workflow is working as expected.")
    else:
        print("\n⚠️  Some tests failed. Check your FC deployment and container service status.")

    sys.exit(0 if passed == total else 1)
