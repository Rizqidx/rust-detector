@echo off
title GUI YOLO Detector Launcher
color 0A

echo ======================================================
echo      RUN APLIKASI GUI DETECTOR
echo ======================================================
echo.

:: 1. Aktifkan Environment
if exist gui_env (
    echo [*] Mengaktifkan environment...
    call gui_env\Scripts\activate
) else (
    echo [!] Virtual environment tidak ditemukan
    echo [*] Pastikan menjalankan Setup.bat untuk mengatasi masalah tersebut
    pause
    exit
)

:: 2. Cek Folder Assets (Peringatan Dini)
if not exist assets (
    echo.
    echo [!] PERINGATAN: Folder 'assets' tidak ditemukan!
    echo     Aplikasi mungkin error jika file icon atau loading image hilang.
    echo.
)

:: 3. Jalankan Aplikasi Utama
echo.
echo Menjalankan GUI_Detector.py ...
echo.
python GUI_Detector.py
pause

:: 4. Selesai
echo.
if errorlevel 1 (
    echo [X] Aplikasi tertutup karena Error.
) else (
    echo [+] Aplikasi ditutup dengan normal.
)