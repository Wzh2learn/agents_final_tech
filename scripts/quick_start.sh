#!/bin/bash
# 建账规则助手系统 - 快速启动脚本

set -e

echo "=========================================="
echo "建账规则助手系统 - 快速启动"
echo "=========================================="
echo ""

# 检查 Python 版本
echo "1. 检查 Python 版本..."
python3 --version || { echo "错误: 需要 Python 3.8+" ; exit 1; }

# 检查是否在项目根目录
if [ ! -f "requirements.txt" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查虚拟环境
echo "2. 检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "3. 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "4. 安装依赖..."
pip install -q -r requirements.txt

# 检查 .env 文件
echo "5. 检查环境配置..."
if [ ! -f ".env" ]; then
    echo "警告: .env 文件不存在"
    echo "从 .env.example 创建 .env 文件..."
    cp .env.example .env
    echo "请编辑 .env 文件，填写实际的数据库配置"
    echo ""
fi

# 检查数据库连接
echo "6. 检查数据库连接..."
DB_HOST=$(grep DB_HOST .env | cut -d '=' -f2)
DB_NAME=$(grep DB_NAME .env | cut -d '=' -f2)
if [ -n "$DB_HOST" ] && [ -n "$DB_NAME" ]; then
    echo "数据库配置: $DB_HOST/$DB_NAME"
else
    echo "警告: 数据库配置不完整"
fi

# 启动服务
echo ""
echo "=========================================="
echo "7. 启动服务..."
echo "=========================================="
echo ""
echo "服务地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo ""

# 设置 PYTHONPATH 并启动
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
python3 src/main.py

# 退出时取消虚拟环境
deactivate
