@echo off
REM ===  Course Architect - describe a course in plain English  ===
cd /d "%~dp0"

REM Load the Gemini API key from the project's .env (two folders up), if present.
set "GOOGLE_API_KEY="
if exist "..\..\.env" (
    for /f "usebackq tokens=1,* delims==" %%a in ("..\..\.env") do (
        if /i "%%a"=="GOOGLE_API_KEY" set "GOOGLE_API_KEY=%%b"
    )
)

echo.
echo  ====================================================
echo    COURSE ARCHITECT
echo    Describe the course you want, in plain English.
echo  ====================================================
echo.
echo    Examples:
echo      How to write basic Excel formulas for office staff
echo      Customer service skills for new call-centre agents
echo      Time management for busy managers
echo.
set /p "TOPIC=What course do you want?  "
if not defined TOPIC (
    echo No topic entered.
    pause
    exit /b 1
)

echo.
echo The agent is designing the outline and writing your course... please wait.
python run_demo.py --topic "%TOPIC%" --out "My Course.pptx"
if errorlevel 1 (
    echo.
    echo *** Something went wrong. Is Python installed? ***
    pause
    exit /b 1
)

echo.
echo Done. Opening "My Course.pptx" ...
start "" "My Course.pptx"
