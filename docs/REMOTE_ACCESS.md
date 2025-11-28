# リモートアクセスガイド

このドキュメントでは、他のローカルマシンやDockerコンテナからこのシステムにアクセスする方法を説明します。

## 現在の設定

デフォルトでは、すべてのサービスは `127.0.0.1` にバインドされており、**ローカルホストからのみアクセス可能**です。

## アクセス方法

### 1. 同じマシン上の他のプロセスからアクセス

現在の設定（`127.0.0.1`）のままで、同じマシン上の他のプロセスからアクセス可能です。

```python
import requests

# MCPブリッジにアクセス
response = requests.post(
    "http://localhost:8080/start_debate",
    json={"initial_prompt": "Hello"}
)
```

### 2. 同じマシン上の他のDockerコンテナからアクセス

Dockerコンテナからホストマシンのサービスにアクセスするには、`host.docker.internal` を使用します。

#### 方法A: host.docker.internal を使用（推奨）

```python
import requests

# Dockerコンテナ内からホストのMCPブリッジにアクセス
response = requests.post(
    "http://host.docker.internal:8080/start_debate",
    json={"initial_prompt": "Hello"}
)
```

**注意**: macOSとWindowsのDocker Desktopでは `host.docker.internal` が自動的に利用可能です。Linuxでは追加設定が必要な場合があります。

#### 方法B: Dockerネットワークを使用

同じDockerネットワークに接続することで、コンテナ名でアクセスできます。

1. **カスタムネットワークを作成**:

```bash
docker network create multi-agent-network
```

2. **既存のコンテナをネットワークに接続**:

```bash
docker network connect multi-agent-network multi-agent-cli-gateway-mcp
```

3. **他のコンテナからアクセス**:

```python
import requests

# コンテナ名でアクセス
response = requests.post(
    "http://multi-agent-cli-gateway-mcp:8080/start_debate",
    json={"initial_prompt": "Hello"}
)
```

### 3. 他のローカルマシンからアクセス

他のローカルマシン（同じネットワーク内）からアクセスするには、サービスを `0.0.0.0` にバインドする必要があります。

#### 設定方法

環境変数でバインドアドレスを変更：

```bash
# ホストラッパーを0.0.0.0にバインド
export WRAPPER_BIND_HOST="0.0.0.0"

# MCPブリッジを0.0.0.0にバインド
export MCP_BIND_HOST="0.0.0.0"
```

または、`.env` ファイルを作成：

```bash
# .env
WRAPPER_BIND_HOST=0.0.0.0
MCP_BIND_HOST=0.0.0.0
```

#### セキュリティ注意事項

⚠️ **重要**: `0.0.0.0` にバインドすると、ネットワーク上のすべてのマシンからアクセス可能になります。

**必ず以下のセキュリティ対策を実施してください**:

1. **認証トークンを設定**:
```bash
export WRAPPER_AUTH_TOKEN="$(openssl rand -hex 32)"
export MCP_AUTH_TOKEN="$(openssl rand -hex 32)"
```

2. **ファイアウォールでアクセスを制限**:
```bash
# macOS
sudo pfctl -f /etc/pf.conf

# Linux
sudo ufw allow from 192.168.1.0/24 to any port 9001,9002,8080
```

3. **VPN内でのみ使用**:
   可能な限り、VPN内でのみアクセスを許可してください。

#### 他のマシンからのアクセス例

```python
import requests

# ホストマシンのIPアドレスを使用
host_ip = "192.168.1.100"  # 実際のIPアドレスに置き換え

# MCPブリッジにアクセス
response = requests.post(
    f"http://{host_ip}:8080/start_debate",
    headers={"X-Auth-Token": "your-mcp-token"},  # 認証が必要な場合
    json={"initial_prompt": "Hello"}
)
```

### 4. Docker Composeで他のサービスからアクセス

`docker-compose.yml` で他のサービスを定義し、同じネットワークで接続します。

#### 例: 他のサービスからアクセス

```yaml
version: '3.8'

services:
  # 既存のMCPサーバー
  mcp_server:
    # ... 既存の設定 ...

  # 他のサービス（例）
  my_app:
    image: my-app:latest
    environment:
      - MCP_BRIDGE_URL=http://mcp_server:8080
      - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}
    networks:
      - multi-agent-network

networks:
  multi-agent-network:
    external: true
```

## 設定の確認

### 現在のバインドアドレスを確認

```bash
# ホストラッパーのバインドアドレス
echo $WRAPPER_BIND_HOST  # デフォルト: 127.0.0.1

# MCPブリッジのバインドアドレス
echo $MCP_BIND_HOST  # デフォルト: 127.0.0.1
```

### ポートの確認

```bash
# どのポートが開いているか確認
netstat -an | grep -E "(9001|9002|8080)"
# または
lsof -i :9001,9002,8080
```

## トラブルシューティング

### Dockerコンテナからアクセスできない

1. **host.docker.internalが利用可能か確認**:
```bash
# Dockerコンテナ内で
ping host.docker.internal
```

2. **Linuxの場合、追加設定が必要**:
```bash
# docker-compose.ymlに追加
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### 他のマシンからアクセスできない

1. **ファイアウォールの確認**:
```bash
# macOS
sudo pfctl -s rules

# Linux
sudo ufw status
```

2. **IPアドレスの確認**:
```bash
# ホストマシンのIPアドレスを確認
ifconfig  # macOS/Linux
ipconfig  # Windows
```

3. **ネットワーク接続の確認**:
```bash
# 他のマシンからping
ping <host-ip-address>
```

### 認証エラーが発生する

1. **認証トークンが設定されているか確認**:
```bash
echo $WRAPPER_AUTH_TOKEN
echo $MCP_AUTH_TOKEN
```

2. **リクエストヘッダーにトークンが含まれているか確認**:
```python
headers = {"X-Auth-Token": "your-token"}
```

## 推奨設定

### 開発環境

```bash
# .env.development
WRAPPER_BIND_HOST=127.0.0.1
MCP_BIND_HOST=127.0.0.1
# 認証なし（開発用）
```

### 本番環境（VPN内）

```bash
# .env.production
WRAPPER_BIND_HOST=0.0.0.0
MCP_BIND_HOST=0.0.0.0
WRAPPER_AUTH_TOKEN=<strong-random-token>
MCP_AUTH_TOKEN=<strong-random-token>
```

### Docker Composeでの設定

```yaml
services:
  mcp_server:
    environment:
      - MCP_BIND_HOST=${MCP_BIND_HOST:-127.0.0.1}
      - WRAPPER_AUTH_TOKEN=${WRAPPER_AUTH_TOKEN}
      - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}
    ports:
      - "${MCP_PORT:-8080}:8080"
```

## セキュリティチェックリスト

- [ ] 認証トークンを設定している（`0.0.0.0` にバインドする場合）
- [ ] ファイアウォールでアクセスを制限している
- [ ] VPN内でのみ使用している（可能な限り）
- [ ] レート制限が有効になっている
- [ ] リクエストサイズ制限が有効になっている
- [ ] TLS終端プロキシを使用している（本番環境）

## まとめ

- **同じマシン**: `127.0.0.1` のままでOK
- **Dockerコンテナ**: `host.docker.internal` を使用
- **他のマシン**: `0.0.0.0` にバインド + 認証 + ファイアウォール設定

詳細は `docs/SECURITY.md` も参照してください。

