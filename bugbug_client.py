import requests
from datetime import datetime

BASE_URL = "https://app.bugbug.io/api/v2"

def get_headers(api_key):
    return {"Authorization": api_key}

def get_all_suites(api_key):
    """Fetch all suites in a BugBug project."""
    response = requests.get(f"{BASE_URL}/suites/", headers=get_headers(api_key))
    response.raise_for_status()
    return response.json().get("results", [])

def get_latest_suite_run(api_key, suite_id):
    """Fetch the most recent suite run for a given suite."""
    response = requests.get(
        f"{BASE_URL}/suiteruns/",
        headers=get_headers(api_key),
        params={"suite": suite_id, "ordering": "-created", "limit": 1}
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    return results[0] if results else None

def get_suite_run_result(api_key, suite_run_id):
    """Fetch the full result of a specific suite run."""
    response = requests.get(
        f"{BASE_URL}/suiteruns/{suite_run_id}/",
        headers=get_headers(api_key)
    )
    response.raise_for_status()
    return response.json()

def parse_duration(duration_str):
    """
    Convert BugBug duration string '00:01:03.800006' to total seconds (float).
    Format is HH:MM:SS.ffffff
    """
    try:
        parts = duration_str.split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return round(hours * 3600 + minutes * 60 + seconds, 2)
    except Exception:
        return 0.0

def extract_clean_rows(suite_name, suite_run_data, run_date):
    """
    Extract only readable columns from a suite run result.
    Returns a list of rows ready for Sheets.
    """
    rows = []
    test_runs = suite_run_data.get("testRuns", [])

    for test in test_runs:
        status = test.get("status", "UNKNOWN").upper()
        duration = parse_duration(test.get("duration", "00:00:00"))
        error = test.get("errorCode") or ""

        rows.append([
            run_date,                        # Run Date
            suite_name,                      # Suite Name
            test.get("name", "N/A"),         # Test Case Name
            status,                          # PASSED / FAILED
            duration,                        # Duration (seconds)
            error                            # Failure Reason (errorCode)
        ])
    return rows

def was_run_today(suite_run_data, today_str):
    """Check if a suite run was created today."""
    created = suite_run_data.get("created", "")
    return created.startswith(today_str)
