@echo off
echo Starting Backend Service...
echo.

REM Navigate to project root and activate the existing virtual environment
cd ..
call .venv\Scripts\activate.bat

REM Navigate back to backend directory
cd backend

REM Install requirements (if needed)
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Start the backend service
echo.
echo Starting FastAPI backend...
python main.py

pause
