# Start the backend with auto-reload (SQLite default). Run setup once first:
#   cd backend; python -m venv venv; .\venv\Scripts\pip install -r requirements.txt; .\venv\Scripts\python -m app.seed
Set-Location "$PSScriptRoot\backend"
.\venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
