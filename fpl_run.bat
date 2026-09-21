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

REM Stamp by the UTC date, the same date price_history uses, so a catch-up run
REM after midnight is filed under the day whose price sample it wrote.
for /f %%i in ('powershell -NoProfile -Command "Get-Date ([DateTime]::UtcNow) -Format yyyy-MM-dd"') do set STAMP=%%i
if not exist reports mkdir reports
set LOG=reports\run_%STAMP%.log

REM Append: a second run on the same date must not erase the first run's log.
echo ==== run %STAMP% UTC, started %DATE% %TIME% local ==== >> "%LOG%"
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
    %PY% fpl_edge.py --record --source minutes >> "%LOG%" 2>&1
    %PY% fpl_edge.py --record --source bottomup >> "%LOG%" 2>&1
) else (
    echo SKIPPED --record: test suite is red, no forecasts written >> "%LOG%"
    echo SKIPPED --record: test suite is red, no forecasts written
)

echo building report ...
set EDGE_OK=1
%PY% fpl_edge.py --diff --out "reports\fpl_%STAMP%.txt" >> "%LOG%" 2>&1
if errorlevel 1 (
    set EDGE_OK=0
    echo EDGE FAILED >> "%LOG%"
    echo EDGE FAILED - see %LOG%
)

REM Archive the dated export, back up fpl.sqlite (last 7), ship the export,
REM projection_log.csv, this run log and the report to G:\My Drive\FPL.
REM Every copy logs its own result line. A failed copy is not fatal but must be
REM visible; with G: unmounted the files wait in outbox\ and go up next run.
REM fpl.sqlite is never shipped.
echo archiving, backing up, shipping ...
%PY% fpl_ship.py --stamp %STAMP% >> "%LOG%" 2>&1
if errorlevel 1 (
    echo SHIP FAILED - see %LOG% >> "%LOG%"
    echo SHIP FAILED - see %LOG%
)

if "%EDGE_OK%"=="0" exit /b 1
echo Done. Report: reports\fpl_%STAMP%.txt
echo Done >> "%LOG%"
