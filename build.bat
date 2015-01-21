rem Kill deluge if already running
taskkill /f /im deluged-debug.exe
taskkill /f /im deluge-debug.exe
taskkill /f /im deluge.exe

rem remove the release directory
rd /s /q "release\"

rem create the egg files
python setup.py bdist_egg

rem copy to the release directory
md "release"
XCOPY  /y /E  "dist" "release\dist\"
XCOPY  /y /E "browsebutton.egg-info" "release\browsebutton.egg-info\"
XCOPY  /y /E "build" "release\build\"

rem remove origional files from root dir
rmdir /s /q "dist\"
rmdir /s /q "browsebutton.egg-info\"
rmdir /s /q "build\"

rem copy egg to deluge dir
copy release\dist\* %APPDATA%\deluge\plugins

rem copy to plugins dir
copy release\dist\* "D:\Program Files (x86)\Deluge\deluge-1.3.11-py2.7.egg\deluge\plugins"

rem copy plugin to server
call MYFTP.bat release/dist/*.egg

rem laubch deluge in debug mode
"D:\Program Files (x86)\Deluge\deluge-debug.exe" -L debug
pause
