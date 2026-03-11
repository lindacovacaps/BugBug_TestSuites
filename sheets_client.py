import gspread
from google.oauth2.service_account import Credentials
from summary import update_summary

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

HEADER_ROW = ["Run Date", "Suite Name", "Test Case Name", "Status", "Duration (s)", "Failure Reason"]

def connect(credentials_file):
    creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    return gspread.authorize(creds)

def get_or_create_worksheet(spreadsheet, suite_name):
    try:
        worksheet = spreadsheet.worksheet(suite_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=suite_name, rows="1000", cols="10")
        worksheet.append_row(HEADER_ROW, value_input_option="RAW")
        print(f" Created new sheet tab: '{suite_name}'")
    return worksheet

def append_rows_to_sheet(worksheet, rows):
    if rows: 
        worksheet.append_rows(rows, value_input_option="USER_ENTERED")
def finalize(spreadsheet):
    update_summary(spreadsheet)