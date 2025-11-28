#!/bin/bash
# すべてのサービスを起動するスクリプト

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Multi-Agent CLI Gateway MCP 起動スクリプト"
echo "=========================================="
echo ""

# ホストラッパーの仮想環境を確認・作成
if [ ! -d "host_wrappers/.venv" ]; then
    echo "ホストラッパーの仮想環境を作成中..."
    cd host_wrappers
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
    cd ..
    echo "✓ 仮想環境の作成が完了しました"
fi

# PIDファイルのディレクトリを作成
mkdir -p .pids

# Codexラッパーの起動
echo "Codexラッパーを起動中..."
cd host_wrappers
source .venv/bin/activate
nohup python codex_wrapper.py > ../.pids/codex_wrapper.log 2>&1 &
CODEX_PID=$!
echo $CODEX_PID > ../.pids/codex_wrapper.pid
cd ..
sleep 2

# Codexラッパーの起動確認
if ps -p $CODEX_PID > /dev/null; then
    echo "✓ Codexラッパーが起動しました (PID: $CODEX_PID, ポート: 9001)"
else
    echo "✗ Codexラッパーの起動に失敗しました"
    exit 1
fi

# Claudeラッパーの起動
echo "Claudeラッパーを起動中..."
cd host_wrappers
source .venv/bin/activate
nohup python claude_wrapper.py > ../.pids/claude_wrapper.log 2>&1 &
CLAUDE_PID=$!
echo $CLAUDE_PID > ../.pids/claude_wrapper.pid
cd ..
sleep 2

# Claudeラッパーの起動確認
if ps -p $CLAUDE_PID > /dev/null; then
    echo "✓ Claudeラッパーが起動しました (PID: $CLAUDE_PID, ポート: 9002)"
else
    echo "✗ Claudeラッパーの起動に失敗しました"
    exit 1
fi

# Dockerコンテナの起動
echo "Dockerコンテナを起動中..."
cd multi-agent-cli-gateway-mcp-server
docker compose up -d
cd ..
sleep 3

# Dockerコンテナの起動確認
if docker ps --filter "name=multi-agent-cli-gateway-mcp" --format "{{.Names}}" | grep -q "multi-agent-cli-gateway-mcp"; then
    echo "✓ Dockerコンテナが起動しました (コンテナ名: multi-agent-cli-gateway-mcp, ポート: 8080)"
else
    echo "✗ Dockerコンテナの起動に失敗しました"
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ すべてのサービスが起動しました！"
echo "=========================================="
echo ""
echo "サービス状態:"
echo "  - Codexラッパー:    http://localhost:9001"
echo "  - Claudeラッパー:   http://localhost:9002"
echo "  - MCPブリッジ:      http://localhost:8080"
echo ""
echo "ログファイル:"
echo "  - Codexラッパー:    .pids/codex_wrapper.log"
echo "  - Claudeラッパー:   .pids/claude_wrapper.log"
echo ""
echo "停止するには: ./stop.sh"
echo ""

