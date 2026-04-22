#!/bin/bash
# ==============================================================
# Campus Buzz - 阿里云 FC 部署辅助脚本
# ==============================================================
# 使用方法：
#   chmod +x scripts/deploy-fc.sh
#   ./scripts/deploy-fc.sh <DATA_SERVICE_PUBLIC_URL>
#
# 示例：
#   ./scripts/deploy-fc.sh https://abc123.ngrok-free.app
# ==============================================================

set -e

# 检查参数
if [ -z "$1" ]; then
    echo "❌ 用法: $0 <DATA_SERVICE_PUBLIC_URL>"
    echo "   示例: $0 https://abc123.ngrok-free.app"
    exit 1
fi

DATA_SERVICE_URL="$1"

echo "=============================================="
echo "  Campus Buzz - 阿里云 FC 部署"
echo "=============================================="
echo ""

# 检查 Serverless Devs 是否安装
if ! command -v s &> /dev/null; then
    echo "❌ 未检测到 Serverless Devs，正在安装..."
    npm install -g @serverless-devs/s
fi

echo "✅ Serverless Devs 版本: $(s -v)"
echo ""

# ---- 第一轮部署：获取函数 URL ----
echo "🚀 第一轮部署：获取函数 HTTP 触发器 URL..."
echo ""

export DATA_SERVICE_URL="$DATA_SERVICE_URL"
export PROCESSING_FN_URL="https://placeholder.cn-beijing.fc.aliyuncs.com"
export RESULT_UPDATE_FN_URL="https://placeholder.cn-beijing.fc.aliyuncs.com"

s deploy --all

echo ""
echo "⚠️  请从上方输出中复制 3 个函数的 HTTP 触发器 URL"
echo ""
echo "然后运行第二轮部署："
echo "  export DATA_SERVICE_URL=\"$DATA_SERVICE_URL\""
echo "  export PROCESSING_FN_URL=\"<processing-function-url>\""
echo "  export RESULT_UPDATE_FN_URL=\"<result-update-function-url>\""
echo "  s deploy --all"
echo ""
echo "部署完成后，将 URL 填入 .env 文件："
echo "  SUBMISSION_EVENT_FN_URL=<submission-event-url>"
echo "  PROCESSING_FN_URL=<processing-function-url>"
echo "  RESULT_UPDATE_FN_URL=<result-update-function-url>"
