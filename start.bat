@echo off
python check_dependencies.py
if errorlevel 1 exit /b %errorlevel%
@echo off
python .\\main\\main.py
