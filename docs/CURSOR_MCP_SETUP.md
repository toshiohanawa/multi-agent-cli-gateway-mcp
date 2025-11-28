# CursorでのMCPソース追加手順

## 現在の状態

✅ **MCPサーバー**: 正常に起動中
- **URL**: `http://localhost:8080`
- **ヘルスチェック**: ✅ 正常
- **利用可能なツール**: `start_debate`, `step`, `stop`

## Cursorでの設定方法

### 方法1: Cursorの設定画面から追加（推奨）

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

### 方法2: 設定ファイルに直接記述

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

### 方法3: Cursorの設定ファイルの場所

Cursorの設定ファイルは通常以下の場所にあります：

- **macOS**: `~/Library/Application Support/Cursor/User/settings.json`
- **Windows**: `%APPDATA%\Cursor\User\settings.json`
- **Linux**: `~/.config/Cursor/User/settings.json`

MCP設定は、設定ファイル内の `mcp.servers` セクションに追加します。

## 設定後の確認

1. **Cursorを再起動**（必要に応じて）
2. **MCPツールが利用可能か確認**
   - Cursorのチャットで、MCPツールが表示されるか確認
   - または、設定画面でMCPサーバーの状態を確認

## 利用可能なツール

設定が完了すると、以下のツールが利用可能になります：

### 1. start_debate
議論セッションを開始します。

**パラメータ**:
- `initial_prompt` (string): 初期のトピックやリクエスト

**使用例**:
```
start_debate ツールを使用して、初期プロンプト「PythonでFizzBuzzを実装してください。」で議論を開始してください。
```

### 2. step
前ターンの裁定結果を受けて、次のターンに進みます。

**パラメータ**:
- `decision` (object):
  - `type` (string): `"adopt_codex"`, `"adopt_claude"`, または `"custom_instruction"`
  - `custom_text` (string, optional): `type`が`"custom_instruction"`の場合に必要

**使用例**:
```
step ツールを使用して、Codexの方針を採用して次のターンに進んでください。
```

### 3. stop
現在の議論セッションを終了します。

**パラメータ**: なし

**使用例**:
```
stop ツールを使用して議論を終了してください。
```

## トラブルシューティング

### MCPサーバーに接続できない場合

1. **MCPサーバーが起動しているか確認**:
   ```bash
   curl http://localhost:8080/health
   ```

2. **ポート8080が使用されているか確認**:
   ```bash
   lsof -i :8080
   ```

3. **Dockerコンテナが起動しているか確認**:
   ```bash
   docker ps --filter "name=multi-agent-cli-gateway-mcp"
   ```

### ツールが表示されない場合

1. **Cursorを再起動**
2. **MCP設定を確認**
3. **MCPサーバーのログを確認**:
   ```bash
   docker logs multi-agent-cli-gateway-mcp
   ```

## 使用例

### 完全な使用例

1. **議論を開始**:
   ```
   CodexとClaudeCodeに議論させて。まずはこのテーマで始めて：
   「PythonでFizzBuzzを実装してください。」
   ```

2. **次のステップに進む**（意見が割れた場合）:
   ```
   Claudeの方針を採用して次に進めて
   ```

3. **議論を終了**:
   ```
   ここで議論を終了して
   ```

## 注意事項

- MCPサーバーはHTTPベースで動作しています
- CursorがHTTPベースのMCPサーバーをサポートしている必要があります
- 標準的なMCPプロトコル（SSE/WebSocket）とは異なる実装のため、Cursorのバージョンによっては動作しない可能性があります

