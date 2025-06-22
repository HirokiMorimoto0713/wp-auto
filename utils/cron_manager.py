"""
Cronジョブ管理とプロセス制御
"""

import os
import sys
import fcntl
import signal
import time
from typing import Optional, Callable
from contextlib import contextmanager

class CronManager:
    """Cronジョブの多重起動防止とプロセス管理"""
    
    def __init__(self, lock_file: str = "/tmp/wp-auto.lockfile"):
        """
        CronManagerの初期化
        
        Args:
            lock_file: ロックファイルのパス
        """
        self.lock_file = lock_file
        self.lock_fd = None
        self.start_time = time.time()
    
    @contextmanager
    def exclusive_lock(self, timeout: int = 0):
        """
        排他ロックのコンテキストマネージャー
        
        Args:
            timeout: タイムアウト秒数（0の場合は即座に失敗）
            
        Yields:
            ロックが取得できた場合はTrue、そうでなければ例外
        """
        try:
            # ロックファイルを開く
            self.lock_fd = open(self.lock_file, 'w')
            
            # 非ブロッキングロックを試行
            if timeout == 0:
                # 即座に失敗
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:
                # タイムアウト付きでロック取得を試行
                start_time = time.time()
                while True:
                    try:
                        fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except IOError:
                        if time.time() - start_time > timeout:
                            raise TimeoutError(f"ロック取得がタイムアウトしました: {timeout}秒")
                        time.sleep(0.1)
            
            # プロセスIDを書き込み
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            
            print(f"✅ 排他ロック取得: {self.lock_file} (PID: {os.getpid()})")
            yield True
            
        except IOError as e:
            print(f"❌ 他のプロセスが実行中です: {e}")
            print("前のプロセスが完了するまでお待ちください。")
            raise
        except TimeoutError as e:
            print(f"❌ {e}")
            raise
        finally:
            # ロックを解放
            if self.lock_fd:
                try:
                    fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                    self.lock_fd.close()
                    # ロックファイルを削除
                    if os.path.exists(self.lock_file):
                        os.unlink(self.lock_file)
                    print(f"✅ 排他ロック解放: {self.lock_file}")
                except Exception as e:
                    print(f"⚠️ ロック解放エラー: {e}")
                finally:
                    self.lock_fd = None
    
    def setup_signal_handlers(self):
        """シグナルハンドラーを設定"""
        def signal_handler(signum, frame):
            print(f"\n🛑 シグナル {signum} を受信しました。プロセスを終了します...")
            self.cleanup()
            sys.exit(0)
        
        # SIGTERM, SIGINTハンドラーを設定
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def cleanup(self):
        """クリーンアップ処理"""
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
                if os.path.exists(self.lock_file):
                    os.unlink(self.lock_file)
                print("✅ クリーンアップ完了")
            except Exception as e:
                print(f"⚠️ クリーンアップエラー: {e}")
    
    def run_with_lock(self, func: Callable, *args, **kwargs):
        """
        排他ロック付きで関数を実行
        
        Args:
            func: 実行する関数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数
            
        Returns:
            関数の戻り値
        """
        self.setup_signal_handlers()
        
        try:
            with self.exclusive_lock():
                print(f"🚀 プロセス開始: {func.__name__}")
                result = func(*args, **kwargs)
                
                # 実行時間を計算
                execution_time = time.time() - self.start_time
                print(f"✅ プロセス完了: {func.__name__} (実行時間: {execution_time:.2f}秒)")
                
                return result
                
        except (IOError, TimeoutError):
            # 既に他のプロセスが実行中
            print("📋 スキップ: 他のプロセスが実行中のため、この実行をスキップします。")
            return None
        except Exception as e:
            print(f"❌ プロセス実行エラー: {e}")
            raise
        finally:
            self.cleanup()
    
    @staticmethod
    def generate_cron_command(script_path: str, 
                            log_file: str = "logs/cron.log",
                            lock_file: str = "/tmp/wp-auto.lockfile") -> str:
        """
        flockを使用したCronコマンドを生成
        
        Args:
            script_path: 実行するスクリプトのパス
            log_file: ログファイルのパス
            lock_file: ロックファイルのパス
            
        Returns:
            Cronコマンド文字列
        """
        abs_script_path = os.path.abspath(script_path)
        script_dir = os.path.dirname(abs_script_path)
        
        return f'/usr/bin/flock -n {lock_file} -c "cd {script_dir} && python3 {os.path.basename(abs_script_path)}" >> {log_file} 2>&1'
    
    @staticmethod
    def print_cron_setup_guide(script_path: str = "post_article.py"):
        """
        Cron設定ガイドを表示
        
        Args:
            script_path: スクリプトパス
        """
        current_dir = os.getcwd()
        cron_command = CronManager.generate_cron_command(
            os.path.join(current_dir, script_path)
        )
        
        print("\n" + "="*60)
        print("🕐 改善されたCron設定ガイド")
        print("="*60)
        print()
        print("以下のコマンドでcrontabを編集してください：")
        print("  crontab -e")
        print()
        print("以下の行を追加してください：")
        print("  # WordPress自動記事投稿（多重起動防止付き）")
        print(f"  0 8,12,18 * * * {cron_command}")
        print()
        print("改善点：")
        print("  ✅ flockによる多重起動防止")
        print("  ✅ ログファイルへの出力")
        print("  ✅ エラーログも記録")
        print("  ✅ 前のプロセス完了まで待機")
        print()
        print("ログの確認方法：")
        print(f"  tail -f {current_dir}/logs/cron.log")
        print("="*60)
        print()

# 使用例関数
def example_cron_job():
    """Cronジョブの例"""
    print("記事生成処理を開始...")
    time.sleep(2)  # 実際の処理をシミュレート
    print("記事生成処理完了")
    return "success"

if __name__ == "__main__":
    # 使用例
    cron_manager = CronManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "guide":
        # Cron設定ガイドを表示
        cron_manager.print_cron_setup_guide()
    else:
        # 実際の処理を実行
        result = cron_manager.run_with_lock(example_cron_job)
        print(f"結果: {result}") 