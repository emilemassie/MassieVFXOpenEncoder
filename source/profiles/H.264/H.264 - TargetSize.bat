@echo off

SETLOCAL ENABLEDELAYEDEXPANSION

for %%a in (%*) do (
	echo [100mENCODING : %%a [0m
	set /p target_size="TARGET SIZE (MB):"
	REM set target_size=30


	bin\ffprobe.exe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 %%a>tmp

	set /p cliptime=<tmp
	del tmp
	set /A bitrate=target_size*7800/cliptime-128
	set newname=%%~dpna_H264.mp4
	bin\ffmpeg.exe -v quiet -stats -i %%a -pix_fmt yuv420p -c:v h264_nvenc -rc:v cbr_ld_hq -b:v !bitrate!k -vsync 2 -c:a aac -b:a 128k "!newname!" > nul
	echo [42mFINISHED :  !newname! [0m
	echo -----------------------------------------------------------------
)
echo.
echo.
echo [42mFINISHED ENCODING. PRESS ANY KEY TO CLOSE. [0m
pause > NUL