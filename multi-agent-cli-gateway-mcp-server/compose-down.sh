#!/bin/bash
# Docker Compose down のラッパースクリプト
# Dockerコンテナを停止してからホストラッパーも停止します

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

# Docker Composeを停止
echo "Docker Composeを停止中..."
docker compose down "$@"

# ホストラッパーを停止
echo ""
echo "ホストラッパーを停止中..."
if [ -f "$PROJECT_ROOT/.pids/codex_wrapper.pid" ]; then
    CODEX_PID=$(cat "$PROJECT_ROOT/.pids/codex_wrapper.pid")
    if ps -p $CODEX_PID > /dev/null 2>&1; then
        kill $CODEX_PID 2>/dev/null || true
        rm -f "$PROJECT_ROOT/.pids/codex_wrapper.pid"
        echo "✓ Codexラッパーを停止しました"
    fi
fi

if [ -f "$PROJECT_ROOT/.pids/claude_wrapper.pid" ]; then
    CLAUDE_PID=$(cat "$PROJECT_ROOT/.pids/claude_wrapper.pid")
    if ps -p $CLAUDE_PID > /dev/null 2>&1; then
        kill $CLAUDE_PID 2>/dev/null || true
        rm -f "$PROJECT_ROOT/.pids/claude_wrapper.pid"
        echo "✓ Claudeラッパーを停止しました"
    fi
fi

echo ""
echo "✓ すべてのサービスを停止しました"

