#!/usr/bin/env python3
"""
新しいWordPressサイト用の設定を作成するスクリプト
"""
import os
import sys
import shutil
from datetime import datetime

def setup_new_site(site_name, wp_url, wp_user, wp_app_pass, theme="", reference_urls="", keywords_list=""):
    """
    新しいサイト用のディレクトリと設定を作成
    """
    print(f"=== {site_name} 用設定を作成中 ===")
    
    # ディレクトリ作成
    base_dir = f"../wp-auto-{site_name}"
    if os.path.exists(base_dir):
        backup_dir = f"{base_dir}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.move(base_dir, backup_dir)
        print(f"✅ 既存ディレクトリをバックアップ: {backup_dir}")
    
    # 現在のディレクトリをコピー
    shutil.copytree(".", base_dir)
    print(f"✅ ディレクトリ作成完了: {base_dir}")
    
    # .envファイルを作成
    env_content = f"""# WordPress設定 - {site_name}
WP_URL={wp_url}
WP_USER={wp_user}
WP_APP_PASS={wp_app_pass}

# OpenAI設定
OPENAI_API_KEY=your_openai_api_key

# 参考記事設定
REFERENCE_MODE=style_with_keywords
USE_STYLE_GUIDE=true
DEBUG_STYLE=false

# サイトテーマ
ARTICLE_THEME={theme if theme else f"{site_name}の専門記事"}

# 参考記事URL（複数の場合はカンマ区切り）
REFERENCE_URLS={reference_urls}
"""
    
    with open(f"{base_dir}/.env", 'w', encoding='utf-8') as f:
        f.write(env_content)
    print(f"✅ .env設定完了")
    
    # keywords.csvを作成
    if keywords_list:
        keywords = keywords_list.split(',')
        with open(f"{base_dir}/keywords.csv", 'w', encoding='utf-8') as f:
            f.write("キーワード\n")
            for keyword in keywords:
                f.write(f"{keyword.strip()}\n")
        print(f"✅ キーワードファイル作成完了: {len(keywords)}個")
    
    # referenceディレクトリをクリア
    ref_dir = f"{base_dir}/reference"
    if os.path.exists(ref_dir):
        shutil.rmtree(ref_dir)
    os.makedirs(ref_dir)
    print(f"✅ 参考記事ディレクトリ準備完了")
    
    # logsディレクトリを作成
    logs_dir = f"{base_dir}/logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # インデックスファイルをリセット
    for index_file in ['current_index.txt', 'last_index.txt']:
        index_path = f"{base_dir}/{index_file}"
        if os.path.exists(index_path):
            with open(index_path, 'w') as f:
                f.write("0")
    
    print(f"\n🎉 {site_name} 用設定完成！")
    print(f"📁 ディレクトリ: {base_dir}")
    print(f"⚙️  設定ファイル: {base_dir}/.env")
    print(f"📝 キーワード: {base_dir}/keywords.csv")
    print()
    print("🚀 次のステップ:")
    print(f"1. cd {base_dir}")
    print("2. .envファイルのOPENAI_API_KEYを設定")
    print("3. python3 post_article.py でテスト実行")
    print()
    print("🕐 Cron設定例:")
    abs_path = os.path.abspath(base_dir)
    print(f"0 9,13,18 * * * cd {abs_path} && /usr/bin/python3 post_article.py >> logs/cron.log 2>&1")

def main():
    if len(sys.argv) < 5:
        print("使用方法:")
        print("python3 setup_new_site.py <サイト名> <WP_URL> <WP_USER> <WP_APP_PASS> [テーマ] [参考URL] [キーワード]")
        print()
        print("例:")
        print("python3 setup_new_site.py tech-blog https://tech-blog.com admin app_pass_123")
        print('python3 setup_new_site.py beauty-site https://beauty.com editor app_456 "美容とスキンケア" "https://example1.com,https://example2.com" "スキンケア,メイク,コスメ"')
        sys.exit(1)
    
    site_name = sys.argv[1]
    wp_url = sys.argv[2]
    wp_user = sys.argv[3] 
    wp_app_pass = sys.argv[4]
    theme = sys.argv[5] if len(sys.argv) > 5 else ""
    reference_urls = sys.argv[6] if len(sys.argv) > 6 else ""
    keywords_list = sys.argv[7] if len(sys.argv) > 7 else ""
    
    setup_new_site(site_name, wp_url, wp_user, wp_app_pass, theme, reference_urls, keywords_list)

if __name__ == "__main__":
    main() 
