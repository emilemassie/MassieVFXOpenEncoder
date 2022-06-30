@echo off

SETLOCAL ENABLEDELAYEDEXPANSION

for %%a in (%*) do (
      echo [100mENCODING : %%a [0m
	  set newname=%%~dpna_AUDIO.wav
	  %~dp0bin\ffmpeg.exe -v quiet -stats -i %%a "!newname!" > nul
	  echo [42mFINISHED :  !newname! [0m
	  echo -----------------------------------------------------------------
)
echo.
echo.
echo [42mFINISHED ENCODING. PRESS ANY KEY TO CLOSE. [0m
pause > NUL

