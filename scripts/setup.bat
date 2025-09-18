@echo off
echo Setting up JDDB Backend...
cd backend

echo Creating Python virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Copying environment file...
copy .env.example .env

echo Initializing database...
python scripts\init_db.py

echo Creating sample data...
python scripts\sample_data.py

echo Setup complete! Run server.bat to start the backend.
pause
