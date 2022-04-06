rem check-crlf.bat
rem source: https://stackoverflow.com/questions/32255747/on-windows-how-would-i-detect-the-line-ending-of-a-file

@echo off
setlocal

call type "%~1" | c:\Windows\System32\find.exe "" /v > "%~1.temp"
set size1=%~z1
rem add 2 in case the file doesn't have a trailing newline, since find will add it
set /a size1plus2=%size1%+2
call :setsize2 "%~1.temp%"

for /f %%a in ('c:\Windows\System32\findstr /R /N "^" "%~1" ^| c:\Windows\System32\find /C ":"') do set lines=%%a

if %size1plus2% equ %size2% (
    if %lines% equ 2 (
        echo File uses LF line endings!
    ) else (
        echo File uses CRLF or has no line endings!
    )
) else (
    if %size1% lss %size2% (
        echo File uses LF line endings!
    ) else (
        echo File uses CR+LF line endings!
    )
)
del "%~1.temp"
exit /b

:setsize2
set size2=%~z1
exit /b
