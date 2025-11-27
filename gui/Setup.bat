@echo off
title GUI YOLO Detector Setup
color 0A

echo ======================================================
echo      SETUP APLIKASI GUI DETECTOR
echo ======================================================
echo.

:: 1. Cek apakah folder 'gui_env' sudah ada
if exist gui_env (
    echo [+] Virtual environment ditemukan.
) else (
    echo [!] Virtual environment belum ada. Membuat baru...
    python -m venv gui_env
    if errorlevel 1 (
        echo [X] Gagal membuat gui_env. Pastikan Python sudah terinstall.
        pause
        exit
    )
    echo [+] Virtual environment berhasil dibuat.
)

:: 2. Aktifkan Environment
echo [*] Mengaktifkan environment...
call gui_env\Scripts\activate

:: 3. Cek dan Install Library
echo [*] Memeriksa dan mengupdate library...
python -m pip install --upgrade pip

echo [*] Menginstall dependencies dari requirements.txt...
if exist ..\requirements.txt (
    echo [+] requirements.txt ditemukan.
    pip install -r ..\requirements.txt
) else (
    echo [X] requirements.txt tidak ditemukan! Pastikan file tersebut ada di direktori yang sama
    pause
    exit
)

:: 4. Cek Folder Assets (Peringatan Dini)
if not exist assets (
    echo.
    echo [!] PERINGATAN: Folder 'assets' tidak ditemukan!
    echo     Aplikasi mungkin error jika file icon atau loading image hilang.
    echo.
)

:: pemmbersihan
timeout /t 3 /nobreak
cls 

:: 5. pengecekan terakhir
echo [*] Melakukan pengecekan akhir...
if exist gui_env if exist assets (
    echo [+] Setup selesai. Anda dapat menjalankan aplikasi dengan Run_GUI_Detector.bat
    echo.
    pause
)