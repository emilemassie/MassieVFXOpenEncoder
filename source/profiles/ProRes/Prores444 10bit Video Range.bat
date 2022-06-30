@echo off

SETLOCAL ENABLEDELAYEDEXPANSION

for %%a in (%*) do (
      echo [100mENCODING : %%a [0m
	  set newname=%%~dpna_Prores444[VIDEO].mov
	  bin\ffmpeg.exe -v quiet -stats -i %%a -map_metadata 0 -pix_fmt yuv422p10le -c:a copy -c:v prores_ks -profile:v 4 "!newname!" > nul
	  echo [42mFINISHED :  !newname! [0m
	  echo -----------------------------------------------------------------
)
echo.
echo.
echo [42mFINISHED ENCODING. PRESS ANY KEY TO CLOSE. [0m
pause > NUL