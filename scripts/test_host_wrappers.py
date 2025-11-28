"""
ホストラッパーの動作確認用スクリプト
"""
import requests
import sys
import time

CODEX_URL = "http://localhost:9001"
CLAUDE_URL = "http://localhost:9002"


def check_health(url: str, name: str) -> bool:
    """ヘルスチェックエンドポイントを確認"""
    try:
        resp = requests.get(f"{url}/health", timeout=5)
        if resp.status_code == 200:
            print(f"✓ {name} ヘルスチェック成功: {resp.json()}")
            return True
        else:
            print(f"✗ {name} ヘルスチェック失敗: HTTP {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ {name} に接続できません。サーバーが起動しているか確認してください。")
        return False
    except Exception as e:
        print(f"✗ {name} エラー: {e}")
        return False


def test_codex(prompt: str = "Hello, this is a test.") -> bool:
    """Codexラッパーをテスト"""
    try:
        resp = requests.post(
            f"{CODEX_URL}/codex",
            json={"prompt": prompt, "history": []},
            timeout=130
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ Codex テスト成功")
            print(f"  レスポンス: {data.get('output', '')[:100]}...")
            return True
        else:
            print(f"✗ Codex テスト失敗: HTTP {resp.status_code}, {resp.text}")
            return False
    except Exception as e:
        print(f"✗ Codex テストエラー: {e}")
        return False


def test_claude(prompt: str = "Hello, this is a test.") -> bool:
    """Claudeラッパーをテスト"""
    try:
        resp = requests.post(
            f"{CLAUDE_URL}/claude",
            json={"prompt": prompt, "history": []},
            timeout=130
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ Claude テスト成功")
            print(f"  レスポンス: {data.get('output', '')[:100]}...")
            return True
        else:
            print(f"✗ Claude テスト失敗: HTTP {resp.status_code}, {resp.text}")
            return False
    except Exception as e:
        print(f"✗ Claude テストエラー: {e}")
        return False


def main():
    print("=" * 60)
    print("ホストラッパーの動作確認")
    print("=" * 60)
    print()

    # ヘルスチェック
    print("1. ヘルスチェック確認中...")
    codex_ok = check_health(CODEX_URL, "Codex")
    claude_ok = check_health(CLAUDE_URL, "Claude")
    print()

    if not codex_ok or not claude_ok:
        print("⚠ ヘルスチェックに失敗しました。")
        print("  以下のコマンドでサーバーを起動してください:")
        print("  cd host_wrappers")
        print("  source .venv/bin/activate")
        print("  python codex_wrapper.py    # ターミナル1")
        print("  python claude_wrapper.py   # ターミナル2")
        sys.exit(1)

    # 実際のAPI呼び出しテスト
    print("2. API呼び出しテスト中...")
    print("   (codex/claudecode CLIがインストールされている必要があります)")
    print()

    test_prompt = "PythonでHello Worldを出力するコードを書いてください。"
    codex_test_ok = test_codex(test_prompt)
    print()
    claude_test_ok = test_claude(test_prompt)
    print()

    if codex_test_ok and claude_test_ok:
        print("=" * 60)
        print("✓ すべてのテストが成功しました！")
        print("=" * 60)
        print()
        print("次のステップ:")
        print("1. Dockerコンテナを起動: cd docker && docker compose up -d")
        print("2. CursorでMCPソースを追加: http://localhost:8080")
        print("3. start_debateツールを使用して議論を開始")
    else:
        print("=" * 60)
        print("⚠ 一部のテストが失敗しました")
        print("=" * 60)
        print()
        print("確認事項:")
        print("- codex/claudecode CLIがインストールされているか")
        print("- CLIがPATHに含まれているか")
        print("- CLIが正常に動作するか（直接実行して確認）")
        sys.exit(1)


if __name__ == "__main__":
    main()

