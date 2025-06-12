#!/usr/bin/env python3
"""
複数WordPressサイトの一括管理スクリプト
"""
import os
import sys
import glob
import subprocess
from datetime import datetime
import json

def find_wp_auto_directories():
    """wp-auto*のディレクトリを検索"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_path)
    
    wp_dirs = []
    for path in glob.glob(f"{parent_dir}/wp-auto*"):
        if os.path.isdir(path) and os.path.exists(f"{path}/.env"):
            wp_dirs.append(path)
    
    return sorted(wp_dirs)

def get_site_info(directory):
    """サイト情報を取得"""
    env_file = f"{directory}/.env"
    info = {
        "name": os.path.basename(directory),
        "path": directory,
        "wp_url": "",
        "theme": "",
        "keywords_count": 0,
        "current_index": 0,
        "last_run": "未実行",
        "status": "不明"
    }
    
    # .envから情報を取得
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('WP_URL='):
                        info["wp_url"] = line.split('=', 1)[1]
                    elif line.startswith('ARTICLE_THEME='):
                        info["theme"] = line.split('=', 1)[1]
        except Exception as e:
            info["status"] = f"設定読み込みエラー: {e}"
    
    # キーワード数を取得
    keywords_file = f"{directory}/keywords.csv"
    if os.path.exists(keywords_file):
        try:
            with open(keywords_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                info["keywords_count"] = len(lines) - 1  # ヘッダー行を除く
        except:
            pass
    
    # 現在のインデックスを取得
    for index_file in ['current_index.txt', 'last_index.txt']:
        index_path = f"{directory}/{index_file}"
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    info["current_index"] = int(f.read().strip())
                break
            except:
                pass
    
    # 最後の実行時間を取得
    log_files = glob.glob(f"{directory}/logs/*.log")
    if log_files:
        latest_log = max(log_files, key=os.path.getmtime)
        info["last_run"] = datetime.fromtimestamp(os.path.getmtime(latest_log)).strftime('%Y-%m-%d %H:%M')
    
    # ステータス判定
    if info["wp_url"] and info["keywords_count"] > 0:
        progress = (info["current_index"] / info["keywords_count"]) * 100 if info["keywords_count"] > 0 else 0
        info["status"] = f"稼働中 ({progress:.1f}%完了)"
    else:
        info["status"] = "設定不完全"
    
    return info

def list_sites():
    """サイト一覧を表示"""
    directories = find_wp_auto_directories()
    
    if not directories:
        print("❌ wp-auto*ディレクトリが見つかりません")
        return
    
    print("📋 WordPressサイト一覧\n")
    print(f"{'No.':<3} {'サイト名':<20} {'URL':<30} {'テーマ':<20} {'進捗':<15} {'最終実行':<16} {'ステータス'}")
    print("-" * 120)
    
    for i, directory in enumerate(directories, 1):
        info = get_site_info(directory)
        progress = f"{info['current_index']}/{info['keywords_count']}"
        
        print(f"{i:<3} {info['name']:<20} {info['wp_url']:<30} {info['theme']:<20} {progress:<15} {info['last_run']:<16} {info['status']}")

def run_site(site_name, dry_run=False):
    """指定サイトで記事生成を実行"""
    directories = find_wp_auto_directories()
    target_dir = None
    
    for directory in directories:
        if site_name in os.path.basename(directory):
            target_dir = directory
            break
    
    if not target_dir:
        print(f"❌ サイト '{site_name}' が見つかりません")
        return False
    
    print(f"🚀 {os.path.basename(target_dir)} で記事生成を実行中...")
    
    if dry_run:
        print("🔍 ドライラン：実際には実行しません")
        return True
    
    try:
        # post_article.pyを実行
        result = subprocess.run(
            ["python3", "post_article.py"],
            cwd=target_dir,
            capture_output=True,
            text=True,
            timeout=1800  # 30分でタイムアウト
        )
        
        if result.returncode == 0:
            print("✅ 記事生成完了")
            print(f"出力: {result.stdout[-200:]}...")  # 最後の200文字を表示
            return True
        else:
            print(f"❌ 記事生成失敗: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ タイムアウト: 30分以内に完了しませんでした")
        return False
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        return False

def run_all_sites(dry_run=False):
    """全サイトで記事生成を実行"""
    directories = find_wp_auto_directories()
    
    if not directories:
        print("❌ wp-auto*ディレクトリが見つかりません")
        return
    
    results = []
    
    for directory in directories:
        site_name = os.path.basename(directory)
        print(f"\n{'='*50}")
        print(f"🚀 {site_name} で記事生成開始")
        print(f"{'='*50}")
        
        success = run_site(site_name, dry_run)
        results.append({"site": site_name, "success": success})
    
    # 結果サマリー
    print(f"\n{'='*50}")
    print("📊 実行結果サマリー")
    print(f"{'='*50}")
    
    for result in results:
        status = "✅ 成功" if result["success"] else "❌ 失敗"
        print(f"{result['site']:<20} {status}")

def setup_cron_all():
    """全サイトのCronジョブ設定例を表示"""
    directories = find_wp_auto_directories()
    
    if not directories:
        print("❌ wp-auto*ディレクトリが見つかりません")
        return
    
    print("🕐 Cron設定例（すべてのサイト）\n")
    print("# 以下をcrontab -eで追加してください")
    print("# 各サイトを時間差で実行（サーバー負荷分散）")
    print()
    
    base_hours = [9, 13, 18]
    
    for i, directory in enumerate(directories):
        site_name = os.path.basename(directory)
        abs_path = os.path.abspath(directory)
        
        # 各サイトを15分ずつずらす
        minutes = i * 15
        if minutes >= 60:
            minutes = minutes % 60
        
        for hour in base_hours:
            print(f"{minutes} {hour} * * * cd {abs_path} && /usr/bin/python3 post_article.py >> logs/cron.log 2>&1")
        
        print(f"# ↑ {site_name}")
        print()

def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("python3 manage_multiple_sites.py <command> [options]")
        print()
        print("コマンド:")
        print("  list                    - サイト一覧を表示")
        print("  run <site_name>         - 指定サイトで記事生成")
        print("  run-all                 - 全サイトで記事生成")
        print("  cron                    - Cron設定例を表示")
        print()
        print("例:")
        print("  python3 manage_multiple_sites.py list")
        print("  python3 manage_multiple_sites.py run tech-blog")
        print("  python3 manage_multiple_sites.py run-all")
        print("  python3 manage_multiple_sites.py cron")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_sites()
    elif command == "run" and len(sys.argv) > 2:
        site_name = sys.argv[2]
        dry_run = "--dry-run" in sys.argv
        run_site(site_name, dry_run)
    elif command == "run-all":
        dry_run = "--dry-run" in sys.argv
        run_all_sites(dry_run)
    elif command == "cron":
        setup_cron_all()
    else:
        print(f"❌ 不明なコマンド: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
