@echo off
setlocal
set "FOREST_BLENDER=%ProgramFiles%\Blender Foundation\Blender 5.2\blender.exe"
if not exist "%FOREST_BLENDER%" (
    for /f "delims=" %%I in ('where blender 2^>nul') do set "FOREST_BLENDER=%%I"
)
if not exist "%FOREST_BLENDER%" (
    echo Blender was not found. Install Blender 5.2 or add blender.exe to PATH.
    pause
    exit /b 1
)
set "FOREST_BLEND=%~dp0..\ForestPath_Walk_Packed.blend"
if not exist "%FOREST_BLEND%" set "FOREST_BLEND=%~dp0..\ForestPath_Local_Packed.blend"
if not exist "%FOREST_BLEND%" set "FOREST_BLEND=%~dp0scenes\ForestPath.blend"
if not exist "%FOREST_BLEND%" (
    echo ForestPath.blend was not found. See README.md.
    pause
    exit /b 1
)
if /i "%~1"=="--check" (
    echo Blender: "%FOREST_BLENDER%"
    echo Scene: "%FOREST_BLEND%"
    exit /b 0
)
start "" "%FOREST_BLENDER%" --factory-startup "%FOREST_BLEND%" --python "%~dp0tools\walk_mode.py"
endlocal
