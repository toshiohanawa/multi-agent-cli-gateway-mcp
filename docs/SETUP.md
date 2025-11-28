# セットアップガイド

このドキュメントでは、システムのセットアップ手順を説明します。

## 目次

1. [前提条件](#前提条件)
2. [CLIのインストール](#cliのインストール)
3. [CursorでのMCP設定](#cursorでのmcp設定)
4. [サービスの起動](#サービスの起動)

## 前提条件

- Python 3.12以上がインストールされていること
- Docker と Docker Compose がインストールされていること
- `codex` と `claude` CLIがインストールされ、PATHに含まれていること

## CLIのインストール

### Codex CLI

Codex CLIのインストール方法：

```bash
# Homebrewを使用（macOS）
brew install codex

# または、公式サイトからダウンロード
# https://codex.openai.com/
```

インストール後、認証を設定：

```bash
codex login
```

### Claude CLI

Claude CLIのインストール方法：

```bash
# Homebrewを使用（macOS）
brew install claude

# または、公式サイトからダウンロード
# https://claude.ai/cli
```

インストール後、認証を設定：

```bash
# 対話型セッション用のログイン
claude login

# 非対話型モード用のトークン設定（推奨）
claude setup-token
```

**重要**: `claude setup-token` を実行すると、非対話型モード（`claude -p`）でも認証が動作するようになります。

## CursorでのMCP設定

### 設定方法

1. **Cursorを開く**
2. **Settings（設定）を開く**
   - `Cmd + ,` (macOS) または `Ctrl + ,` (Windows/Linux)
   - または、メニューから `Cursor` → `Settings`
3. **MCPセクションを探す**
   - 左サイドバーで「MCP」または「Model Context Protocol」を検索
4. **Add Source（ソース追加）をクリック**
5. **以下の情報を入力**:
   - **Name**: `ai_debate_bridge` または任意の名前
   - **Type**: `HTTP` または `HTTP Server`
   - **URL**: `http://localhost:8080`
   - **Description**: `CodexとClaudeCodeの議論セッションを管理するMCPブリッジ`

### 設定ファイルでの設定

Cursorの設定ファイル（通常は `~/.cursor/mcp.json` または設定ディレクトリ内）に以下を追加：

```json
{
  "mcpServers": {
    "ai_debate_bridge": {
      "url": "http://localhost:8080",
      "type": "http",
      "description": "CodexとClaudeCodeの議論セッションを管理するMCPブリッジ"
    }
  }
}
```

### 設定ファイルの場所

- **macOS**: `~/Library/Application Support/Cursor/User/settings.json`
- **Windows**: `%APPDATA%\Cursor\User\settings.json`
- **Linux**: `~/.config/Cursor/User/settings.json`

### 設定後の確認

1. **Cursorを再起動**（必要に応じて）
2. **MCPツールが利用可能か確認**
   - Cursorのチャットで、MCPツールが表示されるか確認
   - または、設定画面でMCPサーバーの状態を確認

## サービスの起動

### 自動起動（推奨）

すべてのサービスを一度に起動:

```bash
./start.sh
```

すべてのサービスを停止:

```bash
./stop.sh
```

### 手動起動

#### ホストラッパーの起動

```bash
cd host_wrappers
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python codex_wrapper.py    # ポート 9001
# 別ターミナルで
python claude_wrapper.py   # ポート 9002
```

#### Dockerコンテナの起動

```bash
cd multi-agent-cli-gateway-mcp-server
docker compose up -d
```

### 動作確認

```bash
# ホストラッパーの確認
curl http://localhost:9001/health
curl http://localhost:9002/health

# MCPブリッジの確認
curl http://localhost:8080/health
```

## トラブルシューティング

### CLIがインストールされていない

- Codex CLI: `codex --version` で確認
- Claude CLI: `claude --version` で確認
- PATHに含まれているか確認: `which codex`, `which claude`

### 認証エラー

- Codex CLI: `codex login` を実行
- Claude CLI: `claude login` と `claude setup-token` を実行

### MCPサーバーに接続できない

1. **MCPサーバーが起動しているか確認**:
   ```bash
   curl http://localhost:8080/health
   ```

2. **Dockerコンテナが起動しているか確認**:
   ```bash
   docker ps --filter "name=multi-agent-cli-gateway-mcp"
   ```

3. **ポート8080が使用されているか確認**:
   ```bash
   lsof -i :8080
   ```

### ツールが表示されない場合

1. **Cursorを再起動**
2. **MCP設定を確認**
3. **MCPサーバーのログを確認**:
   ```bash
   docker logs multi-agent-cli-gateway-mcp
   ```

## 次のステップ

セットアップが完了したら、`USAGE.md` を参照して使用方法を確認してください。

