#!/usr/bin/env python3
"""
スタイル付きキーワード記事生成モードの設定スクリプト
"""
import os
import shutil
from datetime import datetime

def setup_style_mode():
    env_file = ".env"
    backup_file = f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print("=== スタイル付きキーワードモード設定 ===")
    
    # バックアップ作成
    if os.path.exists(env_file):
        shutil.copy(env_file, backup_file)
        print(f"✅ バックアップ作成: {backup_file}")
    
    # 現在の設定を読み込み
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    print()
    print("参考記事を指定してください（スタイル抽出用）:")
    print("1. URL指定 - WebサイトのURLをカンマ区切りで入力")
    print("2. ファイル指定 - ローカルファイルパスをカンマ区切りで入力")
    print("3. 両方指定 - URLとファイルを混合")
    print()
    
    choice = input("選択 (1/2/3): ").strip()
    
    reference_urls = ""
    reference_files = ""
    
    if choice in ["1", "3"]:
        print("📎 参考記事のURLをカンマ区切りで入力してください:")
        print("例: https://example1.com/article1,https://example2.com/article2")
        reference_urls = input("REFERENCE_URLS: ").strip()
    
    if choice in ["2", "3"]:
        print("📄 参考記事のファイルパスをカンマ区切りで入力してください:")
        print("例: ./reference/sample1.md,./reference/sample2.md")
        reference_files = input("REFERENCE_FILES: ").strip()
    
    if not reference_urls and not reference_files:
        print("❌ 参考記事が指定されていません。終了します。")
        return
    
    # デバッグモード設定
    print()
    debug_mode = input("🔍 デバッグモード（生成されたスタイルを表示）を有効にしますか？ (y/N): ").strip().lower()
    debug_style = "true" if debug_mode == "y" else "false"
    
    # 環境変数を更新
    env_vars['REFERENCE_MODE'] = 'style_with_keywords'
    env_vars['USE_STYLE_GUIDE'] = 'true'
    env_vars['DEBUG_STYLE'] = debug_style
    
    if reference_urls:
        env_vars['REFERENCE_URLS'] = reference_urls
    if reference_files:
        env_vars['REFERENCE_FILES'] = reference_files
    
    # .envファイルを書き込み
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# WordPress設定\n")
        f.write(f"WP_URL={env_vars.get('WP_URL', 'https://your-site.com')}\n")
        f.write(f"WP_USER={env_vars.get('WP_USER', 'your_username')}\n")
        f.write(f"WP_APP_PASS={env_vars.get('WP_APP_PASS', 'your_app_password')}\n")
        f.write("\n")
        f.write("# OpenAI設定\n")
        f.write(f"OPENAI_API_KEY={env_vars.get('OPENAI_API_KEY', 'your_openai_api_key')}\n")
        f.write("\n")
        f.write("# 参考記事設定\n")
        f.write("# style_with_keywords: 参考記事のスタイル + keywords.csvの組み合わせ\n")
        f.write("REFERENCE_MODE=style_with_keywords\n")
        f.write("\n")
        
        if reference_urls:
            f.write("# 複数参考記事URL（カンマ区切り）\n")
            f.write(f"REFERENCE_URLS={reference_urls}\n")
        
        if reference_files:
            f.write("# 複数参考記事ファイル（カンマ区切り）\n")
            f.write(f"REFERENCE_FILES={reference_files}\n")
        
        f.write("\n")
        f.write("# スタイルガイド機能設定\n")
        f.write("USE_STYLE_GUIDE=true\n")
        f.write(f"DEBUG_STYLE={debug_style}\n")
        
        # その他の設定があれば保持
        other_vars = ['ARTICLE_THEME']
        for var in other_vars:
            if var in env_vars:
                f.write(f"{var}={env_vars[var]}\n")
    
    print()
    print("✅ スタイル付きキーワードモードを設定しました")
    print()
    print("📋 設定内容:")
    print(f"   モード: style_with_keywords")
    if reference_urls:
        print(f"   参考URL: {len(reference_urls.split(','))}個")
    if reference_files:
        print(f"   参考ファイル: {len(reference_files.split(','))}個")
    print(f"   デバッグ: {debug_style}")
    print()
    print("🚀 記事生成実行:")
    print("python post_article.py")

if __name__ == "__main__":
    setup_style_mode() 
