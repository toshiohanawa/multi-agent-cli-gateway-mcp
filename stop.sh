#!/bin/bash
# すべてのサービスを停止するスクリプト

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Multi-Agent CLI Gateway MCP 停止スクリプト"
echo "=========================================="
echo ""

# Dockerコンテナの停止
echo "Dockerコンテナを停止中..."
cd multi-agent-cli-gateway-mcp-server
docker compose down
cd ..
echo "✓ Dockerコンテナを停止しました"

# Codexラッパーの停止
if [ -f ".pids/codex_wrapper.pid" ]; then
    CODEX_PID=$(cat .pids/codex_wrapper.pid)
    if ps -p $CODEX_PID > /dev/null 2>&1; then
        echo "Codexラッパーを停止中... (PID: $CODEX_PID)"
        kill $CODEX_PID
        sleep 1
        if ps -p $CODEX_PID > /dev/null 2>&1; then
            kill -9 $CODEX_PID
        fi
        echo "✓ Codexラッパーを停止しました"
    else
        echo "Codexラッパーは既に停止しています"
    fi
    rm -f .pids/codex_wrapper.pid
else
    echo "CodexラッパーのPIDファイルが見つかりません"
fi

# Claudeラッパーの停止
if [ -f ".pids/claude_wrapper.pid" ]; then
    CLAUDE_PID=$(cat .pids/claude_wrapper.pid)
    if ps -p $CLAUDE_PID > /dev/null 2>&1; then
        echo "Claudeラッパーを停止中... (PID: $CLAUDE_PID)"
        kill $CLAUDE_PID
        sleep 1
        if ps -p $CLAUDE_PID > /dev/null 2>&1; then
            kill -9 $CLAUDE_PID
        fi
        echo "✓ Claudeラッパーを停止しました"
    else
        echo "Claudeラッパーは既に停止しています"
    fi
    rm -f .pids/claude_wrapper.pid
else
    echo "ClaudeラッパーのPIDファイルが見つかりません"
fi

# ポートを使用しているプロセスを確認して停止（フォールバック）
for port in 9001 9002; do
    PID=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$PID" ]; then
        echo "ポート $port を使用しているプロセスを停止中... (PID: $PID)"
        kill $PID 2>/dev/null || true
        sleep 1
        if ps -p $PID > /dev/null 2>&1; then
            kill -9 $PID 2>/dev/null || true
        fi
    fi
done

echo ""
echo "=========================================="
echo "✓ すべてのサービスを停止しました"
echo "=========================================="
echo ""

