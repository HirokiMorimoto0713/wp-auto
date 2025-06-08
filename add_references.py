#!/usr/bin/env python3
"""
AI GENE記事をリファレンスに追加するスクリプト
"""
import os
import shutil
from datetime import datetime

def add_ai_gene_references():
    env_file = ".env"
    backup_file = f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 追加するAI GENE記事
    new_urls = [
        "https://ai-gene.jp/ai-writing-prompt-guide",
        "https://ai-gene.jp/ai-writing-beginner-guide"
    ]
    
    print("=== AI GENE記事をリファレンスに追加 ===")
    print("追加記事:")
    for i, url in enumerate(new_urls, 1):
        print(f"  {i}. {url}")
    print()
    
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
    
    # 既存のREFERENCE_URLsを取得
    existing_urls = env_vars.get('REFERENCE_URLS', '').split(',') if env_vars.get('REFERENCE_URLS') else []
    existing_urls = [url.strip() for url in existing_urls if url.strip()]
    
    # 新しいURLを追加（重複除去）
    all_urls = existing_urls.copy()
    for url in new_urls:
        if url not in all_urls:
            all_urls.append(url)
    
    # 環境変数を更新
    env_vars['REFERENCE_MODE'] = 'style_with_keywords'
    env_vars['REFERENCE_URLS'] = ','.join(all_urls)
    env_vars['USE_STYLE_GUIDE'] = 'true'
    env_vars['DEBUG_STYLE'] = 'false'
    
    # .envファイルを更新
    with open(env_file, 'w', encoding='utf-8') as f:
        # WordPress設定
        f.write("# WordPress設定\n")
        f.write(f"WP_URL={env_vars.get('WP_URL', 'https://your-site.com')}\n")
        f.write(f"WP_USER={env_vars.get('WP_USER', 'your_username')}\n")
        f.write(f"WP_APP_PASS={env_vars.get('WP_APP_PASS', 'your_app_password')}\n")
        f.write("\n")
        
        # OpenAI設定
        f.write("# OpenAI設定\n")
        f.write(f"OPENAI_API_KEY={env_vars.get('OPENAI_API_KEY', 'your_openai_api_key')}\n")
        f.write("\n")
        
        # 参考記事設定
        f.write("# 参考記事設定\n")
        f.write("REFERENCE_MODE=style_with_keywords\n")
        f.write("\n")
        
        # 参考記事URL（AI GENE記事を含む）
        f.write("# 参考記事URL（AI GENE記事を含む）\n")
        f.write(f"REFERENCE_URLS={','.join(all_urls)}\n")
        f.write("\n")
        
        # 参考記事ファイル（既存があれば保持）
        if env_vars.get('REFERENCE_FILES'):
            f.write("# 参考記事ファイル\n")
            f.write(f"REFERENCE_FILES={env_vars['REFERENCE_FILES']}\n")
            f.write("\n")
        
        # スタイルガイド設定
        f.write("# スタイルガイド機能設定\n")
        f.write("USE_STYLE_GUIDE=true\n")
        f.write("DEBUG_STYLE=false\n")
        
        # その他の設定があれば保持
        other_vars = ['ARTICLE_THEME', 'ENABLE_IMAGE_GENERATION']
        for var in other_vars:
            if var in env_vars:
                f.write(f"{var}={env_vars[var]}\n")
    
    print("✅ AI GENE記事をリファレンスに追加しました")
    print()
    print("📋 更新後の設定:")
    print(f"   モード: style_with_keywords")
    print(f"   参考記事数: {len(all_urls)}個")
    print("   参考記事:")
    for i, url in enumerate(all_urls, 1):
        if url in new_urls:
            print(f"     {i}. {url} ← ✨ 新規追加")
        else:
            print(f"     {i}. {url}")
    print()
    print("🚀 記事生成テスト:")
    print("python post_article.py")
    print()
    print("📈 期待される効果:")
    print("   - AI GENE記事のスタイル（表・具体例・実践的な内容）を学習")
    print("   - プロンプト例やテンプレートを含む記事生成")
    print("   - 初心者にもわかりやすい構成")

if __name__ == "__main__":
    add_ai_gene_references() 
