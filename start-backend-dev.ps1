# Start the backend without auto-reload (stable env on Windows VMs).
# Uses the default SQLite database (backend/tapms.db).
$env:ENVIRONMENT = "local"
Set-Location "$PSScriptRoot\backend"
.\venv\Scripts\python -m uvicorn app.main:app --port 8000
