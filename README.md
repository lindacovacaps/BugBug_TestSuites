# BugBug_TestSuites
Python script for retrieving test suite runs (daily) and storing in spreadsheet for easy analysis

## Set Up / Running
set-up: create venv + pip install -r requirements.txt

to run script: python bugbug_export.py

exported sheets will be in master document organised by "Project_Name - Test Suite Title". 

Master sheets document (can be changed): https://docs.google.com/spreadsheets/d/1s7LpJgfEgrVqavlW9zQBBnfvYE1VlDK3zjXJQP4QvQQ/edit?gid=0#gid=0

Github Repo: https://github.com/lindacovacaps/BugBug_TestSuites 

### credentials.json
Using a google cloud service account, enable APIs for Google Drive as well as Google Sheets. After creating account, add personal credentials.json file from service account keys to local directory. Importantly, add service account email address (ending with "@bugbug-testsuites.iam.gserviceaccount.com" or equivalent) to shared list of worksheet collaborators with "Editor" access. 

Ensure that both 

GOOGLE_SHEET_NAME = "[Automated] BugBug Test Results" (or equivalent sheet name -- must be exact verbatim)
GOOGLE_CREDENTIALS_FILE = "credentials.json"

before running the script. 

## Adding New Projects / Suites
New projects can be added from bugbug into config.py in the format of: ("PROJECT_NAME", "Token PROJECT_API_KEY") and bugbug_export.py then re-run for new project data to start being logged. 

New suites added within existing projects do not need to be added into any configuration files, they will automatically be added and logged on the worksheet without code changes required. 


