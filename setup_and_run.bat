@echo off
:: Set code page to UTF-8
chcp 65001 > nul
setlocal enabledelayedexpansion

echo Checking if Miniconda is installed...

:: Check if Miniconda is already installed
if exist "%USERPROFILE%\miniconda3\Scripts\conda.exe" (
    echo Miniconda is already installed.
    set CONDA_PATH=%USERPROFILE%\miniconda3\Scripts\conda.exe
) else if exist "%USERPROFILE%\Miniconda3\Scripts\conda.exe" (
    echo Miniconda is already installed.
    set CONDA_PATH=%USERPROFILE%\Miniconda3\Scripts\conda.exe
) else if exist "miniconda3\Scripts\conda.exe" (
    echo Miniconda is already installed.
    set CONDA_PATH=miniconda3\Scripts\conda.exe
) else (
    echo Miniconda is not installed, downloading...
    
    :: Download Miniconda installer
    curl -o miniconda_installer.exe https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
    
    if not exist miniconda_installer.exe (
        echo Failed to download Miniconda. Please check your internet connection or download it manually.
        exit /b 1
    )
    
    echo Installing Miniconda...
    :: Silent installation of Miniconda
    start /wait "" miniconda_installer.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%USERPROFILE%\miniconda3
    
    if exist "%USERPROFILE%\miniconda3\Scripts\conda.exe" (
        echo Miniconda installation successful.
        set CONDA_PATH=%USERPROFILE%\miniconda3\Scripts\conda.exe
    ) else (
        echo Miniconda installation failed. Please install it manually.
        exit /b 1
    )
    
    :: Delete installer
    del miniconda_installer.exe
)

:: Initialize conda
call "%USERPROFILE%\miniconda3\Scripts\activate.bat"

:: Check if environment exists
echo Checking Python environment...
"%CONDA_PATH%" env list | findstr "py311" > nul
if !errorlevel! equ 0 (
    echo Environment py311 already exists.
) else (
    echo Creating Python 3.11 environment...
    "%CONDA_PATH%" create -y -n py311 python=3.11
    if !errorlevel! neq 0 (
        echo Failed to create environment.
        exit /b 1
    )
    echo Environment created successfully.
)

:: Activate environment
echo Activating Python environment...
call "%USERPROFILE%\miniconda3\Scripts\activate.bat" py311

:: Install dependencies
echo Installing dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo Failed to install dependencies.
        exit /b 1
    )
    echo Dependencies installed successfully.
) else (
    echo requirements.txt file not found, skipping dependency installation.
)

:: Run Python script
echo Running Python script...
if exist main.py (
    python main.py
    if !errorlevel! neq 0 (
        echo Failed to run script.
        exit /b 1
    )
) else (
    echo main.py file not found.
    exit /b 1
)

echo Script execution completed.
pause 