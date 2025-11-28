#!/bin/bash
# Docker Compose up のラッパースクリプト
# ホストラッパーを自動的に起動してからDockerコンテナを起動します

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

# ホストラッパーを起動
echo "ホストラッパーを起動中..."
bash "$PROJECT_ROOT/mcp-server/start-host-wrappers.sh"

# Docker Composeを起動
echo ""
echo "Docker Composeを起動中..."
docker compose up -d "$@"

echo ""
echo "✓ Docker Composeが起動しました"
echo ""
echo "サービス状態:"
echo "  - Codexラッパー:    http://localhost:9001"
echo "  - Claudeラッパー:   http://localhost:9002"
echo "  - MCPブリッジ:      http://localhost:8080"
echo ""
echo "ログを確認: docker compose logs -f"
echo "停止するには: docker compose down"

