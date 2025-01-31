@ECHO ON
python3 -m PyInstaller --clean -y -n MassieVFX_OpenMediaEncoder --onefile --noconsole --icon=icon.ico --add-data ./ui:ui --add-data icon.ico;. --add-data ffmpeg.exe;.  MassieVFX_OpenMediaEncoder.py
pause