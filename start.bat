@echo off
chcp 65001 >nul
title ERP系统启动脚本

echo 🚀 启动ERP系统...

:: 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未安装，请先安装Docker
    pause
    exit /b 1
)

:: 检查docker compose是否可用
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

:: 创建静态文件目录
if not exist "static" mkdir static

:: 启动服务
echo 📦 构建并启动Docker容器...
docker compose up -d --build

:: 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 5 /nobreak >nul

:: 检查服务状态
echo 🔍 检查服务状态...
docker compose ps

echo.
echo ✅ ERP系统启动完成！
echo.
echo 📍 访问地址：
echo    - 应用地址: http://localhost:8080
echo    - 管理后台: http://localhost:8080/admin/
echo.
echo 🔑 默认管理员账号：
echo    用户名: admin
echo    密码: admin123
echo.
echo 📝 常用命令：
echo    查看日志: docker compose logs -f
echo    停止服务: docker compose down
echo    重启服务: docker compose restart
echo.

pause
