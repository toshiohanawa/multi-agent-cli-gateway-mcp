# MCPツールの使用例

## Cursorでの使用方法

CursorでMCPソースを設定した後、以下のように使用できます。

## 1. 議論を開始

Cursorのチャットで以下のように指示します：

```
CodexとClaudeCodeに議論させて。まずはこのテーマで始めて：
「PythonでFizzBuzzを実装してください。」
```

Cursor LLMが自動的に `start_debate` ツールを呼び出し、CodexとClaudeの両方から応答を取得します。

## 2. 次のステップに進む

CodexとClaudeの応答を比較した後、意見が割れた場合、以下のように指示します：

### Codexの方針を採用する場合
```
Codexの方針を採用して次に進めて
```

### Claudeの方針を採用する場合
```
Claudeの方針を採用して次に進めて
```

### 独自の方針を指定する場合
```
以下の方針で次に進めて：
「より効率的な実装を提案してください。」
```

Cursor LLMが自動的に `step` ツールを呼び出し、新しいターンを生成します。

## 3. 議論を終了

```
ここで議論を終了して
```

または

```
議論を終了してください
```

Cursor LLMが自動的に `stop` ツールを呼び出します。

## 動作確認

### MCPツールが表示されているか確認

Cursorのチャットで、MCPツールが利用可能か確認してください。通常、以下のような表示があります：

- ツール一覧に `start_debate`, `step`, `stop` が表示される
- チャットでツールを呼び出すことができる

### テスト実行

以下のコマンドで、MCPサーバーが正常に動作しているか確認できます：

```bash
# ヘルスチェック
curl http://localhost:8080/health

# start_debateのテスト
curl -X POST http://localhost:8080/start_debate \
  -H "Content-Type: application/json" \
  -d '{"initial_prompt": "PythonでHello Worldを出力するコードを書いてください。"}'
```

## トラブルシューティング

### MCPツールが表示されない場合

1. **Cursorを再起動**
2. **MCP設定を確認**
   - Settings → MCP で設定が正しく保存されているか確認
   - URLが `http://localhost:8080` になっているか確認
3. **MCPサーバーのログを確認**:
   ```bash
   docker logs multi-agent-cli-gateway-mcp
   ```

### ツールを呼び出してもエラーが出る場合

1. **MCPサーバーが起動しているか確認**:
   ```bash
   docker ps --filter "name=multi-agent-cli-gateway-mcp"
   ```

2. **ホストラッパーが起動しているか確認**:
   ```bash
   curl http://localhost:9001/health
   curl http://localhost:9002/health
   ```

3. **ログを確認**:
   ```bash
   docker logs multi-agent-cli-gateway-mcp
   tail -f .pids/codex_wrapper.log
   tail -f .pids/claude_wrapper.log
   ```

## 期待される動作

1. **start_debate**を呼び出すと：
   - CodexとClaudeの両方から応答が返される
   - セッションが開始される

2. **step**を呼び出すと：
   - 前ターンの裁定結果に基づいて、新しい応答が生成される
   - CodexとClaudeの両方から新しい応答が返される

3. **stop**を呼び出すと：
   - セッションが終了する
   - 状態がクリアされる

