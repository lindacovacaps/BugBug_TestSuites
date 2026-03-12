import sys
import config
from sheets_client import connect

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('1', '2'):
        print("Usage: python run.py <mode>")
        print("  1 — Full export: BugBug fetch + Summary rebuild")
        print("  2 — Summary only: rebuild Summary from existing sheet data")
        sys.exit(1)

    mode = sys.argv[1]

    print("\nConnecting to Google Sheets...")
    gc = connect(config.GOOGLE_CREDENTIALS_FILE)
    spreadsheet = gc.open(config.GOOGLE_SHEET_NAME)
    print("Connected.")

    if mode == '1':
        print("\n[Mode 1] Running BugBug export + Summary...\n")
        from bugbug_export import process_project
        from summary import update_summary
        from datetime import datetime

        today_str = datetime.today().strftime("%Y-%m-%d")
        all_summary = []

        for project_name, api_key in config.BUGBUG_PROJECTS:
            try:
                project_summary = process_project(project_name, api_key, spreadsheet, today_str)
                all_summary.extend(project_summary)
            except Exception as e:
                print(f"  ERROR processing {project_name}: {e}")
                all_summary.append((project_name, f"ERROR: {e}", 0))

        print("\nUpdating Summary sheet...")
        update_summary(spreadsheet)

        print("\nExport complete:")
        for tab_name, status, count in all_summary:
            icon = "✓" if status == "OK" else "✗"
            print(f"  {icon} {tab_name:<40} {status}  ({count} rows)")

    elif mode == '2':
        print("\n[Mode 2] Rebuilding Summary from existing sheet data...\n")
        from summary import update_summary
        update_summary(spreadsheet)

    print("\nDone.")

if __name__ == "__main__":
    main()