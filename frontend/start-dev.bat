@ECHO OFF
SET PATH=C:\Program Files\nodejs;%PATH%
cd /d "%~dp0"
npx vite --host --port %PORT%
