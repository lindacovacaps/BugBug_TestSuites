# BugBug_TestSuites
Python script for retrieving test suite runs (daily) and storing in spreadsheet for easy analysis

## Set Up / Running
set-up: create venv + pip install -r requirements.txt

to run script: python bugbug_export.py

exported sheets will be in master document organised by "Project_Name - Test Suite Title". 

Master sheets document (can be changed): https://docs.google.com/spreadsheets/d/1s7LpJgfEgrVqavlW9zQBBnfvYE1VlDK3zjXJQP4QvQQ/edit?gid=0#gid=0

Github Repo: https://github.com/lindacovacaps/BugBug_TestSuites 

### Generating credentials.json
Create a google cloud project. Once created, enable the APIs for  Google Drive as well as Google Sheets for the project. Then navigate to "IAM & Admin > Service Accounts" and create a service account for the project. Once created, go to the service account's sub-section "Keys" and click "new key" > "JSON" and download the credentials.json file. 
Additionally, add personal credentials.json file from service account keys to your local project file directory. Importantly, add service account email address (ending with "@bugbug-testsuites.iam.gserviceaccount.com" or equivalent) to the "shared" list of google sheets collaborators with "Editor" access to allow it to make remove changes on your behalf. 

Lastly, ensure that both 

GOOGLE_SHEET_NAME = "[Automated] BugBug Test Results" (or equivalent sheet name -- must be exact verbatim)
GOOGLE_CREDENTIALS_FILE = "credentials.json"

before running the script. 

## Adding New Projects / Suites
New projects can be added from bugbug into config.py in the format of: ("PROJECT_NAME", "Token PROJECT_API_KEY") and bugbug_export.py then re-run for new project data to start being logged. 

New suites added within existing projects do not need to be added into any configuration files, they will automatically be added and logged on the worksheet without code changes required. 


