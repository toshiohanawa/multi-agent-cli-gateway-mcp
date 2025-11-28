#!/bin/bash
# ホストラッパー起動スクリプト
# docker-compose.ymlから呼び出されるか、直接実行可能

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# PIDファイルのディレクトリを作成
mkdir -p .pids

# ホストラッパーの仮想環境を確認・作成
if [ ! -d "host_wrappers/.venv" ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ホストラッパーの仮想環境を作成中..."
    cd host_wrappers
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
    cd ..
fi

# Codexラッパーの起動（既に起動している場合はスキップ）
if [ -f ".pids/codex_wrapper.pid" ]; then
    CODEX_PID=$(cat .pids/codex_wrapper.pid)
    if ps -p $CODEX_PID > /dev/null 2>&1; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] Codexラッパーは既に起動しています (PID: $CODEX_PID)"
    else
        rm -f .pids/codex_wrapper.pid
    fi
fi

if [ ! -f ".pids/codex_wrapper.pid" ] || ! ps -p $(cat .pids/codex_wrapper.pid) > /dev/null 2>&1; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Codexラッパーを起動中..."
    cd host_wrappers
    source .venv/bin/activate
    nohup python codex_wrapper.py > ../.pids/codex_wrapper.log 2>&1 &
    CODEX_PID=$!
    echo $CODEX_PID > ../.pids/codex_wrapper.pid
    cd ..
    sleep 2
    
    if ps -p $CODEX_PID > /dev/null; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✓ Codexラッパーが起動しました (PID: $CODEX_PID, ポート: 9001)"
    else
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✗ Codexラッパーの起動に失敗しました"
        exit 1
    fi
fi

# Claudeラッパーの起動（既に起動している場合はスキップ）
if [ -f ".pids/claude_wrapper.pid" ]; then
    CLAUDE_PID=$(cat .pids/claude_wrapper.pid)
    if ps -p $CLAUDE_PID > /dev/null 2>&1; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] Claudeラッパーは既に起動しています (PID: $CLAUDE_PID)"
    else
        rm -f .pids/claude_wrapper.pid
    fi
fi

if [ ! -f ".pids/claude_wrapper.pid" ] || ! ps -p $(cat .pids/claude_wrapper.pid) > /dev/null 2>&1; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Claudeラッパーを起動中..."
    cd host_wrappers
    source .venv/bin/activate
    nohup python claude_wrapper.py > ../.pids/claude_wrapper.log 2>&1 &
    CLAUDE_PID=$!
    echo $CLAUDE_PID > ../.pids/claude_wrapper.pid
    cd ..
    sleep 2
    
    if ps -p $CLAUDE_PID > /dev/null; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✓ Claudeラッパーが起動しました (PID: $CLAUDE_PID, ポート: 9002)"
    else
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✗ Claudeラッパーの起動に失敗しました"
        exit 1
    fi
fi

echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✓ ホストラッパーの起動が完了しました"

