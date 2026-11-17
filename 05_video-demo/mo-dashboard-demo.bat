@echo off
chcp 65001 >nul
rem Mở dashboard CHỈ VỚI DỮ LIỆU GIẢ để quay video demo.
rem Kết quả và lịch sử phân tích nằm riêng trong 01_du-lieu\video-demo\, không lẫn với dữ liệu thật.
cd /d "%~dp0.."
if not exist ".venv\Scripts\streamlit.exe" (
    echo [LỖI] Chưa cài đặt. Hãy bấm đúp file cai-dat.bat ở thư mục gốc trước.
    pause
    exit /b 1
)
if not exist "01_du-lieu\video-demo\Du_lieu_demo.csv" (
    echo Chưa có dữ liệu demo, đang tạo...
    ".venv\Scripts\python.exe" -X utf8 05_video-demo\tao_du_lieu_demo.py
)
set "FIT_KET_QUA=%CD%\01_du-lieu\video-demo\ket-qua"
set "FIT_LICH_SU=%CD%\01_du-lieu\video-demo\lich-su-phan-tich"
set "FIT_MAT_KHAU_NHA_TRUONG=demo"
cls
echo ============================================================
echo   DASHBOARD DEMO (DỮ LIỆU GIẢ) ĐANG CHẠY
echo   Địa chỉ: http://localhost:8502      Mật khẩu Nhà trường: demo
echo   GIỮ cửa sổ này mở trong lúc quay. Đóng cửa sổ = tắt dashboard.
echo ============================================================
start "" /min cmd /c "timeout /t 6 >nul & start http://localhost:8502"
".venv\Scripts\streamlit.exe" run 03_ma-nguon\dashboard\app.py --server.port 8502 --server.headless true
pause
