# セキュリティ設定ガイド

このドキュメントでは、システムのセキュリティ設定方法を説明します。

## 実装済みのセキュリティ対策

### 1. 認証トークン（オプション）

すべてのエンドポイントで認証トークンによる保護が可能です。

#### ホストラッパー（codex_wrapper.py, claude_wrapper.py）

環境変数 `WRAPPER_AUTH_TOKEN` を設定すると、認証が有効になります：

```bash
export WRAPPER_AUTH_TOKEN="your-secret-token-here"
```

リクエスト時には `X-Auth-Token` ヘッダーを追加：

```bash
curl -X POST http://localhost:9001/codex \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: your-secret-token-here" \
  -d '{"prompt": "Hello"}'
```

#### MCPブリッジ（bridge.py）

環境変数 `MCP_AUTH_TOKEN` を設定：

```bash
export MCP_AUTH_TOKEN="your-mcp-token-here"
```

リクエスト時には `X-Auth-Token` ヘッダーを追加：

```bash
curl -X POST http://localhost:8080/start_debate \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: your-mcp-token-here" \
  -d '{"initial_prompt": "Hello"}'
```

### 2. 環境変数のホワイトリスト

ホストラッパーは、CLIに渡す環境変数をホワイトリストで制限しています。

**許可される環境変数**:
- `PATH`
- `HOME`
- `SHELL`
- `LANG`
- `LC_ALL`
- `TERM`

これにより、APIキーなどの機密情報がCLIに渡されることを防ぎます。

### 3. レート制限

すべてのエンドポイントでレート制限が実装されています：

- **ホストラッパー**: 60秒間に30リクエストまで
- **MCPブリッジ**: 60秒間に20リクエストまで

レート制限を超えると `429 Too Many Requests` エラーが返されます。

### 4. リクエストサイズ制限

- **ホストラッパー**: 16KB
- **MCPブリッジ**: 32KB

制限を超えると `413 Request Entity Too Large` エラーが返されます。

### 5. タイムアウト設定

- **CLI実行タイムアウト**: デフォルト30秒（`CLI_TIMEOUT_SECONDS`で変更可能）
- **HTTPタイムアウト**: デフォルト30秒（`HTTP_TIMEOUT_SECONDS`で変更可能）

### 6. バインドアドレスの制限

デフォルトで `127.0.0.1` にバインドされ、ローカルホストからのみアクセス可能です。

環境変数で変更可能：
- `WRAPPER_BIND_HOST`: ホストラッパーのバインドアドレス（デフォルト: `127.0.0.1`）
- `MCP_BIND_HOST`: MCPブリッジのバインドアドレス（デフォルト: `127.0.0.1`）

### 7. セッション分離

MCPブリッジは、ユーザー単位でセッションを分離しています。

各リクエストに `X-User-ID` ヘッダーを追加することで、ユーザーごとのセッションが管理されます：

```bash
curl -X POST http://localhost:8080/start_debate \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user-123" \
  -d '{"initial_prompt": "Hello"}'
```

`X-User-ID` が指定されない場合、自動的にUUIDが生成されます。

## 推奨設定

### 本番環境での設定

```bash
# 認証トークンを設定（強く推奨）
export WRAPPER_AUTH_TOKEN="$(openssl rand -hex 32)"
export MCP_AUTH_TOKEN="$(openssl rand -hex 32)"

# ローカルホストのみにバインド（デフォルト）
export WRAPPER_BIND_HOST="127.0.0.1"
export MCP_BIND_HOST="127.0.0.1"

# タイムアウトを短く設定（必要に応じて）
export CLI_TIMEOUT_SECONDS="30"
export HTTP_TIMEOUT_SECONDS="30"
```

### Docker Composeでの設定

`multi-agent-cli-gateway-mcp-server/docker-compose.yml` に環境変数を追加：

```yaml
services:
  mcp_server:
    environment:
      - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}
      - WRAPPER_AUTH_TOKEN=${WRAPPER_AUTH_TOKEN}
      - MCP_BIND_HOST=127.0.0.1
      - HTTP_TIMEOUT_SECONDS=30
```

### 起動スクリプトでの設定

`.env` ファイルを作成して環境変数を設定：

```bash
# .env
WRAPPER_AUTH_TOKEN=your-wrapper-token
MCP_AUTH_TOKEN=your-mcp-token
WRAPPER_BIND_HOST=127.0.0.1
MCP_BIND_HOST=127.0.0.1
```

`start.sh` で読み込み：

```bash
#!/bin/bash
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi
# ... rest of the script
```

## 追加のセキュリティ対策

### 1. リバースプロキシの使用

NginxやCaddyなどのリバースプロキシを使用して、TLS終端と追加の認証を提供：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header X-Auth-Token "your-token";
    }
}
```

### 2. ファイアウォール設定

必要に応じて、ファイアウォールでポートへのアクセスを制限：

```bash
# macOS
sudo pfctl -f /etc/pf.conf

# Linux
sudo ufw allow from 127.0.0.1 to any port 9001,9002,8080
```

### 3. VPN内での運用

ローカルネットワーク内でのみアクセス可能にするため、VPN内での運用を推奨します。

## セキュリティチェックリスト

- [ ] 認証トークンを設定している
- [ ] バインドアドレスを `127.0.0.1` に設定している
- [ ] 環境変数のホワイトリストが機能している
- [ ] レート制限が有効になっている
- [ ] リクエストサイズ制限が有効になっている
- [ ] タイムアウトが適切に設定されている
- [ ] セッション分離が機能している
- [ ] TLS終端プロキシを使用している（本番環境）
- [ ] ファイアウォールでアクセスを制限している（本番環境）

## トラブルシューティング

### 認証エラーが発生する

- 環境変数が正しく設定されているか確認
- リクエストヘッダーに `X-Auth-Token` が含まれているか確認
- トークンが一致しているか確認

### レート制限エラーが発生する

- リクエスト頻度を下げる
- `RATE_LIMIT_MAX_REQUESTS` を調整（コードを変更）

### セッションが共有される

- `X-User-ID` ヘッダーを各リクエストに追加
- ユーザーごとに異なるIDを使用

## 実装詳細

### 実装前の問題と対策

#### claude_wrapper.py

**実装前の問題**:
- `0.0.0.0` で公開され、外部からアクセス可能
- 全環境変数をCLIに渡す（APIキー等の漏えいリスク）
- 認証なし、レート制限なし、リクエストサイズ制限なし

**実装後の対策**:
- ✅ 環境変数ホワイトリスト: `ALLOWED_ENV_VARS` で許可された環境変数のみをCLIに渡す
- ✅ 認証トークン: `WRAPPER_AUTH_TOKEN` 環境変数で認証を有効化（オプション）
- ✅ レート制限: 60秒間に30リクエストまで
- ✅ リクエストサイズ制限: 16KBまで
- ✅ 127.0.0.1バインド: デフォルトでローカルホストのみにバインド
- ✅ タイムアウト: デフォルト60秒（`CLI_TIMEOUT_SECONDS`で変更可能）

#### bridge.py

**実装前の問題**:
- 認証なし、レート制限なし
- グローバルセッション（複数ユーザーで共有）
- リクエストサイズ制限なし、`0.0.0.0` で公開

**実装後の対策**:
- ✅ 認証トークン: `MCP_AUTH_TOKEN` 環境変数で認証を有効化（オプション）
- ✅ レート制限: 60秒間に20リクエストまで
- ✅ リクエストサイズ制限: 32KBまで
- ✅ セッション分離: ユーザー単位でセッションを分離（`X-User-ID`ヘッダー）
- ✅ 127.0.0.1バインド: デフォルトでローカルホストのみにバインド
- ✅ プロンプトサイズ制限: 8192文字まで
- ✅ タイムアウト: デフォルト60秒（`HTTP_TIMEOUT_SECONDS`で変更可能）

### コード例

#### 環境変数ホワイトリスト

```python
ALLOWED_ENV_VARS = {"PATH", "HOME", "SHELL", "LANG", "LC_ALL", "TERM"}

def _build_safe_env() -> dict:
    env = {k: v for k, v in os.environ.items() if k in ALLOWED_ENV_VARS}
    env.setdefault("PATH", os.environ.get("PATH", ""))
    return env
```

#### 認証トークン

```python
AUTH_TOKEN = os.getenv("WRAPPER_AUTH_TOKEN")  # または MCP_AUTH_TOKEN

def _verify_token(token: str = Header(default=None, alias="X-Auth-Token")) -> None:
    if AUTH_TOKEN is None:
        return  # 認証が無効な場合はスキップ
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")
```

#### セッション分離

```python
_sessions: Dict[str, DebateSession] = {}

def _get_user_id(request: Request) -> str:
    user_id_header = request.headers.get("X-User-ID")
    if user_id_header:
        return user_id_header
    return str(uuid.uuid4())  # 自動生成
```

## テスト方法

### 認証テスト

```bash
# 認証なし（エラーになるはず）
curl -X POST http://localhost:8080/start_debate \
  -H "Content-Type: application/json" \
  -d '{"initial_prompt": "test"}'

# 認証あり（成功）
curl -X POST http://localhost:8080/start_debate \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: your-token" \
  -d '{"initial_prompt": "test"}'
```

### レート制限テスト

```bash
# 連続でリクエストを送信
for i in {1..25}; do
  curl -X POST http://localhost:8080/start_debate \
    -H "Content-Type: application/json" \
    -H "X-Auth-Token: your-token" \
    -d '{"initial_prompt": "test"}' &
done
wait
# 20リクエストを超えると429エラーが返される
```

### セッション分離テスト

```bash
# ユーザー1でセッション開始
curl -X POST http://localhost:8080/start_debate \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: your-token" \
  -H "X-User-ID: user-1" \
  -d '{"initial_prompt": "test"}'

# ユーザー2でセッション開始（別セッション）
curl -X POST http://localhost:8080/start_debate \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: your-token" \
  -H "X-User-ID: user-2" \
  -d '{"initial_prompt": "test"}'
```

## 今後の改善案

1. **セッション永続化**: Redis等を使用してセッションを永続化
2. **TLS対応**: HTTPSエンドポイントの追加
3. **ログ記録**: セキュリティイベントのログ記録
4. **IPホワイトリスト**: 特定のIPアドレスからのみアクセスを許可
5. **BASIC認証**: HTTP Basic認証のサポート

## 注意事項

- **開発環境**: 認証を無効にしても動作しますが、本番環境では必ず有効にしてください
- **トークン管理**: トークンは安全に管理し、バージョン管理システムにコミットしないでください
- **ネットワーク**: 可能な限りローカルホストのみにバインドし、外部からのアクセスを制限してください
- **セッション管理**: 現在の実装では、セッションはメモリ内に保持されます。再起動すると失われます

