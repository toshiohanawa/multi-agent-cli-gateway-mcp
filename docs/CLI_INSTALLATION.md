# CLIインストールガイド

## インストール済み

### Codex CLI
- **パッケージ**: `@openai/codex`
- **バージョン**: 0.63.0
- **コマンド**: `codex`
- **パス**: `/Users/toshiohanawa/.nvm/versions/node/v22.17.1/bin/codex`

### Claude CLI
- **パッケージ**: `@anthropic-ai/claude-code`
- **バージョン**: 2.0.55
- **コマンド**: `claude`（プロジェクトでは`claudecode`として使用していたが、実際のコマンドは`claude`）
- **パス**: `/Users/toshiohanawa/.nvm/versions/node/v22.17.1/bin/claude`

## インストール方法

### npmを使用したインストール

```bash
# Codex CLI
npm install -g @openai/codex

# Claude CLI
npm install -g @anthropic-ai/claude-code
```

### Homebrewを使用したインストール（macOS）

```bash
# Codex CLI
brew install codex

# Claude CLI
brew install --cask claude-code
```

## 設定

### Codex CLI
- OpenAI APIキーが必要な場合があります
- 環境変数 `OPENAI_API_KEY` を設定するか、初回実行時に設定を求められます

### Claude CLI
- Claude.aiアカウントが必要です
- 初回実行時にログインを求められます

## プロジェクトでの使用

プロジェクトのコードでは以下のように使用されています：

- **Codex**: `codex chat` コマンド（`host_wrappers/codex_wrapper.py`）
- **Claude**: `claude chat` コマンド（`host_wrappers/claude_wrapper.py`）

**注意**: `claude_wrapper.py`は`claudecode`コマンドを想定していましたが、実際のインストールされたコマンドは`claude`のため、コードを更新しました。

## 動作確認

```bash
# Codex CLIのバージョン確認
codex --version

# Claude CLIのバージョン確認
claude --version

# ヘルプの表示
codex --help
claude --help
```

## トラブルシューティング

### コマンドが見つからない場合

```bash
# npmのグローバルパスを確認
npm config get prefix

# PATHに追加（必要に応じて）
export PATH="$PATH:$(npm config get prefix)/bin"
```

### 権限エラーの場合

```bash
# sudoを使用してインストール（推奨しない）
sudo npm install -g @openai/codex
sudo npm install -g @anthropic-ai/claude-code
```

