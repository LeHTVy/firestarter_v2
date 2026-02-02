#!/bin/bash

# Di chuyển vào thư mục chứa script
cd "$(dirname "$0")"

# Đường dẫn tới venv ngay tại thư mục backend
VENV_PATH="./venv"

if [ -d "$VENV_PATH" ]; then
    echo "🚀 Kích hoạt môi trường ảo (venv)..."
    source "$VENV_PATH/bin/activate"
    
    echo "🔥 Khởi động Firestarter AI Backend (Port 8000)..."
    # Chạy trực tiếp uvicorn từ python module
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "❌ Không tìm thấy venv tại $VENV_PATH"
    echo "Vui lòng tạo venv bằng lệnh: python3 -m venv venv"
fi
