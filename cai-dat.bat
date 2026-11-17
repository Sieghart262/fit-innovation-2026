@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   CÀI ĐẶT (chỉ cần làm MỘT lần trên mỗi máy)
echo ============================================================
echo.
where python >nul 2>nul
if errorlevel 1 (
    echo [LỖI] Máy chưa có Python.
    echo Hãy cài Python theo mục 1 trong file HUONG-DAN-SU-DUNG.md,
    echo nhớ tích ô "Add python.exe to PATH", rồi bấm đúp lại file này.
    echo.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo Đang tạo môi trường chạy riêng cho dự án...
    python -m venv .venv
    if errorlevel 1 goto loi
)
echo Đang tải và cài các thư viện cần thiết (vài phút, cần có Internet)...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>nul
".venv\Scripts\python.exe" -m pip install -r 03_ma-nguon\requirements.txt
if errorlevel 1 goto loi
echo.
echo ============================================================
echo   CÀI ĐẶT XONG. Bước tiếp theo: bấm đúp file mo-dashboard.bat
echo ============================================================
echo.
pause
exit /b 0

:loi
echo.
echo [LỖI] Cài đặt chưa thành công. Kiểm tra kết nối Internet rồi bấm đúp lại file này.
echo Nếu vẫn lỗi, chụp màn hình cửa sổ này gửi cho nhóm phát triển.
echo.
pause
exit /b 1
