@echo off

SETLOCAL ENABLEDELAYEDEXPANSION

set /p QA="Constant Quality [0 (lossless) - 50 (trash)]  ?: "


for %%a in (%*) do (
      echo [100mENCODING : %%a [0m
	  set newname=%%~dpna_H265.mp4
	  bin\ffmpeg.exe -v quiet -stats -i %%a -pix_fmt yuv420p -c:a aac -b:a 128k -c:v hevc_nvenc -rc constqp -cq !QA! -preset slow -vsync 2 "!newname!" > nul
	  echo [42mFINISHED :  !newname! [0m
	  echo -----------------------------------------------------------------
)
echo.
echo.
echo [42mFINISHED ENCODING. PRESS ANY KEY TO CLOSE. [0m
pause > NUL