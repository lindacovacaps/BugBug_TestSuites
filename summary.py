# summary.py
import gspread
from collections import defaultdict

EXCLUDE_SHEETS = ['Summary', 'General Notice']

def update_summary(spreadsheet: gspread.Spreadsheet):
    all_results = _collect_all_results(spreadsheet)
    rows = _build_pivot_rows(all_results)
    _write_summary_sheet(spreadsheet, rows)

def _collect_all_results(spreadsheet):
    results = []
    for ws in spreadsheet.worksheets():
        if ws.title in EXCLUDE_SHEETS:
            continue

        # Strip the " — Suite Name" suffix to get the base project name
        # e.g. "Deal_Author(NewUI_Release) — All tests" → "Deal_Author(NewUI_Release)"
        base_project = ws.title.split(' — ')[0].strip()

        for row in ws.get_all_records():
            if row.get('Test Case Name') and row.get('Status') in ('PASSED', 'FAILED'):
                results.append({
                    'run_date': str(row['Run Date']),
                    'project': base_project,        # <-- use stripped name
                    'test_case': row['Test Case Name'],
                    'status': row['Status'],
                })
    return results

def _build_pivot_rows(results):
    counts = defaultdict(lambda: {'PASSED': 0, 'FAILED': 0})
    all_dates = set()
    test_index = {}  # (project, test_case) -> project

    for r in results:
        key = (r['project'], r['test_case'], r['run_date'])  # no suite in key
        counts[key][r['status']] += 1                        # sums across all suites
        all_dates.add(r['run_date'])
        test_index[(r['project'], r['test_case'])] = r['project']

    sorted_dates = sorted(all_dates, reverse=True)
    sorted_tests = sorted(test_index.keys(), key=lambda x: (x[0], x[1]))

    header = ['Project', 'Test Case Name']
    for date in sorted_dates:
        header.append(f'{date} PASSED')
        header.append(f'{date} FAILED')

    rows = [header]
    for (project, test_case) in sorted_tests:
        row = [project, test_case]
        for date in sorted_dates:
            key = (project, test_case, date)
            row.append(counts[key]['PASSED'])
            row.append(counts[key]['FAILED'])
        rows.append(row)

    return rows

def _write_summary_sheet(spreadsheet, rows):
    try:
        sheet = spreadsheet.worksheet('Summary')
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet('Summary', rows=1000, cols=100)

    sheet.update('A1', rows)

    # Bold + grey header
    sheet.format(f'A1:{gspread.utils.rowcol_to_a1(1, len(rows[0]))}', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.875, 'green': 0.894, 'blue': 0.925}
    })

    # Bold + light gray the Project column (col A) for all data rows
    sheet.format(f'A2:A{len(rows)}', {
        'textFormat': {'bold': True}
    })
    sheet.format(f'A2:B{len(rows)}', {
        'backgroundColor': {'red': 0.957, 'green': 0.965, 'blue': 0.973}
    })

    print(f"✅ Summary sheet updated: {len(rows)-1} test cases × {len(rows[0])-2} date columns")
