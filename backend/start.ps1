# Di chuyển vào thư mục backend
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

$VENV_PATH = "./venv"

if (Test-Path "$VENV_PATH/Scripts/Activate.ps1") {
    Write-Host "🚀 Kích hoạt môi trường ảo (venv)..." -ForegroundColor Cyan
    & "$VENV_PATH/Scripts/Activate.ps1"
    
    Write-Host "🔥 Khởi động Firestarter AI Backend..." -ForegroundColor Yellow
    python run.py
} else {
    Write-Host "❌ Không tìm thấy venv tại $VENV_PATH" -ForegroundColor Red
}
