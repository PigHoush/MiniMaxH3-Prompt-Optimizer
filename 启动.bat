@echo off
set "PATH=C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem;%~dp0python;%~dp0python\Library\bin;%PATH%"
chcp 65001 >nul
title MiniMax H3 提示词优化（独立环境）
netstat -ano | findstr ":8199" | findstr "LISTENING" >nul
if not errorlevel 1 goto already
cd /d "%~dp0ComfyUI"
"%~dp0python\python.exe" main.py --port 8199 --auto-launch
echo.
echo [已退出] 关闭窗口将停止服务，重新双击本脚本即可再启动。
pause >nul
exit /b 0
:already
echo [提示] 端口 8199 已在运行，直接打开页面。
start "" http://127.0.0.1:8199/
timeout /t 3 >nul
exit /b 0
