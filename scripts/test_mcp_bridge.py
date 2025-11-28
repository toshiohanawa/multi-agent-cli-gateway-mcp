"""
MCPブリッジの動作確認用スクリプト
"""
import requests
import sys

MCP_URL = "http://localhost:8080"


def check_health() -> bool:
    """MCPブリッジのヘルスチェック"""
    try:
        resp = requests.get(f"{MCP_URL}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ MCPブリッジ ヘルスチェック成功")
            print(f"  状態: {data}")
            return True
        else:
            print(f"✗ MCPブリッジ ヘルスチェック失敗: HTTP {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ MCPブリッジに接続できません。")
        print(f"  Dockerコンテナが起動しているか確認してください:")
        print(f"  cd docker && docker compose up -d")
        return False
    except Exception as e:
        print(f"✗ エラー: {e}")
        return False


def test_start_debate(prompt: str = "PythonでFizzBuzzを実装してください。") -> bool:
    """start_debateエンドポイントをテスト"""
    try:
        resp = requests.post(
            f"{MCP_URL}/start_debate",
            json={"initial_prompt": prompt},
            timeout=250
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ start_debate 成功")
            if "turn" in data:
                turn = data["turn"]
                print(f"  ユーザー指示: {turn.get('user_instruction', '')[:80]}...")
                print(f"  Codex出力: {turn.get('codex_output', '')[:80]}...")
                print(f"  Claude出力: {turn.get('claude_output', '')[:80]}...")
            return True
        else:
            print(f"✗ start_debate 失敗: HTTP {resp.status_code}, {resp.text}")
            return False
    except Exception as e:
        print(f"✗ start_debate エラー: {e}")
        return False


def test_step(decision_type: str = "adopt_codex", custom_text: str = None) -> bool:
    """stepエンドポイントをテスト"""
    try:
        decision = {"type": decision_type}
        if custom_text:
            decision["custom_text"] = custom_text

        resp = requests.post(
            f"{MCP_URL}/step",
            json={"decision": decision},
            timeout=250
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ step 成功 (decision: {decision_type})")
            if "turn" in data:
                turn = data["turn"]
                print(f"  ユーザー指示: {turn.get('user_instruction', '')[:80]}...")
                print(f"  Codex出力: {turn.get('codex_output', '')[:80]}...")
                print(f"  Claude出力: {turn.get('claude_output', '')[:80]}...")
            return True
        else:
            print(f"✗ step 失敗: HTTP {resp.status_code}, {resp.text}")
            return False
    except Exception as e:
        print(f"✗ step エラー: {e}")
        return False


def test_stop() -> bool:
    """stopエンドポイントをテスト"""
    try:
        resp = requests.post(f"{MCP_URL}/stop", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ stop 成功: {data}")
            return True
        else:
            print(f"✗ stop 失敗: HTTP {resp.status_code}, {resp.text}")
            return False
    except Exception as e:
        print(f"✗ stop エラー: {e}")
        return False


def main():
    print("=" * 60)
    print("MCPブリッジの動作確認")
    print("=" * 60)
    print()

    # ヘルスチェック
    print("1. ヘルスチェック確認中...")
    if not check_health():
        sys.exit(1)
    print()

    # start_debateテスト
    print("2. start_debate テスト中...")
    test_prompt = "PythonでFizzBuzzを実装してください。"
    if not test_start_debate(test_prompt):
        print("⚠ start_debateが失敗しました。")
        print("  ホストラッパー（ポート9001, 9002）が起動しているか確認してください。")
        sys.exit(1)
    print()

    # stepテスト（adopt_codex）
    print("3. step テスト中 (adopt_codex)...")
    if not test_step("adopt_codex"):
        print("⚠ stepが失敗しました。")
        sys.exit(1)
    print()

    # stepテスト（adopt_claude）
    print("4. step テスト中 (adopt_claude)...")
    if not test_step("adopt_claude"):
        print("⚠ stepが失敗しました。")
        sys.exit(1)
    print()

    # stepテスト（custom_instruction）
    print("5. step テスト中 (custom_instruction)...")
    if not test_step("custom_instruction", "より効率的な実装を提案してください。"):
        print("⚠ stepが失敗しました。")
        sys.exit(1)
    print()

    # stopテスト
    print("6. stop テスト中...")
    if not test_stop():
        print("⚠ stopが失敗しました。")
        sys.exit(1)
    print()

    print("=" * 60)
    print("✓ すべてのテストが成功しました！")
    print("=" * 60)
    print()
    print("次のステップ:")
    print("1. CursorでMCPソースを追加: http://localhost:8080")
    print("2. start_debate, step, stopツールを使用して議論を開始")


if __name__ == "__main__":
    main()

