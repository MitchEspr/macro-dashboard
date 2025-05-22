@echo off
setlocal enabledelayedexpansion

(
echo Directory Structure:
for /r %%d in (.) do (
    set "dir=%%d"
    rem --- Updated exclusion list ---
    echo !dir! | findstr /i /v "node_modules obj bin venv .venv env .env __pycache__ dist build .git .vscode" >nul
    if not errorlevel 1 (
        if exist "%%d" (
            pushd "%%d"
            dir /b /a-d 2>nul
            popd
        )
    )
)

echo.
echo File Contents:
for /r %%d in (.) do (
    set "dir=%%d"
    rem --- Updated exclusion list ---
    echo !dir! | findstr /i /v "node_modules obj bin venv .venv env .env __pycache__ dist build .git .vscode" >nul
    if not errorlevel 1 (
        if exist "%%d" (
            pushd "%%d"
            rem --- Updated file types list ---
            rem Removed *.cs, *.py.bak. Added *.yaml. Kept frontend files like *.tsx, *.ts, *.css, *.html.
            for %%i in (*.py *.md *.yml *.yaml *.json *.sh *.toml *.css *.tsx *.ts *.html *.bat *.ps1) do (
                if exist "%%i" (
                    echo.
                    echo === %%~fi ===
                    echo.
                    type "%%i" 2>nul
                )
            )
            popd
        )
    )
)

if exist Dockerfile (
    echo.
    echo === Dockerfile ===
    echo.
    type Dockerfile
)
) > full_codebase.txt

echo Full codebase snapshot created in full_codebase.txt
endlocal