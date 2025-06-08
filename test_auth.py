#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()
WP_URL = os.getenv("WP_URL").rstrip("/")
WP_USER = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")

print("=== WordPress認証テスト ===")
print(f"サイトURL: {WP_URL}")
print(f"ユーザー名: {WP_USER}")
print(f"アプリパス: {'*' * len(WP_APP_PASS) if WP_APP_PASS else 'None'}")
print()

# 1. サイト基本情報取得テスト
print("1. サイト基本情報取得テスト...")
try:
    resp = requests.get(f"{WP_URL}/wp-json/wp/v2/", timeout=10)
    if resp.status_code == 200:
        site_info = resp.json()
        print(f"✅ サイト接続成功: {site_info.get('name', 'Unknown Site')}")
    else:
        print(f"❌ サイト接続失敗: {resp.status_code}")
        print(f"レスポンス: {resp.text[:200]}")
except Exception as e:
    print(f"❌ サイト接続エラー: {e}")

print()

# 2. 認証付きユーザー情報取得テスト
print("2. 認証付きユーザー情報取得テスト...")
try:
    resp = requests.get(
        f"{WP_URL}/wp-json/wp/v2/users/me",
        auth=(WP_USER, WP_APP_PASS),
        timeout=10
    )
    if resp.status_code == 200:
        user_info = resp.json()
        print(f"✅ 認証成功")
        print(f"   ユーザーID: {user_info.get('id')}")
        print(f"   表示名: {user_info.get('name')}")
        print(f"   権限: {user_info.get('roles', [])}")
        print(f"   権限詳細: {user_info.get('capabilities', {})}")
    else:
        print(f"❌ 認証失敗: {resp.status_code}")
        print(f"レスポンス: {resp.text}")
except Exception as e:
    print(f"❌ 認証エラー: {e}")

print()

# 3. メディアアップロード権限テスト
print("3. メディアアップロード権限テスト...")
try:
    # 既存メディア一覧取得
    resp = requests.get(
        f"{WP_URL}/wp-json/wp/v2/media",
        auth=(WP_USER, WP_APP_PASS),
        params={"per_page": 1},
        timeout=10
    )
    if resp.status_code == 200:
        print("✅ メディア一覧取得成功")
        print("   → 画像アップロード権限は基本的にあると推測")
    else:
        print(f"❌ メディア一覧取得失敗: {resp.status_code}")
        print(f"レスポンス: {resp.text}")
except Exception as e:
    print(f"❌ メディアアクセスエラー: {e}")

print()

# 4. 投稿作成権限テスト
print("4. 投稿作成権限テスト...")
try:
    # テスト投稿作成（下書き）
    test_data = {
        "title": "認証テスト投稿（削除予定）",
        "content": "このテスト投稿は削除してください",
        "status": "draft"
    }
    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/posts",
        auth=(WP_USER, WP_APP_PASS),
        json=test_data,
        timeout=10
    )
    if resp.status_code == 201:
        post_info = resp.json()
        print("✅ 投稿作成成功")
        print(f"   投稿ID: {post_info.get('id')}")
        
        # テスト投稿を削除
        delete_resp = requests.delete(
            f"{WP_URL}/wp-json/wp/v2/posts/{post_info.get('id')}?force=true",
            auth=(WP_USER, WP_APP_PASS),
            timeout=10
        )
        if delete_resp.status_code == 200:
            print("✅ テスト投稿削除成功")
        else:
            print(f"⚠️ テスト投稿削除失敗（手動削除してください）: {delete_resp.status_code}")
            
    else:
        print(f"❌ 投稿作成失敗: {resp.status_code}")
        print(f"レスポンス: {resp.text}")
except Exception as e:
    print(f"❌ 投稿作成エラー: {e}")

print()
print("=== テスト完了 ===") 
