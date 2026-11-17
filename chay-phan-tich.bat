@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [LỖI] Chưa cài đặt. Hãy bấm đúp file cai-dat.bat trước.
    echo.
    pause
    exit /b 1
)
set "DU_LIEU=01_du-lieu\raw\Du_lieu_Ban_Ket_FIT_Innovation\Du_lieu.csv"
if not exist "%DU_LIEU%" (
    echo [LỖI] Không tìm thấy file điểm:
    echo    %DU_LIEU%
    echo Hãy chép file Du_lieu.csv vào đúng thư mục trên (xem mục 3 trong HUONG-DAN-SU-DUNG.md),
    echo hoặc mở dashboard và tải file lên ở trang "Phân tích dữ liệu mới".
    echo.
    pause
    exit /b 1
)
echo ============================================================
echo   PHÂN TÍCH FILE ĐIỂM (khoảng 1 phút)
echo ============================================================
echo.
".venv\Scripts\python.exe" -X utf8 -W ignore 03_ma-nguon\run_gp3.py
if errorlevel 1 (
    echo.
    echo [LỖI] Phân tích chưa thành công. Chụp màn hình cửa sổ này gửi cho nhóm phát triển.
    echo.
    pause
    exit /b 1
)
echo.
echo ============================================================
echo   XONG. Bấm đúp file mo-dashboard.bat để xem kết quả.
echo   (Nếu dashboard đang mở, chỉ cần tải lại trang trình duyệt.)
echo ============================================================
echo.
pause
