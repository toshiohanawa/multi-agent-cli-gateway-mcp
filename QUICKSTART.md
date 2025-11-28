# クイックスタートガイド

このガイドでは、システムを起動して動作確認を行う手順を説明します。

## 前提条件

- Python 3.12以上がインストールされていること
- Docker と Docker Compose がインストールされていること
- `codex` と `claude` CLIがインストールされ、PATHに含まれていること
  - インストール方法: `docs/CLI_INSTALLATION.md` を参照
  - Claude CLIは `claude setup-token` で認証設定が必要

## クイックスタート（自動起動 - 推奨）

すべてのサービスを一度に起動:
```bash
./start.sh
```

すべてのサービスを停止:
```bash
./stop.sh
```

## 手動起動（詳細手順）

### ステップ1: ホストラッパーの起動

#### 1-1. 仮想環境の作成と依存関係のインストール

```bash
cd host_wrappers
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### 1-2. ラッパーサーバーの起動

**ターミナル1**でCodexラッパーを起動:
```bash
cd host_wrappers
source .venv/bin/activate
python codex_wrapper.py
# → http://localhost:9001 で起動
```

**ターミナル2**でClaudeラッパーを起動:
```bash
cd host_wrappers
source .venv/bin/activate
python claude_wrapper.py
# → http://localhost:9002 で起動
```

### ステップ2: Docker側MCPサーバーの起動

#### 2-1. Dockerイメージのビルドと起動（自動 - 推奨）

ホストラッパーも自動的に起動します:
```bash
cd docker
./compose-up.sh
# → ホストラッパーとDockerコンテナが自動的に起動します
```

#### 2-2. Dockerイメージのビルドと起動（手動）

ホストラッパーを手動で起動した場合:
```bash
cd docker
docker compose up -d
# → http://localhost:8080 で起動
```

#### 2-3. 動作確認

ログを確認:
```bash
cd docker
docker compose logs -f mcp_server
```

停止する場合:
```bash
cd docker
./compose-down.sh
# または
docker compose down
```

## ステップ3: 動作確認テスト

### 3-1. ホストラッパーのテスト

ホストラッパーが起動している状態で:
```bash
cd scripts
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python test_host_wrappers.py
```

### 3-2. MCPブリッジのテスト

Dockerコンテナとホストラッパーが起動している状態で:
```bash
cd scripts
source .venv/bin/activate  # 既にアクティブな場合は不要
python test_mcp_bridge.py
```

## ステップ4: Cursorへの登録

1. Cursor → Settings → MCP → Add Source
2. HTTP で `http://localhost:8080` を指定
3. `mcp/mcp.json` のメタデータを参照してツール `start_debate`, `step`, `stop` を使用

## ステップ5: 使用例

### 議論を開始（交互応答）

Cursorで以下のように指示:
```
CodexとClaudeCodeに議論させて。まずはこのテーマで始めて：
「PythonでFizzBuzzを実装してください。」
```

**動作**:
1. Codexが最初に応答
2. ClaudeがCodexの応答に対して応答
3. 以降は交互に応答（Codex → Claude → Codex → ...）

**トークン節約**: 各ターンで1つのモデルだけが応答するため、約50%のトークン削減

### 次のステップに進む（交互応答）

意見が割れた場合、ユーザーが裁定を選択:
```
Claudeの方針を採用して次に進めて
```

**動作**:
- Codex → Claude → Codex → ... の順で交互に応答
- 前のターンのもう一方のモデルの応答を参照して応答

### 議論を終了

```
ここで議論を終了して
```

Cursor LLMが `stop` ツールを呼び出します。

## 交互応答について

詳細は `docs/ALTERNATING_RESPONSE.md` を参照してください。

- **以前の実装**: 各ターンで両方のモデルが同時に応答（2倍のトークン）
- **現在の実装**: 各ターンで1つのモデルだけが応答（約50%のトークン削減）

## トラブルシューティング

### ホストラッパーに接続できない
- `codex` と `claudecode` CLIがインストールされているか確認
- CLIがPATHに含まれているか確認
- ポート9001, 9002が使用中でないか確認

### Dockerコンテナに接続できない
- Docker Desktopが起動しているか確認
- `docker compose ps` でコンテナの状態を確認
- `docker compose logs mcp_server` でエラーログを確認

### CursorでMCPツールが見えない
- MCPサーバーが起動しているか確認（`http://localhost:8080/health`）
- CursorのMCP設定で正しいURLを指定しているか確認
- Cursorを再起動してみる
