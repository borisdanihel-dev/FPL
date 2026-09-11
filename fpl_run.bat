@echo off
REM ---------------------------------------------------------------------------
REM fpl_run.bat - sync the FPL API, then write a dated analysis report.
REM Put this next to fpl_sync.py and fpl_edge.py.
REM Schedule daily so price_history accumulates.
REM ---------------------------------------------------------------------------

cd /d "%~dp0"

REM UTF-8 everywhere: player names contain accents that cp1252 cannot encode
set PYTHONIOENCODING=utf-8
chcp 65001 >nul 2>&1

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set STAMP=%%i
if not exist reports mkdir reports
set LOG=reports\run_%STAMP%.log

echo ==== run %STAMP% ==== > "%LOG%"
echo working dir: %CD% >> "%LOG%"

REM find python even when Task Scheduler gives a bare PATH
where python >nul 2>&1 && set PY=python
if not defined PY where py >nul 2>&1 && set PY=py
if not defined PY (
    echo PYTHON NOT FOUND ON PATH >> "%LOG%"
    echo PYTHON NOT FOUND ON PATH
    exit /b 1
)
echo using: %PY% >> "%LOG%"

echo running tests ...
set TESTS_OK=1
%PY% test_fpl.py >> "%LOG%" 2>&1
if errorlevel 1 (
    set TESTS_OK=0
    echo TESTS FAILED - see %LOG% >> "%LOG%"
    echo TESTS FAILED - see %LOG%
)

echo syncing FPL API ...
%PY% fpl_sync.py >> "%LOG%" 2>&1
if errorlevel 1 echo SYNC FAILED - continuing with existing data >> "%LOG%"

REM Record BOTH models so the calibration table is a like-for-like comparison.
REM The deadline guard refuses to write once a gameweek has started, so this
REM schedule must complete before each Friday/Saturday deadline.
REM A red suite must not write point-in-time forecasts. Those rows freeze at
REM the deadline and cannot be regenerated, so one bad set permanently
REM contaminates the calibration table that the wildcard decision rests on.
REM Sync and the report still run - their output is regenerable, this is not.
if "%TESTS_OK%"=="1" (
    echo recording forecasts for next GW ...
    %PY% fpl_edge.py --record --source own >> "%LOG%" 2>&1
    %PY% fpl_edge.py --record --source xg  >> "%LOG%" 2>&1
) else (
    echo SKIPPED --record: test suite is red, no forecasts written >> "%LOG%"
    echo SKIPPED --record: test suite is red, no forecasts written
)

echo building report ...
%PY% fpl_edge.py --diff --out "reports\fpl_%STAMP%.txt" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo EDGE FAILED >> "%LOG%"
    exit /b 1
)

echo Done. Report: reports\fpl_%STAMP%.txt
echo Done >> "%LOG%"
