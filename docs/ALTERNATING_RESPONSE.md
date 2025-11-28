# 交互応答実装について

## 概要

トークン数を節約するため、CodexとClaudeが**交互に応答**する実装に変更しました。

## 実装の変更点

### 以前の実装

- `start_debate`: CodexとClaudeの両方に**同じプロンプト**を送信し、**同時に**応答を取得
- `step`: CodexとClaudeの両方に**同じプロンプト**を送信し、**同時に**応答を取得
- **トークン使用量**: 各ターンで2倍（両方のモデルが同じプロンプトを処理）

### 新しい実装（交互応答）

- `start_debate`: 
  1. Codexが最初に応答
  2. Codexの応答をClaudeに渡して、Claudeが応答
- `step`: 
  - 前のターンの応答者を追跡
  - 交互に1つのモデルだけが応答（Codex → Claude → Codex → ...）
  - もう一方のモデルの前回の応答を参照
- **トークン使用量**: 各ターンで約半分（1つのモデルだけが応答）

## データ構造の変更

### Turn構造

```python
@dataclass
class Turn:
    user_instruction: str
    codex_output: Optional[str] = None  # None if Codex didn't respond this turn
    claude_output: Optional[str] = None  # None if Claude didn't respond this turn
    responder: Literal["codex", "claude"] = "codex"  # Who responded in this turn
```

### DebateSession構造

```python
@dataclass
class DebateSession:
    active: bool = False
    history: List[Turn] = field(default_factory=list)
    user_id: Optional[str] = None
    next_responder: Literal["codex", "claude"] = "codex"  # Track who should respond next
```

## 動作フロー

### start_debate

1. **Codexが最初に応答**:
   ```
   ユーザー: "PythonでHello Worldを出力するコードを書いてください。"
   → Codex: [応答]
   ```

2. **ClaudeがCodexの応答に対して応答**:
   ```
   Codex said: [Codexの応答]
   → Claude: [応答]
   ```

3. **次のターンはCodexが応答**（`next_responder = "codex"`）

### step

1. **前のターンの応答者を確認**
2. **次の応答者を決定**（交互に）
3. **前のターンのもう一方のモデルの応答を参照**
4. **1つのモデルだけが応答**

例：
- ターン1: Codex → Claude
- ターン2: Codex（Claudeの前回の応答を参照）
- ターン3: Claude（Codexの前回の応答を参照）
- ...

## トークン節約効果

### 以前の実装

各ターンで：
- Codex: プロンプト処理 + 応答生成
- Claude: プロンプト処理 + 応答生成
- **合計**: 2倍のトークン使用量

### 新しい実装

各ターンで：
- CodexまたはClaudeのどちらか1つだけが応答
- **合計**: 約半分のトークン使用量

### 推定節約率

- `start_debate`: 約50%削減（最初の2ターンで両方が応答するが、以降は交互）
- `step`: 約50%削減（1つのモデルだけが応答）

## レスポンス形式

### start_debate レスポンス

```json
{
  "status": "ok",
  "turn": {
    "user_instruction": "...",
    "codex_output": "...",  // Codexの応答
    "claude_output": "...",  // Claudeの応答
    "responder": "claude",   // 最後に応答したモデル
    "next_responder": "codex"  // 次のターンで応答するモデル
  }
}
```

### step レスポンス

```json
{
  "status": "ok",
  "turn": {
    "user_instruction": "...",
    "codex_output": "...",  // Codexが応答した場合のみ
    "claude_output": null,   // Claudeが応答しなかった場合はnull
    "responder": "codex",    // このターンで応答したモデル
    "next_responder": "claude"  // 次のターンで応答するモデル
  }
}
```

## 注意事項

1. **会話の流れ**: 交互に応答するため、より自然な会話の流れになります
2. **コンテキスト**: 前のターンの応答を参照するため、コンテキストが保持されます
3. **トークン節約**: 各ターンで1つのモデルだけが応答するため、トークン使用量が約半分になります

## テスト結果

実装後のテストで、以下の動作を確認しました：

- ✅ Codexが最初に応答
- ✅ ClaudeがCodexの応答に対して応答
- ✅ stepで交互に応答
- ✅ 前のターンの応答を参照して応答

## 互換性

既存のAPIインターフェースは維持されていますが、レスポンスに `responder` と `next_responder` フィールドが追加されました。これにより、クライアント側で次の応答者を把握できます。

