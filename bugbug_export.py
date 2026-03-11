import config
from bugbug_client import (
    get_all_suites,
    get_latest_suite_run,
    get_suite_run_result,
    extract_clean_rows,
    was_run_today
)
from sheets_client import connect, get_or_create_worksheet, append_rows_to_sheet, finalize
from datetime import datetime

def process_project(project_name, api_key, spreadsheet, today_str):
    """Process all suites within a single BugBug project."""
    print(f"\nProject: {project_name}")
    print(f"{'-'*40}")

    suites = get_all_suites(api_key)
    print(f"  Found {len(suites)} suite(s)")

    project_summary = []

    for suite in suites:
        suite_id = suite["id"]
        suite_name = suite["name"]

        # Use "ProjectName — SuiteName" as the tab name if a project has multiple suites
        tab_name = f"{project_name}" if len(suites) == 1 else f"{project_name} — {suite_name}"
        print(f"  Processing suite: {suite_name}")

        latest_run = get_latest_suite_run(api_key, suite_id)

        if not latest_run:
            print(f"    ⚠ No runs found. Skipping.")
            project_summary.append((tab_name, "NO RUNS FOUND", 0))
            continue

        #if not was_run_today(latest_run, today_str):
        #    print(f"    ⚠ Last run was not today ({latest_run.get('created', '')[:10]}). Skipping.")
        #    project_summary.append((tab_name, "NOT RUN TODAY", 0))
        #    continue

        run_data = get_suite_run_result(api_key, latest_run["id"])
        rows = extract_clean_rows(suite_name, run_data, today_str)

        worksheet = get_or_create_worksheet(spreadsheet, tab_name)
        append_rows_to_sheet(worksheet, rows)

        passed = sum(1 for r in rows if r[3] == "PASSED")
        failed = sum(1 for r in rows if r[3] == "FAILED")
        print(f"    ✓ {len(rows)} test cases — {passed} passed, {failed} failed")
        project_summary.append((tab_name, "OK", len(rows)))

    return project_summary

def main():
    today_str = datetime.today().strftime("%Y-%m-%d")
    print(f"\n{'='*50}")
    print(f"BugBug Export — {today_str}")
    print(f"{'='*50}")

    print("\nConnecting to Google Sheets...")
    gc = connect(config.GOOGLE_CREDENTIALS_FILE)
    spreadsheet = gc.open(config.GOOGLE_SHEET_NAME)
    print("Connected.")

    all_summary = []

    for project_name, api_key in config.BUGBUG_PROJECTS:
        try:
            project_summary = process_project(project_name, api_key, spreadsheet, today_str)
            all_summary.extend(project_summary)
        except Exception as e:
            print(f"  ✗ ERROR processing {project_name}: {e}")
            all_summary.append((project_name, f"ERROR: {e}", 0))
    
    # Summary Sheet Pivot Table Logging
    print("\nUpdating Summary sheet...")
    finalize(spreadsheet)

    # Final summary
    print(f"\n{'='*50}")
    print("EXPORT SUMMARY")
    print(f"{'='*50}")
    for tab_name, status, count in all_summary:
        icon = "✓" if status == "OK" else "⚠" if status != "OK" else "✗"
        print(f"  {icon} {tab_name:<40} {status}  ({count} rows)")
    print(f"\nDone. Open your Master Sheet to view results.")

if __name__ == "__main__":
    main()
