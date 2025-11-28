# multi-agent-cli-gateway-mcp

Codex と ClaudeCode を Docker 内 MCP サーバ経由で議論させ、Cursor から操作できるようにするブリッジ実装。

## 何があるか
- `host_wrappers/`: FastAPI + Uvicorn で Codex/ClaudeCode CLI を HTTP に変換（9001/9002）
- `mcp/`: MCP ブリッジ（FastAPI）。ホストのラッパーに HTTP で渡してセッションを管理
- `multi-agent-cli-gateway-mcp-server/`: MCP ブリッジを動かす Dockerfile と docker-compose
- `mcp/mcp.json`: Cursor の MCP ソース設定用メタデータ
- `docs/`: ドキュメント（テスト結果、実装状況、使用方法など）
- `scripts/`: テストスクリプト

## ディレクトリ構成
```
.
├── host_wrappers/
│   ├── codex_wrapper.py
│   ├── claude_wrapper.py
│   └── requirements.txt
├── mcp/
│   ├── bridge.py
│   ├── mcp.json
│   └── requirements.txt
├── multi-agent-cli-gateway-mcp-server/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── compose-up.sh
│   ├── compose-down.sh
│   └── start-host-wrappers.sh
├── scripts/
│   ├── test_host_wrappers.py
│   ├── test_mcp_bridge.py
│   └── requirements.txt
├── docs/
│   ├── TEST_RESULTS.md
│   ├── IMPLEMENTATION_STATUS.md
│   ├── CLI_INSTALLATION.md
│   ├── CURSOR_MCP_SETUP.md
│   └── USAGE_EXAMPLE.md
├── start.sh
├── stop.sh
└── README.md
```

## クイックスタート

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

#### ホスト側ラッパの起動
Codex/ClaudeCode CLI がローカルにインストール済みであることが前提。
```bash
cd host_wrappers
python -m venv .venv
source .venv/bin/activate  # fish: source .venv/bin/activate.fish
pip install -r requirements.txt
python codex_wrapper.py    # ポート 9001
# 別ターミナルで
python claude_wrapper.py   # ポート 9002
```

#### Docker 上の MCP ブリッジ起動

### 自動起動（推奨 - ホストラッパーも自動起動）
```bash
cd multi-agent-cli-gateway-mcp-server
./compose-up.sh
# → ホストラッパーとDockerコンテナが自動的に起動します
```

### 手動起動
```bash
cd multi-agent-cli-gateway-mcp-server
docker build -t ai-debate-mcp .
docker compose up -d
# → http://localhost:8080 で起動
# 注意: ホストラッパーは別途起動が必要です
```
ボリュームマウントしているので、ローカルで `mcp/` を編集するとコンテナ側に即時反映される。

## MCP エンドポイント（HTTP）
- `POST /start_debate` — `{ "initial_prompt": "..." }` を渡し、Codex/Claude 双方の初回応答を返す
- `POST /step` — `{ "decision": { "type": "adopt_codex" | "adopt_claude" | "custom_instruction", "custom_text": "..." } }`
  - 直前のターンをもとに次の入力を組み立て、両モデルの応答を返す
- `POST /stop` — セッション終了（状態クリア）
- `GET /health` — 簡易ヘルスチェック

レスポンス例（start_debate/step 共通）:
```json
{
  "status": "ok",
  "turn": {
    "user_instruction": "...",
    "codex_output": "...",
    "claude_output": "..."
  }
}
```

## 動作確認

### 1. ホストラッパーの動作確認

ホストラッパーが起動している状態で、以下のコマンドでテストを実行します：

```bash
cd scripts
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python test_host_wrappers.py
```

このテストは以下を確認します：
- Codexラッパー（ポート9001）のヘルスチェック
- Claudeラッパー（ポート9002）のヘルスチェック
- 実際のAPI呼び出し（codex/claude CLIがインストールされている必要があります）

**注意**: CLIコマンドのインストール方法は `docs/CLI_INSTALLATION.md` を参照してください。

### 2. MCPブリッジの動作確認

Dockerコンテナが起動している状態で、以下のコマンドでテストを実行します：

```bash
cd scripts
source .venv/bin/activate  # 既にアクティブな場合は不要
python test_mcp_bridge.py
```

このテストは以下を確認します：
- MCPブリッジ（ポート8080）のヘルスチェック
- `start_debate` エンドポイント
- `step` エンドポイント（adopt_codex, adopt_claude, custom_instruction）
- `stop` エンドポイント

**注意**: MCPブリッジのテストを実行する前に、ホストラッパー（ポート9001, 9002）が起動している必要があります。

## Cursor への登録手順

詳細な手順は `docs/CURSOR_MCP_SETUP.md` を参照してください。

1. Cursor → Settings → MCP → Add Source
2. HTTP で `http://localhost:8080` を指定
3. `mcp/mcp.json` のメタデータを参照してツール `start_debate`, `step`, `stop` を使用

## ドキュメント

- **クイックスタート**: `QUICKSTART.md`
- **セットアップ**: `docs/SETUP.md` 📦 **CLIインストールとCursor設定**
- **使用方法**: `docs/USAGE.md` 📖 **MCPツールの使い方と複数プロジェクトでの使用**
- **セキュリティ設定**: `docs/SECURITY.md` ⚠️ **重要**
- **リモートアクセス**: `docs/REMOTE_ACCESS.md` 📡 **他のマシン/Dockerからアクセス**
- **テスト結果**: `docs/TEST_RESULTS.md`
- **実装状況**: `docs/IMPLEMENTATION_STATUS.md`
- **仕様書**: `masterplan.md`

## 使用例（Cursor経由）

詳細な使用例は `docs/USAGE_EXAMPLE.md` を参照してください。

1. **議論を開始**:
   ```
   CodexとClaudeCodeに議論させて。まずはこのテーマで始めて：
   「PythonでFizzBuzzを実装してください。」
   ```

2. **次のステップに進む**:
   ```
   Codexの方針を採用して次に進めて
   ```
   または
   ```
   Claudeの方針を採用して次に進めて
   ```

3. **議論を終了**:
   ```
   ここで議論を終了して
   ```

## テスト結果

**すべてのテストが成功しました！** ✅

- ✅ ホストラッパーのテスト: 成功
- ✅ MCPブリッジのテスト: 成功
- ✅ 統合テスト: 成功
- ✅ エンドツーエンドテスト: 成功
- ✅ 実際の議論セッション: 成功

詳細は `docs/TEST_RESULTS.md` を参照してください。
