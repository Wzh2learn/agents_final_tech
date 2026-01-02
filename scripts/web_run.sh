#!/bin/bash

# Web 服务启动脚本
# 用途: 启动建账规则助手的可视化 Web 界面

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 解析参数
MODE="web"
PORT=5000
DEBUG=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -p, --port PORT   指定端口号 (默认: 5000)"
            echo "  -d, --debug       启用调试模式"
            echo "  -h, --help        显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                    # 使用默认配置启动"
            echo "  $0 -p 8000           # 在端口 8000 启动"
            echo "  $0 -p 8000 -d       # 在端口 8000 启动并启用调试模式"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}未知参数: $1${NC}"
            echo "使用 -h 或 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 进入项目根目录
cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   建账规则助手 - Web 服务${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✓ 项目目录: $PROJECT_ROOT${NC}"
echo -e "${GREEN}✓ 服务模式: Web 界面${NC}"
echo -e "${GREEN}✓ 监听端口: $PORT${NC}"
echo -e "${GREEN}✓ 调试模式: $DEBUG${NC}"
echo ""

# 检查必要的文件
if [ ! -f "src/web/app.py" ]; then
    echo -e "${YELLOW}警告: src/web/app.py 不存在${NC}"
    exit 1
fi

# 设置环境变量
export WEB_PORT=$PORT
export WEB_DEBUG=$DEBUG
export PYTHONPATH="${PYTHONPATH}:$PROJECT_ROOT/src"

# 检查依赖
echo -e "${BLUE}检查依赖...${NC}"
if ! python -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}Flask 未安装，正在安装...${NC}"
    pip install flask
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   启动 Web 服务${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}📱 访问地址: http://localhost:$PORT${NC}"
echo -e "${GREEN}🎯 角色选择: a=产品经理, b=技术开发, c=销售运营, d=默认工程师${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
echo ""

# 启动 Flask 应用
python src/web/app.py
