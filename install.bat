@echo off
echo ============================================================
echo  HealthGuard AI - Dependency Installer
echo  Supports Python 3.10 to 3.13
echo ============================================================
echo.

echo [1/4] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo [2/4] Installing numpy and pandas (pre-built binaries)...
pip install "numpy>=2.1.0" "pandas>=2.2.0" --only-binary :all: --quiet
if %errorlevel% neq 0 (
    pip install numpy pandas --only-binary :all: --quiet
)

echo [3/4] Installing IBM watsonx-ai SDK (latest)...
pip install "ibm-watsonx-ai>=1.5.0" --prefer-binary --no-deps --quiet
pip install certifi httpx ibm-cos-sdk lomond packaging requests tabulate urllib3 cachetools --prefer-binary --quiet

echo [4/4] Installing Flask and remaining dependencies...
pip install Flask==3.0.3 Flask-SQLAlchemy==3.1.1 Flask-Login==0.6.3 Flask-WTF==1.2.1 Flask-Bcrypt==1.0.1 Flask-Migrate==4.0.7 WTForms==3.1.2 python-dotenv==1.0.1 "Pillow>=10.0.0" python-dateutil==2.9.0 email-validator==2.1.1 SQLAlchemy==2.0.31 Werkzeug==3.0.3 PyPDF2==3.0.1 --prefer-binary --quiet

echo.
echo ============================================================
echo  Installation complete!
echo  Run the app:   python app.py
echo  Open browser:  http://localhost:5000
echo ============================================================
pause
