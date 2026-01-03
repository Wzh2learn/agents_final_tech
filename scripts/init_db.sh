#!/bin/bash
# PostgreSQL 数据库初始化脚本

set -e

echo "=========================================="
echo "PostgreSQL 数据库初始化"
echo "=========================================="
echo ""

# 默认配置
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-vector_db}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-}

# 检查 psql 是否安装
if ! command -v psql &> /dev/null; then
    echo "错误: psql 未安装"
    echo "请先安装 PostgreSQL 客户端"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql-client"
    echo "  macOS: brew install postgresql"
    exit 1
fi

echo "数据库配置:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# 提示输入密码（如果未设置）
if [ -z "$DB_PASSWORD" ]; then
    read -s -p "请输入 PostgreSQL 密码: " DB_PASSWORD
    echo ""
fi

export PGPASSWORD=$DB_PASSWORD

# 1. 创建数据库
echo "1. 创建数据库..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres << EOF 2>/dev/null || true
SELECT 'CREATE DATABASE $DB_NAME' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec
\q
EOF

echo "✓ 数据库已创建"

# 2. 连接到数据库并安装 PGVector 扩展
echo ""
echo "2. 安装 PGVector 扩展..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << EOF 2>/dev/null || true
CREATE EXTENSION IF NOT EXISTS vector;
\q
EOF

echo "✓ PGVector 扩展已安装"

# 3. 创建必要的表（通过 SQLAlchemy）
echo ""
echo "3. 初始化数据库表..."
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
python3 -c "
from storage.database.shared.model import Base, engine
try:
    Base.metadata.create_all(bind=engine)
    print('✓ 数据库表已创建')
except Exception as e:
    print(f'✗ 表创建失败: {e}')
    exit(1)
"

echo ""
echo "=========================================="
echo "✓ 数据库初始化完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo "  1. 编辑 .env 文件，确认数据库配置正确"
echo "  2. 运行: ./scripts/quick_start.sh"
echo "  3. 访问: http://localhost:5000"
echo ""
