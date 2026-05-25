@echo off
setlocal EnableExtensions

pushd "%~dp0"

set "VERSION=%~1"
if not defined VERSION (
  echo Usage: build.bat ^<version^>
  popd
  exit /b 1
)

set "PYTHON_EXE=%PYTHON27%"
if not defined PYTHON_EXE if exist "C:\Python27\python.exe" set "PYTHON_EXE=C:\Python27\python.exe"
if not defined PYTHON_EXE if exist "C:\Python27-32\python.exe" set "PYTHON_EXE=C:\Python27-32\python.exe"

if not defined PYTHON_EXE (
  echo Set PYTHON27 to a Python 2.7 executable.
  popd
  exit /b 1
)

"%PYTHON_EXE%" pack_mtmod.py "%VERSION%"
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
