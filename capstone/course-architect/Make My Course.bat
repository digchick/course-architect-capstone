@echo off
REM ===  Course Architect - one-click course builder  ===
REM Edit MY_COURSE.md first, then double-click this file.
cd /d "%~dp0"

REM Load the Gemini API key from the project's .env (two folders up), if present.
set "GOOGLE_API_KEY="
if exist "..\..\.env" (
    for /f "usebackq tokens=1,* delims==" %%a in ("..\..\.env") do (
        if /i "%%a"=="GOOGLE_API_KEY" set "GOOGLE_API_KEY=%%b"
    )
)

if defined GOOGLE_API_KEY (
    echo Using Gemini to write your course...
) else (
    echo No API key found - using the built-in offline writer.
)

echo Building your course from MY_COURSE.md ...
python run_demo.py --outline "MY_COURSE.md" --out "My Course.pptx"
if errorlevel 1 (
    echo.
    echo *** Something went wrong. Is Python installed? ***
    echo.
    pause
    exit /b 1
)

echo.
echo Done. Opening "My Course.pptx" ...
start "" "My Course.pptx"
