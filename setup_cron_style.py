#!/usr/bin/env python3
"""
Cron用スタイル付きキーワードモード設定（非対話型）
"""
import os
import shutil
import sys
from datetime import datetime

def setup_cron_style_mode(reference_sources, debug=False):
    """
    Cron実行用のスタイル付きキーワードモード設定
    
    Args:
        reference_sources: 参考記事のURL/ファイルパスのリスト
        debug: デバッグモードの有効/無効
    """
    env_file = ".env"
    backup_file = f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print("=== Cron用スタイル付きキーワードモード設定 ===")
    
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
    
    # URLとファイルを分離
    urls = [s for s in reference_sources if s.startswith('http')]
    files = [s for s in reference_sources if not s.startswith('http')]
    
    # 環境変数を更新
    env_vars['REFERENCE_MODE'] = 'style_with_keywords'
    env_vars['USE_STYLE_GUIDE'] = 'true'
    env_vars['DEBUG_STYLE'] = 'true' if debug else 'false'
    
    if urls:
        env_vars['REFERENCE_URLS'] = ','.join(urls)
    if files:
        env_vars['REFERENCE_FILES'] = ','.join(files)
    
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
        
        if urls:
            f.write("# 複数参考記事URL（カンマ区切り）\n")
            f.write(f"REFERENCE_URLS={','.join(urls)}\n")
        
        if files:
            f.write("# 複数参考記事ファイル（カンマ区切り）\n")
            f.write(f"REFERENCE_FILES={','.join(files)}\n")
        
        f.write("\n")
        f.write("# スタイルガイド機能設定\n")
        f.write("USE_STYLE_GUIDE=true\n")
        f.write(f"DEBUG_STYLE={'true' if debug else 'false'}\n")
        
        # その他の設定があれば保持
        other_vars = ['ARTICLE_THEME']
        for var in other_vars:
            if var in env_vars:
                f.write(f"{var}={env_vars[var]}\n")
    
    print("✅ Cron用スタイル付きキーワードモードを設定しました")
    print()
    print("📋 設定内容:")
    print(f"   モード: style_with_keywords")
    if urls:
        print(f"   参考URL: {len(urls)}個")
    if files:
        print(f"   参考ファイル: {len(files)}個")
    print(f"   デバッグ: {'有効' if debug else '無効'}")
    print()
    print("🤖 Cron設定例:")
    cron_path = os.path.abspath(".")
    print(f"# 毎日3回（9時、13時、18時）記事自動生成")
    print(f"0 9,13,18 * * * cd {cron_path} && /usr/bin/python3 post_article.py >> cron.log 2>&1")
    print()
    print("🚀 手動テスト実行:")
    print("python post_article.py")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法:")
        print("python setup_cron_style.py 'URL1,URL2,URL3' [debug]")
        print()
        print("例:")
        print("python setup_cron_style.py 'https://example1.com/article1,https://example2.com/article2'")
        print("python setup_cron_style.py './reference/sample1.md,./reference/sample2.md' debug")
        sys.exit(1)
    
    # 参考記事ソースを取得
    sources_str = sys.argv[1]
    sources = [s.strip() for s in sources_str.split(',') if s.strip()]
    
    # デバッグモードチェック
    debug_mode = len(sys.argv) > 2 and sys.argv[2].lower() == 'debug'
    
    if not sources:
        print("❌ 参考記事が指定されていません")
        sys.exit(1)
    
    setup_cron_style_mode(sources, debug_mode) 
