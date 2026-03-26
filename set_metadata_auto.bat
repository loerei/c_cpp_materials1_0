@echo off
setlocal

set "TARGET_DIR=%~1"
if not defined TARGET_DIR set "TARGET_DIR=%~dp0"
set "TARGET_DIR=%TARGET_DIR:"=%"
for %%I in ("%TARGET_DIR%\.") do set "TARGET_DIR=%%~fI"

echo Target: %TARGET_DIR%
python "%~dp0set_metadata_auto.py" "%TARGET_DIR%"

if errorlevel 1 (
  echo Failed.
  exit /b 1
)

echo Success.
exit /b 0
