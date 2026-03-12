# summary.py — improved high-level summary with three views
import gspread
import gspread.utils
from collections import defaultdict
from datetime import datetime

EXCLUDE_SHEETS = ['Summary', 'General Notice']

# ── Colour palette ────────────────────────────────────────────────
HEADER_BG    = {'red': 0.129, 'green': 0.149, 'blue': 0.196}  # dark navy
HEADER_FG    = {'red': 1.0,   'green': 1.0,   'blue': 1.0}
PASS_BG      = {'red': 0.851, 'green': 0.937, 'blue': 0.855}  # soft green
FAIL_BG      = {'red': 0.988, 'green': 0.855, 'blue': 0.843}  # soft red
WARN_BG      = {'red': 1.0,   'green': 0.949, 'blue': 0.800}  # soft amber
SUBHDR_BG    = {'red': 0.227, 'green': 0.271, 'blue': 0.353}  # medium navy
SUBHDR_FG    = {'red': 1.0,   'green': 1.0,   'blue': 1.0}
ROW_ALT_BG   = {'red': 0.953, 'green': 0.961, 'blue': 0.973}  # light blue-grey
ROW_BASE_BG  = {'red': 1.0,   'green': 1.0,   'blue': 1.0}


def update_summary(spreadsheet: gspread.Spreadsheet):
    raw = _collect_all_results(spreadsheet)
    _write_dashboard(spreadsheet, raw)


# ── Data collection ───────────────────────────────────────────────

def _collect_all_results(spreadsheet):
    results = []
    for ws in spreadsheet.worksheets():
        if ws.title in EXCLUDE_SHEETS:
            continue
        base_project = ws.title.split(' — ')[0].strip()
        for row in ws.get_all_records():
            if row.get('Test Case Name') and row.get('Status') in ('PASSED', 'FAILED'):
                results.append({
                    'run_date':  str(row['Run Date'])[:10],
                    'project':   base_project,
                    'test_case': row['Test Case Name'],
                    'status':    row['Status'],
                })
    return results


# ── Main dashboard writer ─────────────────────────────────────────

def _write_dashboard(spreadsheet, results):
    try:
        sheet = spreadsheet.worksheet('Summary')
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet('Summary', rows=300, cols=60)

    all_dates    = sorted({r['run_date'] for r in results}, reverse=True)
    all_projects = sorted({r['project'] for r in results})

    # Aggregate: project x date -> {PASSED, FAILED, failing_tests}
    proj_date = defaultdict(lambda: defaultdict(lambda: {'PASSED': 0, 'FAILED': 0, 'failing_tests': set()}))
    test_date = defaultdict(lambda: defaultdict(lambda: {'PASSED': 0, 'FAILED': 0}))

    for r in results:
        proj_date[r['project']][r['run_date']][r['status']] += 1
        if r['status'] == 'FAILED':
            proj_date[r['project']][r['run_date']]['failing_tests'].add(r['test_case'])
        test_date[(r['project'], r['test_case'])][r['run_date']][r['status']] += 1

    # ── Build data rows ───────────────────────────────────────────
    all_data: list[list] = []

    # Title
    all_data.append(['TEST SUITE DASHBOARD'] + [''] * (2 + len(all_dates) * 3 - 1))
    all_data.append(['Generated: ' + datetime.today().strftime('%Y-%m-%d %H:%M')] + [''] * (1 + len(all_dates) * 3))
    all_data.append([''] * (3 + len(all_dates) * 3))

    # ── Section 1: Scorecard ──────────────────────────────────────
    section1_row = len(all_data) + 1
    all_data.append(['PROJECT HEALTH SCORECARD'] + [''] * (2 + len(all_dates) * 3 - 1))

    hdr = ['Project', 'Test Cases']
    for d in all_dates:
        #short = d[5:]
        #hdr += [f'{short} Pass %', f'{short} Passed', f'{short} Failed']
        hdr += [f'{d} Pass %', f'{d} Passed', f'{d} Failed']
    all_data.append(hdr)
    scorecard_hdr_row = len(all_data)
    scorecard_data_start = len(all_data) + 1

    for proj in all_projects:
        test_cases = len({r['test_case'] for r in results if r['project'] == proj})
        row = [proj, test_cases]
        for d in all_dates:
            p = proj_date[proj][d]['PASSED']
            f = proj_date[proj][d]['FAILED']
            total = p + f
            pct = f'{round(100*p/total)}%' if total > 0 else '-'
            row += [pct, p, f]
        all_data.append(row)
    scorecard_data_end = len(all_data)

    # ── Section 2: Trend heatmap ──────────────────────────────────
    all_data.append([''] * (3 + len(all_dates) * 3))
    section2_row = len(all_data) + 1
    all_data.append(['DAILY PASS RATE TREND (per project)'] + [''] * len(all_dates))

    all_data.append(['Project'] + all_dates)
    trend_hdr_row = len(all_data)
    trend_data_start = len(all_data) + 1
    trend_pct_matrix = []

    for proj in all_projects:
        row = [proj]
        proj_row_pcts = []
        for d in all_dates:
            p = proj_date[proj][d]['PASSED']
            f = proj_date[proj][d]['FAILED']
            total = p + f
            pct_num = round(100 * p / total) if total > 0 else None
            row.append(f'{pct_num}%' if pct_num is not None else '-')
            proj_row_pcts.append(pct_num)
        all_data.append(row)
        trend_pct_matrix.append(proj_row_pcts)
    trend_data_end = len(all_data)

    # ── Section 3: Failing tests spotlight ───────────────────────
    all_data.append([''] * (3 + len(all_dates) * 3))
    section3_row = len(all_data) + 1
    all_data.append(['FAILING TESTS SPOTLIGHT (most recent run)'] + [''] * 3)

    all_data.append(['Project', 'Test Case', 'Status', 'Failure Streak (days)'])
    spotlight_hdr_row = len(all_data)
    spotlight_data_start = len(all_data) + 1

    latest_date = all_dates[0] if all_dates else None
    spotlight_rows = []
    if latest_date:
        seen = {}
        for r in results:
            if r['run_date'] == latest_date and r['status'] == 'FAILED':
                streak = 0
                for d in all_dates:
                    if test_date[(r['project'], r['test_case'])][d].get('FAILED', 0) > 0:
                        streak += 1
                    else:
                        break
                key = (r['project'], r['test_case'])
                if key not in seen or streak > seen[key][3]:
                    seen[key] = [r['project'], r['test_case'], 'FAILED', streak]
        spotlight_rows = sorted(seen.values(), key=lambda x: (-x[3], x[0]))

    if spotlight_rows:
        all_data.extend(spotlight_rows)
    else:
        all_data.append(['No failures on the most recent run', '', '', ''])
    spotlight_data_end = len(all_data)

    # ── Write data (single API call) ──────────────────────────────
    print('  Writing data...')
    sheet.update(values=all_data, range_name='A1', value_input_option='USER_ENTERED')

    # ── Build ALL format requests and send as ONE batch_format call ──
    print('  Applying formatting...')
    nc = max(len(r) for r in all_data)

    def _a1(r, c):
        return gspread.utils.rowcol_to_a1(r, c)

    def _rng(r1, c1, r2, c2):
        return f'{_a1(r1, c1)}:{_a1(r2, c2)}'

    last_col = nc
    formats = []

    def _add(range_str, fmt):
        formats.append({'range': range_str, 'format': fmt})

    # Title row
    _add('A1', {'textFormat': {'bold': True, 'fontSize': 14, 'foregroundColor': HEADER_BG}})

    # Section header banners
    for sr in [section1_row, section2_row, section3_row]:
        _add(_rng(sr, 1, sr, last_col), {
            'backgroundColor': HEADER_BG,
            'textFormat': {'bold': True, 'fontSize': 11, 'foregroundColor': HEADER_FG},
            'horizontalAlignment': 'LEFT',
        })

    # Column sub-headers
    for hr in [scorecard_hdr_row, trend_hdr_row, spotlight_hdr_row]:
        _add(_rng(hr, 1, hr, last_col), {
            'backgroundColor': SUBHDR_BG,
            'textFormat': {'bold': True, 'foregroundColor': SUBHDR_FG},
            'horizontalAlignment': 'CENTER',
            'verticalAlignment': 'MIDDLE',
        })

    # Scorecard data rows
    for i, proj in enumerate(all_projects):
        data_row = scorecard_data_start + i
        bg = ROW_ALT_BG if i % 2 == 0 else ROW_BASE_BG
        _add(_rng(data_row, 1, data_row, last_col), {'backgroundColor': bg, 'horizontalAlignment': 'CENTER'})
        _add(_a1(data_row, 1), {'textFormat': {'bold': True}, 'horizontalAlignment': 'LEFT'})

        for j, d in enumerate(all_dates):
            col_pct  = 3 + j * 3
            col_fail = col_pct + 2
            p = proj_date[proj][d]['PASSED']
            f = proj_date[proj][d]['FAILED']
            total = p + f
            if total > 0:
                pct = 100 * p / total
                cell_bg = PASS_BG if pct >= 90 else WARN_BG if pct >= 50 else FAIL_BG
                _add(_rng(data_row, col_pct, data_row, col_fail), {'backgroundColor': cell_bg})

    # Trend heatmap rows
    for i, proj in enumerate(all_projects):
        data_row = trend_data_start + i
        bg = ROW_ALT_BG if i % 2 == 0 else ROW_BASE_BG
        _add(_rng(data_row, 1, data_row, 1 + len(all_dates)), {'backgroundColor': bg})
        _add(_a1(data_row, 1), {'textFormat': {'bold': True}})
        for j, pct_num in enumerate(trend_pct_matrix[i]):
            if pct_num is not None:
                cell_bg = PASS_BG if pct_num >= 90 else WARN_BG if pct_num >= 50 else FAIL_BG
                _add(_a1(data_row, 2 + j), {'backgroundColor': cell_bg, 'horizontalAlignment': 'CENTER'})

    # Spotlight rows
    for i, sr in enumerate(spotlight_rows):
        data_row = spotlight_data_start + i
        bg = ROW_ALT_BG if i % 2 == 0 else ROW_BASE_BG
        _add(_rng(data_row, 1, data_row, 4), {'backgroundColor': bg})
        _add(_a1(data_row, 3), {'backgroundColor': FAIL_BG, 'textFormat': {'bold': True}, 'horizontalAlignment': 'CENTER'})
        streak = sr[3]
        if streak >= 3:
            _add(_a1(data_row, 4), {'backgroundColor': FAIL_BG, 'textFormat': {'bold': True}, 'horizontalAlignment': 'CENTER'})
        elif streak == 2:
            _add(_a1(data_row, 4), {'backgroundColor': WARN_BG, 'horizontalAlignment': 'CENTER'})

    # Send all formatting in a single API call
    sheet.batch_format(formats)

    sheet.freeze(rows=1)

    print(f'  Done! Dashboard summary written - {len(all_projects)} projects x {len(all_dates)} dates')


if __name__ == "__main__":
    import config
    from sheets_client import connect

    gc = connect(config.GOOGLE_CREDENTIALS_FILE)
    spreadsheet = gc.open(config.GOOGLE_SHEET_NAME)
    update_summary(spreadsheet)