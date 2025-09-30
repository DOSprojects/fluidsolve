@ECHO OFF
pushd %~dp0
REM Command file for Sphinx documentation

REM Set variables
if "%SPHINXBUILD%" == "" (
    set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=source
set BUILDDIR=build

REM Check if make is available
where make >NUL 2>NUL
if %ERRORLEVEL% EQU 0 (
    REM Use GNU Make and your Makefile for known targets
    if "%1" == "html" (
        make html
        goto end
    )
    if "%1" == "html-nowarn" (
        make html-nowarn
        goto end
    )
    if "%1" == "html-verbose" (
        make html-verbose
        goto end
    )
    if "%1" == "clean" (
        make clean
        goto end
    )
)

REM Fallback to Sphinx’s built-in targets
if "%1" == "" goto help
%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
    echo.
    echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
    echo.installed, then set the SPHINXBUILD environment variable to point
    echo.to the full path of the 'sphinx-build' executable. Alternatively you
    echo.may add the Sphinx directory to PATH.
    echo.
    echo.If you don't have Sphinx installed, grab it from
    echo.http://sphinx-doc.org/
    exit /b 1
)
%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end
:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
:end
popd