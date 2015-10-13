REM set this variable equal to your putty saved session name.
set serverAddr=PuttySavedSessionName

rem stop plugin on deluge deamon
plink %serverAddr% deluge-console plugin -s
plink %serverAddr% deluge-console plugin -d browseButton

rem Kill deluge if already running
taskkill /f /im deluged-debug.exe
taskkill /f /im deluge-debug.exe
taskkill /f /im deluge.exe

rem remove the release directory
rd /s /q "release\"

rem create the egg files
IF NOT %~1 == "" (
    ECHO building with custom python

    setlocal enabledelayedexpansion

    set argCount=0

    for %%x in (%*) do (
        set /A argCount+=1
        set "argVec[!argCount!]=%%~x"
        echo Arg = "%%~x"
    )

    echo Number of processed arguments: !argCount!

    for /L %%i in (1,1,!argCount!) do (
        echo Running as : !argVec[%%i]! setup.py bdist_egg
        !argVec[%%i]! setup.py bdist_egg
    )
) ELSE (
    ECHO building with default python
    python setup.py bdist_egg
)

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
for %%x in (release/dist/*.egg) do (
    pscp release/dist/%%x %serverAddr%:.config/deluge/plugins
)

rem start plugin on deluge server
plink %serverAddr% deluge-console plugin -e browseButton
plink %serverAddr% deluge-console plugin -s

rem laubch deluge in debug mode
"D:\Program Files (x86)\Deluge\deluge-debug.exe" -L debug
pause
