@echo off

SETLOCAL ENABLEDELAYEDEXPANSION

for %%a in (%*) do (
      echo [100mENCODING : %%a [0m
	  set newname=%%~dpna_Prores4444+Alpha.mov
	  bin\ffmpeg.exe -v quiet -stats -i %%a -pix_fmt yuv444p10  -c:v prores_ks -profile:v 4 -vendor ap10 -an "!newname!" > nul
	  echo [42mFINISHED :  !newname! [0m
	  echo -----------------------------------------------------------------
)
echo.
echo.
echo [42mFINISHED ENCODING. PRESS ANY KEY TO CLOSE. [0m
pause > NUL