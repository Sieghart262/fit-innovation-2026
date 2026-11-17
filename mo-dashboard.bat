@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\streamlit.exe" (
    echo [LỖI] Chưa cài đặt. Hãy bấm đúp file cai-dat.bat trước.
    echo.
    pause
    exit /b 1
)
echo ============================================================
echo   MỞ DASHBOARD
echo ============================================================
echo.
echo Đặt mật khẩu cho vai trò "Nhà trường" (dùng để đăng nhập trên dashboard).
echo Bỏ trống rồi nhấn Enter nếu chỉ cần xem công khai.
echo.
set "FIT_MAT_KHAU_NHA_TRUONG="
set /p "FIT_MAT_KHAU_NHA_TRUONG=Mật khẩu: "
cls
echo ============================================================
echo   DASHBOARD ĐANG CHẠY
echo   Trình duyệt sẽ tự mở. Nếu không, mở trình duyệt và vào:
echo   http://localhost:8501
echo.
echo   GIỮ cửa sổ này mở trong lúc dùng dashboard.
echo   Đóng cửa sổ này = tắt dashboard.
echo ============================================================
echo.
rem Mở trình duyệt sau 6 giây (chờ dashboard khởi động). Chạy ở chế độ headless để Streamlit
rem không hỏi địa chỉ email ở lần chạy đầu tiên – người dùng sẽ tưởng cửa sổ bị treo.
start "" /min cmd /c "timeout /t 6 >nul & start http://localhost:8501"
".venv\Scripts\streamlit.exe" run 03_ma-nguon\dashboard\app.py --server.port 8501 --server.headless true
pause
