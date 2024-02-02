@echo off

:: Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.x and try again.
    exit /b 1
)

:: Create a virtual environment
python -m venv rooster-venv

:: Activate the virtual environment
rooster-venv\Scripts\activate

:: Install dependencies from requirements.txt
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo requirements.txt not found. Please create the file with your project dependencies.
    exit /b 1
)

echo Virtual environment created and activated. Dependencies installed.
