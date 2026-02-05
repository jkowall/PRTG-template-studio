<#
.SYNOPSIS
    Runs the PRTG Template Studio application in the virtual environment.
.DESCRIPTION
    Checks for 'venv', creates it if missing, installs requirements, and runs the app.
    Passes any arguments (like --reload) to app.py.
.EXAMPLE
    .\run.ps1
.EXAMPLE
    .\run.ps1 --reload
#>

$ErrorActionPreference = "Stop"

# Ensure script directory is current working directory
Set-Location $PSScriptRoot

if (-not (Test-Path "venv")) {
    Write-Host "[-] Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "[+] venv created." -ForegroundColor Green
    
    Write-Host "[-] Installing requirements..." -ForegroundColor Yellow
    .\venv\Scripts\python.exe -m pip install -r requirements.txt
    Write-Host "[+] Requirements installed." -ForegroundColor Green
} else {
    # Optional: Check if we need to update requirements? 
    # For now, let's imply that if venv exists, it's good. 
    # Or just try to install quickly to ensure sync?
    # .\venv\Scripts\python.exe -m pip install -r requirements.txt -q
}

Write-Host "[*] Starting PRTG Template Studio..." -ForegroundColor Cyan
& .\venv\Scripts\python.exe app.py $args
