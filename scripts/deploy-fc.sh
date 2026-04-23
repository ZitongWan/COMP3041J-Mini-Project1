#!/bin/bash
# ==============================================================
# Campus Buzz - Alibaba Cloud FC deployment helper
# ==============================================================
# Usage:
#   chmod +x scripts/deploy-fc.sh
#   ./scripts/deploy-fc.sh <DATA_SERVICE_PUBLIC_URL>
#
# Example:
#   ./scripts/deploy-fc.sh https://abc123.ngrok-free.app
# ==============================================================

set -e

# Make sure the required argument is provided
if [ -z "$1" ]; then
    echo "❌ Usage: $0 <DATA_SERVICE_PUBLIC_URL>"
    echo "   Example: $0 https://abc123.ngrok-free.app"
    exit 1
fi

DATA_SERVICE_URL="$1"

echo "=============================================="
echo "  Campus Buzz - Alibaba Cloud FC Deployment"
echo "=============================================="
echo ""

# Check whether Serverless Devs is installed
if ! command -v s &> /dev/null; then
    echo "❌ Serverless Devs not found. Installing now..."
    npm install -g @serverless-devs/s
fi

echo "✅ Serverless Devs version: $(s -v)"
echo ""

# ---- First deployment pass: get function URLs ----
echo "🚀 First deployment pass: getting function HTTP trigger URLs..."
echo ""

export DATA_SERVICE_URL="$DATA_SERVICE_URL"
export PROCESSING_FN_URL="https://placeholder.cn-beijing.fc.aliyuncs.com"
export RESULT_UPDATE_FN_URL="https://placeholder.cn-beijing.fc.aliyuncs.com"

s deploy --all

echo ""
echo "⚠️  Copy the HTTP trigger URLs for all 3 functions from the output above."
echo ""
echo "Then run the second deployment pass:"
echo "  export DATA_SERVICE_URL=\"$DATA_SERVICE_URL\""
echo "  export PROCESSING_FN_URL=\"<processing-function-url>\""
echo "  export RESULT_UPDATE_FN_URL=\"<result-update-function-url>\""
echo "  s deploy --all"
echo ""
echo "After deployment, add the URLs to your .env file:"
echo "  SUBMISSION_EVENT_FN_URL=<submission-event-url>"
echo "  PROCESSING_FN_URL=<processing-function-url>"
echo "  RESULT_UPDATE_FN_URL=<result-update-function-url>"
