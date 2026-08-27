@echo off
rem ==============================================================================
rem Cog: Context on Git - Windows Command Prompt CLI Entry Point
rem Usage: .\Cog\Ctx.cmd [COMMAND] [OPTIONS]
rem ==============================================================================

setlocal enabledelayedexpansion

rem Determine the directory where this script resides
set "SCRIPT_DIR=%~dp0"

rem Search for python / python3 binary on PATH
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PYTHON_BIN=python"
    goto :RUN
)

where python3 >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PYTHON_BIN=python3"
    goto :RUN
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PYTHON_BIN=py -3"
    goto :RUN
)

echo [Cog ERROR] Python was not found on your PATH. >&2
exit /b 1

:RUN
%PYTHON_BIN% "%SCRIPT_DIR%core\engine.py" %*
exit /b %ERRORLEVEL%