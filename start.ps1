# Launches both servers in separate windows.
# Run with:  powershell -ExecutionPolicy Bypass -File .\start.ps1

$root = $PSScriptRoot

Write-Host "Starting backend (FastAPI) on http://localhost:8000 ..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root\backend'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"
)

Write-Host "Starting frontend (Next.js) on http://localhost:3000 ..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root\frontend'; npm.cmd run dev"
)

Write-Host ""
Write-Host "Open http://localhost:3000 in your browser."
