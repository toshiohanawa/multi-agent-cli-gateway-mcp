# Docker MCP サーバー 実装仕様書

# 1. プロジェクト概要

## 1.1 目的

本システムは、以下 4 者による議論環境を構築することを目的とする：

- Codex（CLI 経由で利用するモデル A）
- ClaudeCode（CLI 経由で利用するモデル B）
- Cursor 標準 LLM（ジャッジ兼オーケストレータ）
- ユーザー（最終意思決定者）

ユーザーは Cursor 上で自然言語で操作するだけで、

Codex と ClaudeCode の対話を開始・継続し、両者の意見が割れた場合に

どちらの方針を採用するか、あるいは折衷案・独自方針を選択できる。

## 1.2 前提条件

- OS: macOS（Apple Silicon / Intel いずれも可）
- `codex` CLI コマンドが mac ホストにインストール済み
- `claudecode` CLI コマンドが mac ホストにインストール済み
- Docker Desktop for Mac がインストール済み
- Cursor が MCP に対応している（現行 Cursor）

## 1.3 非機能要件

- 外部 API キーは利用しない（Codex/ClaudeCode は CLI のみ）
- ログファイル保存は行わない（コンソール出力のみでよい）
- セッションは同時に 1 つのみ扱う想定で設計する
- 初期テーマは不要（ユーザーが都度入力）

---

# 2. 全体アーキテクチャ

## 2.1 コンポーネント構成

物理的な構成は以下の通り：

1. mac ホスト側
    - `codex_wrapper.py`（Codex CLI ラッパ HTTP サーバ）
    - `claude_wrapper.py`（ClaudeCode CLI ラッパ HTTP サーバ）
    - `codex` CLI 本体
    - `claudecode` CLI 本体
2. Docker コンテナ側
    - `bridge.py`（Codex と ClaudeCode の呼び出し・状態管理）
    - `mcp.json`（MCP サーバのメタデータ定義）
    - HTTP / WebSocket ベースの MCP サーバ実装
3. Cursor 側
    - MCP Source として Docker コンテナの MCP サーバに接続
    - 標準 LLM がツール（bridge の MCP メソッド）を呼び出す
    - Codex/Claude の出力を比較し、ユーザーへの問いかけと裁定の反映を行う

## 2.2 通信フローの概要

1. Cursor LLM → MCP サーバ（Docker 内）
    - MCP ツール呼び出し（開始 / 継続 / 停止など）
2. MCP サーバ（bridge.py） → ホスト側 HTTP ラッパ
    - Codex 用: `POST http://host.docker.internal:9001/codex`
    - Claude 用: `POST http://host.docker.internal:9001/claude`
3. ホスト側ラッパ → `codex` / `claudecode` CLI 実行
    - `subprocess.run` で CLI に標準入力を渡し、標準出力を取得

---

# 3. ディレクトリ構成

Codex に生成させる想定のディレクトリ構成は以下：

```
project-root/
  README.md
  docker/
    Dockerfile
    docker-compose.yml
  mcp/
    mcp.json
    bridge.py
    __init__.py (任意)
  host_wrappers/
    codex_wrapper.py
    claude_wrapper.py
    requirements.txt

```

---

# 4. ホスト側ラッパ仕様（codex_wrapper / claude_wrapper）

## 4.1 共通仕様

- Python + FastAPI + Uvicorn を利用した HTTP サーバ
- ポート:
    - Codex wrapper: 9001
    - Claude wrapper: 9002
- エンドポイント:
    - Codex: `POST /codex`
    - Claude: `POST /claude`
- リクエスト/レスポンスは JSON

### 4.1.1 リクエスト形式

```json
{
  "prompt": "string",
  "history": [
    {
      "role": "user" | "assistant",
      "content": "string"
    }
  ]
}

```

- `prompt`: 今ターンの入力
- `history`: 必要なら過去のやりとりを CLI 側に埋め込むための履歴（実装側で使わなくてもよいが型として用意）

### 4.1.2 レスポンス形式

```json
{
  "output": "string"
}

```

- CLI の標準出力全体を `output` に格納

## 4.2 `codex_wrapper.py`

### 4.2.1 起動方法（仕様）

```bash
python host_wrappers/codex_wrapper.py

```

### 4.2.2 処理内容

1. POST `/codex` を受信
2. JSON をパースし `prompt` を取得
3. 以下のように CLI を実行（例）：
    
    ```python
    result = subprocess.run(
        ["codex", "chat"],
        input=prompt,
        text=True,
        capture_output=True,
        timeout=120
    )
    
    ```
    
4. `result.stdout` を `output` として JSON で返す
5. エラーがあれば適切な HTTP ステータス（例: 500）とエラーメッセージを返す

## 4.3 `claude_wrapper.py`

`codex_wrapper.py` とほぼ同一。違いは CLI コマンドのみ：

```python
["claudecode", "chat"]

```

---

# 5. Docker 側 MCP サーバ仕様

## 5.1 Dockerfile（要件）

- ベースイメージ: `python:3.12-slim` など
- ランタイム依存:
    - `fastapi`
    - `uvicorn[standard]`
    - `requests`
    - （MCP サーバ実装で必要なもの）
- 作業ディレクトリ: `/app`
- `/app/mcp` に `bridge.py`, `mcp.json` を配置
- `uvicorn mcp.bridge:app --host 0.0.0.0 --port 8080` のような形で起動

## 5.2 docker-compose.yml（要件）

- サービス名: `mcp_server`
- ポート:
    - コンテナ: 8080
    - ホスト: 8080
- ボリュームマウント:
    - `./mcp:/app/mcp`
    - `./host_wrappers:/app/host_wrappers`（必要なら中からも参照可能）

例（仕様レベル）：

```yaml
services:
  mcp_server:
    build: ./docker
    ports:
      - "8080:8080"
    volumes:
      - ./mcp:/app/mcp
      - ./host_wrappers:/app/host_wrappers

```

---

# 6. bridge.py の仕様

## 6.1 概要

`bridge.py` は MCP サーバとして動作し、

ツールとして以下を提供する:

- `start_debate(initial_prompt: str)`
    
    議論セッションの開始。Codex / Claude の初回応答を取得し、セッション状態を作成。
    
- `step(decision: object)`
    
    前ターンの裁定結果（どちらの方針を採用するか等）を受け取り、次の Codex / Claude の応答を生成。
    
- `stop()`
    
    現在のセッションを終了。
    

セッションは一つのみを想定するため、セッション ID は固定または省略可能。

## 6.2 内部データモデル

Python の型イメージ：

```python
from dataclasses import dataclass, field
from typing import List, Literal, Optional, Dict

Role = Literal["user", "assistant", "system"]

@dataclass
class Message:
  role: Role
  content: str

@dataclass
class ModelOutput:
  model: Literal["codex", "claude"]
  content: str

@dataclass
class Turn:
  user_instruction: str
  codex_output: str
  claude_output: str

@dataclass
class DebateSession:
  active: bool
  history: List[Turn] = field(default_factory=list)

```

`bridge.py` 内では、グローバルに 1 つの `DebateSession` を保持してよい（シングルトン前提）。

## 6.3 HTTP クライアント仕様（ホストラッパ呼び出し）

`requests` ライブラリを用いて、ホスト側ラッパを呼ぶ。

### 6.3.1 Codex 呼び出し

```python
import requests

def call_codex(prompt: str, history: list[dict] | None = None) -> str:
    payload = {"prompt": prompt, "history": history or []}
    resp = requests.post(
        "http://host.docker.internal:9001/codex",
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["output"]

```

### 6.3.2 Claude 呼び出し

```python
def call_claude(prompt: str, history: list[dict] | None = None) -> str:
    payload = {"prompt": prompt, "history": history or []}
    resp = requests.post(
        "http://host.docker.internal:9002/claude",
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["output"]

```

## 6.4 MCP ツールのインターフェース仕様

MCP 実装方式は任意だが、ツールの入出力は概ね以下とする。

### 6.4.1 start_debate

### 入力（Cursor → MCP）

```json
{
  "initial_prompt": "string"
}

```

### 処理フロー

1. `DebateSession` がすでに存在し `active=True` の場合はエラーを返す（または強制リセット）。
2. `initial_prompt` を Codex と Claude の両方に投げるか、以下のように段階的に投げる：
    - Codex に initial_prompt → `codex_output_1`
    - Claude に `codex_output_1` を前提とした入力を生成して投げる → `claude_output_1`
3. `Turn` オブジェクトを生成して `session.history` に追加
4. `DebateSession.active = True`

### 出力（MCP → Cursor）

```json
{
  "status": "ok",
  "turn": {
    "user_instruction": "string",
    "codex_output": "string",
    "claude_output": "string"
  }
}

```

### 6.4.2 step

### 入力（Cursor → MCP）

Cursor 側の LLM が、前ターンの Codex / Claude の出力を比較し、ユーザーとも対話したうえで「採用方針」を決め、その情報を MCP に渡す。

```json
{
  "decision": {
    "type": "adopt_codex" | "adopt_claude" | "custom_instruction",
    "custom_text": "string (type=custom_instructionのときのみ)"
  }
}

```

### 処理フロー（例）

1. 直近の `Turn` を取得
2. `decision` に応じて次ターンの入力文を組み立て:
    - `adopt_codex` の場合:
        - 「前ターンは Codex の方針を採用することになった。その前提でさらに議論を進めよ」というメタ指示 + 直近のやりとり要約
    - `adopt_claude` の場合:
        - 同様に Claude 側の方針を採用する前提で入力を組み立て
    - `custom_instruction` の場合:
        - `custom_text` をベースに、Codex/Claude 両者への新たな議題として用いる
3. Codex → Claude の順に新しい応答を取得
4. 新しい `Turn` を `history` に追加
5. 新しい `Turn` をレスポンスとして返す

### 出力（MCP → Cursor）

```json
{
  "status": "ok",
  "turn": {
    "user_instruction": "string",
    "codex_output": "string",
    "claude_output": "string"
  }
}

```

### 6.4.3 stop

### 入力

空、または単純な JSON:

```json
{}

```

### 処理

- `DebateSession.active = False`
- `history` は必要に応じてクリアしてもよい（今回は保持しなくてよい）

### 出力

```json
{
  "status": "stopped"
}

```

---

# 7. mcp.json の仕様

`mcp.json` は Cursor がこの MCP サーバをツール群として認識するためのメタデータ定義。

内容例（仕様レベル。Codex はこれを具体化する）：

- name: `"ai_debate_bridge"`
- version: `"1.0.0"`
- tools:
    - `"start_debate"`:
        - description: Codex/Claude の議論セッションを開始
        - input schema: `{"initial_prompt": "string"}`
    - `"step"`:
        - description: 前ターンの裁定結果を受けて次ターンを進める
        - input schema: `{"decision": {...}}`
    - `"stop"`:
        - description: セッションを終了

---

# 8. Cursor LLM 側での「ジャッジ」ロジック（コード外仕様）

これは Codex が実装するものではなく、

**Cursor 内の LLM が「どう振る舞うべきか」を示す仕様**。

1. `start_debate` を呼び出したあと、レスポンス内の
    
    `turn.codex_output` と `turn.claude_output` を読み取る。
    
2. その 2 文書を比較し、モデル自身が：
    - 結論が一致しているか
    - 意見が割れているか
    - 対立点は何か
    
    を自然言語で整理する。
    
3. 意見が割れていると判断した場合、ユーザーに質問する：
    - Codex 側を採用するか
    - Claude 側を採用するか
    - 折衷案を自分（Cursor LLM）が生成してから採用するか
    - ユーザー自身の方針文を入力するか
4. ユーザーの回答内容に応じて `decision` オブジェクトを構築し、
    
    `step` ツールを呼び出す：
    
    - Codex 採用 → `"type": "adopt_codex"`
    - Claude 採用 → `"type": "adopt_claude"`
    - ユーザー方針 → `"type": "custom_instruction", "custom_text": "..."`
5. `step` の結果の新しい `turn` を受け取り、同様のループを繰り返す。

---

# 9. エラーハンドリング仕様

## 9.1 ホスト側ラッパ

- CLI がエラーを返した場合：
    - HTTP 500 + JSON `{ "error": "CLI error message..." }`
- タイムアウト（例: 120 秒）した場合：
    - HTTP 504 + エラーメッセージ

## 9.2 bridge.py（MCP サーバ）

- ラッパからエラーが返ってきた場合：
    - MCP レスポンスで `status: "error"` と `message` を返す
- セッションが存在しない状態で `step` / `stop` が呼ばれた場合：
    - `status: "error"` と `"no active session"` を返す

Cursor LLM はこれを見てユーザーに報告し、再実行や終了を提案する。

---

# 10. セットアップ / 使用手順（開発者向け）

## 10.1 ホスト側ラッパのセットアップ

```bash
cd host_wrappers
python -m venv .venv
source .venv/bin/activate  # macOS
pip install -r requirements.txt
python codex_wrapper.py
python claude_wrapper.py

```

※ 要求ライブラリ:

- fastapi
- uvicorn
- pydantic
- （標準ライブラリ: subprocess, typing 等）

## 10.2 Docker 側 MCP サーバ起動

```bash
cd docker
docker build -t ai-debate-mcp .
docker compose up -d

```

## 10.3 Cursor からの接続

1. Cursor → Settings → MCP → Add Source
2. HTTP or WebSocket で `http://localhost:8080` を指定
3. ツール `start_debate`, `step`, `stop` が見えていれば OK

## 10.4 実行シナリオ（ユーザー視点）

1. Cursor でユーザーがプロンプト：
    
    > Codex と ClaudeCode に議論させて。まずはこのテーマで始めて：
    > 
    > 
    > 「書店の将来戦略について」
    > 
2. Cursor LLM:
    - `start_debate` を呼び出す
    - `turn.codex_output` / `turn.claude_output` を比較
    - 意見が割れているか判定
    - 割れていればユーザーに裁定を質問
3. ユーザーが回答：
    
    > まずは Claude の方針を採用して次に進めて
    > 
4. Cursor LLM:
    - `decision = { "type": "adopt_claude" }` を構成
    - `step` を呼び出す
    - 新しい `turn` をもとに再び比較・判定
5. ユーザーが `/stop` または「ここで議論を終了して」と言えば `stop` を呼ぶ。