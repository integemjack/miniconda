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
echo Initializing conda...
if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
    call "%USERPROFILE%\miniconda3\Scripts\activate.bat"
) else (
    echo activate.bat not found, trying conda init...
    call "%CONDA_PATH%" init cmd.exe
    echo Please restart this script after conda initialization.
    pause
    exit /b 0
)

:: Check if environment exists
echo Checking Python environment...
echo Listing all conda environments...
"%CONDA_PATH%" env list

"%CONDA_PATH%" env list | findstr "pydrone_balloon_log_analyze" > nul 2>&1
if !errorlevel! equ 0 (
    echo Environment pydrone_balloon_log_analyze already exists.
) else (
    echo Environment pydrone_balloon_log_analyze not found, creating new environment...
    echo Creating Python 3.11 environment...
    "%CONDA_PATH%" create -y -n pydrone_balloon_log_analyze python=3.11
    if !errorlevel! neq 0 (
        echo Failed to create environment. Trying alternative method...
        echo Initializing conda first...
        call "%CONDA_PATH%" init cmd.exe
        "%CONDA_PATH%" create -y -n pydrone_balloon_log_analyze python=3.11
        if !errorlevel! neq 0 (
            echo Failed to create environment after initialization.
            exit /b 1
        )
    )
    echo Environment created successfully.
)

:: Activate environment
echo Activating Python environment...
echo Available environments:
"%CONDA_PATH%" env list

echo Attempting to activate pydrone_balloon_log_analyze environment...
call "%USERPROFILE%\miniconda3\Scripts\activate.bat" pydrone_balloon_log_analyze
if !errorlevel! neq 0 (
    echo Failed to activate with activate.bat, trying conda activate...
    call "%CONDA_PATH%" activate pydrone_balloon_log_analyze
    if !errorlevel! neq 0 (
        echo Failed to activate environment. Please check if pydrone_balloon_log_analyze exists.
        echo Creating environment again...
        "%CONDA_PATH%" create -y -n pydrone_balloon_log_analyze python=3.11
        call "%CONDA_PATH%" activate pydrone_balloon_log_analyze
        if !errorlevel! neq 0 (
            echo Failed to create and activate environment.
            exit /b 1
        )
    )
)

:: Verify environment activation
echo Verifying environment activation...
python -c "import sys; print('Python path:', sys.executable)" 2>nul
if !errorlevel! neq 0 (
    echo Error: Python is not accessible. Environment activation may have failed.
    exit /b 1
)

:: Check if we're in the correct environment
for /f "tokens=*" %%i in ('python -c "import sys; import os; print(os.path.basename(os.path.dirname(sys.executable)))" 2^>nul') do set CURRENT_ENV=%%i
if /i "!CURRENT_ENV!" neq "pydrone_balloon_log_analyze" (
    echo Warning: Current environment appears to be "!CURRENT_ENV!" instead of "pydrone_balloon_log_analyze"
    echo Continuing anyway...
) else (
    echo Environment activation verified: !CURRENT_ENV!
)

python -c "import sys; print('Python version:', sys.version.split()[0])"
echo Environment is ready!

:: Install dependencies
echo Installing dependencies...
if exist requirements.txt (
    echo Upgrading pip first...
    python -m pip install --upgrade pip setuptools wheel
    
    echo Installing requirements...
    pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo Failed to install dependencies from requirements.txt, trying with updated versions...
        pip install "numpy>=1.24.3" "pandas>=2.0.3" "matplotlib>=3.7.2" "bleak>=0.20.2"
        if !errorlevel! neq 0 (
            echo Failed to install dependencies.
            exit /b 1
        )
    )
    echo Dependencies installed successfully.
) else (
    echo requirements.txt file not found, installing basic dependencies...
    echo Upgrading pip first...
    python -m pip install --upgrade pip setuptools wheel
    pip install "numpy>=1.24.3" "pandas>=2.0.3" "matplotlib>=3.7.2" "bleak>=0.20.2"
    if !errorlevel! neq 0 (
        echo Failed to install basic dependencies.
        exit /b 1
    )
)

:: Set main script to run
set MAIN_SCRIPT=main.py
if "%1"=="simple" set MAIN_SCRIPT=main_simple.py
if not exist %MAIN_SCRIPT% (
    if exist main_simple.py (
        set MAIN_SCRIPT=main_simple.py
        echo Using main_simple.py instead...
    )
)

:: Run Python script
echo Running Python script: %MAIN_SCRIPT%
if exist %MAIN_SCRIPT% (
    python %MAIN_SCRIPT%
    if !errorlevel! neq 0 (
        echo Failed to run script.
        exit /b 1
    )
) else (
    echo No Python script found. Please create main.py or main_simple.py
    exit /b 1
)

echo Script execution completed.
pause 