@echo off

SETLOCAL ENABLEDELAYEDEXPANSION

for %%a in (%*) do (
      echo [100mENCODING : %%a [0m
	  set newname=%%~dpna_H264.mp4
	  %~dp0bin\ffmpeg.exe -i %%a -pix_fmt yuv420p -c:a aac -b:a 320k -c:v libx264 -preset veryslow -vsync 2 "!newname!" > nul
	  echo [42mFINISHED :  !newname! [0m
	  echo -----------------------------------------------------------------
)
echo.
echo.
echo [42mFINISHED ENCODING. PRESS ANY KEY TO CLOSE. [0m
pause > NUL