"""
ログ管理の改善
標準出力/標準エラー出力を使用してGCP Cloud Loggingに対応
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class LogLevel(Enum):
    """ログレベル"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogManager:
    """改善されたログ管理クラス"""
    
    def __init__(self, 
                 service_name: str = "wp-auto",
                 enable_cloud_logging: bool = True,
                 enable_file_logging: bool = False,
                 log_file: str = "logs/app.log"):
        """
        ログマネージャーの初期化
        
        Args:
            service_name: サービス名
            enable_cloud_logging: Cloud Logging有効化
            enable_file_logging: ファイルログ有効化
            log_file: ログファイルパス
        """
        self.service_name = service_name
        self.enable_cloud_logging = enable_cloud_logging
        self.enable_file_logging = enable_file_logging
        self.log_file = log_file
        
        # ログディレクトリを作成
        if enable_file_logging:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Pythonロガーの設定
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)
        
        # ハンドラーの設定
        self._setup_handlers()
    
    def _setup_handlers(self):
        """ログハンドラーの設定"""
        # 既存のハンドラーをクリア
        self.logger.handlers.clear()
        
        # 標準出力ハンドラー（Cloud Logging用）
        if self.enable_cloud_logging:
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setLevel(logging.INFO)
            stdout_handler.setFormatter(self._get_cloud_formatter())
            self.logger.addHandler(stdout_handler)
            
            # エラー用標準エラー出力ハンドラー
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setLevel(logging.ERROR)
            stderr_handler.setFormatter(self._get_cloud_formatter())
            self.logger.addHandler(stderr_handler)
        
        # ファイルハンドラー（オプション）
        if self.enable_file_logging:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(self._get_file_formatter())
            self.logger.addHandler(file_handler)
    
    def _get_cloud_formatter(self) -> logging.Formatter:
        """Cloud Logging用のフォーマッター"""
        return logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _get_file_formatter(self) -> logging.Formatter:
        """ファイル用のフォーマッター"""
        return logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _create_structured_log(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """構造化ログエントリを作成"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'severity': level,
            'service': self.service_name,
            'message': message,
        }
        
        # 追加フィールドを含める
        if kwargs:
            log_entry.update(kwargs)
        
        return log_entry
    
    def info(self, message: str, **kwargs):
        """情報ログ"""
        if self.enable_cloud_logging:
            # 構造化ログとして出力
            log_entry = self._create_structured_log('INFO', message, **kwargs)
            print(json.dumps(log_entry, ensure_ascii=False))
        else:
            self.logger.info(message)
    
    def debug(self, message: str, **kwargs):
        """デバッグログ"""
        if self.enable_cloud_logging:
            log_entry = self._create_structured_log('DEBUG', message, **kwargs)
            print(json.dumps(log_entry, ensure_ascii=False))
        else:
            self.logger.debug(message)
    
    def warning(self, message: str, **kwargs):
        """警告ログ"""
        if self.enable_cloud_logging:
            log_entry = self._create_structured_log('WARNING', message, **kwargs)
            print(json.dumps(log_entry, ensure_ascii=False))
        else:
            self.logger.warning(message)
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """エラーログ"""
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_message'] = str(error)
            kwargs['traceback'] = traceback.format_exc()
        
        if self.enable_cloud_logging:
            log_entry = self._create_structured_log('ERROR', message, **kwargs)
            print(json.dumps(log_entry, ensure_ascii=False), file=sys.stderr)
        else:
            self.logger.error(message, exc_info=error is not None)
    
    def critical(self, message: str, error: Exception = None, **kwargs):
        """重要エラーログ"""
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_message'] = str(error)
            kwargs['traceback'] = traceback.format_exc()
        
        if self.enable_cloud_logging:
            log_entry = self._create_structured_log('CRITICAL', message, **kwargs)
            print(json.dumps(log_entry, ensure_ascii=False), file=sys.stderr)
        else:
            self.logger.critical(message, exc_info=error is not None)
    
    def log_process_start(self, process_name: str, **kwargs):
        """プロセス開始ログ"""
        self.info(f"🚀 プロセス開始: {process_name}", 
                 process_name=process_name, 
                 event_type="process_start", 
                 **kwargs)
    
    def log_process_end(self, process_name: str, execution_time: float = None, **kwargs):
        """プロセス終了ログ"""
        message = f"✅ プロセス完了: {process_name}"
        if execution_time:
            message += f" (実行時間: {execution_time:.2f}秒)"
        
        self.info(message, 
                 process_name=process_name, 
                 event_type="process_end",
                 execution_time=execution_time,
                 **kwargs)
    
    def log_article_generation(self, keyword: str, title: str, success: bool = True, **kwargs):
        """記事生成ログ"""
        if success:
            self.info(f"📝 記事生成成功: {title}", 
                     keyword=keyword, 
                     title=title, 
                     event_type="article_generated",
                     **kwargs)
        else:
            self.error(f"❌ 記事生成失敗: {keyword}", 
                      keyword=keyword, 
                      event_type="article_generation_failed",
                      **kwargs)
    
    def log_wordpress_post(self, title: str, post_id: int = None, success: bool = True, **kwargs):
        """WordPress投稿ログ"""
        if success:
            self.info(f"📤 WordPress投稿成功: {title}", 
                     title=title, 
                     post_id=post_id,
                     event_type="wordpress_posted",
                     **kwargs)
        else:
            self.error(f"❌ WordPress投稿失敗: {title}", 
                      title=title, 
                      event_type="wordpress_post_failed",
                      **kwargs)
    
    def log_image_generation(self, prompt: str, image_url: str = None, success: bool = True, **kwargs):
        """画像生成ログ"""
        if success:
            self.info(f"🎨 画像生成成功", 
                     prompt=prompt[:100], 
                     image_url=image_url,
                     event_type="image_generated",
                     **kwargs)
        else:
            self.error(f"❌ 画像生成失敗", 
                      prompt=prompt[:100], 
                      event_type="image_generation_failed",
                      **kwargs)
    
    def log_seo_analysis(self, title: str, seo_score: int, grade: str, **kwargs):
        """SEO分析ログ"""
        self.info(f"📊 SEO分析完了: {title} (スコア: {seo_score}, グレード: {grade})", 
                 title=title, 
                 seo_score=seo_score,
                 seo_grade=grade,
                 event_type="seo_analyzed",
                 **kwargs)
    
    def log_cron_execution(self, script_name: str, success: bool = True, **kwargs):
        """Cron実行ログ"""
        if success:
            self.info(f"⏰ Cron実行成功: {script_name}", 
                     script_name=script_name,
                     event_type="cron_executed",
                     **kwargs)
        else:
            self.error(f"❌ Cron実行失敗: {script_name}", 
                      script_name=script_name,
                      event_type="cron_execution_failed",
                      **kwargs)
    
    @staticmethod
    def setup_cloud_logging_guide():
        """Cloud Logging設定ガイドを表示"""
        print("\n" + "="*60)
        print("☁️ GCP Cloud Logging設定ガイド")
        print("="*60)
        print()
        print("1. GCPプロジェクトでCloud Loggingを有効化")
        print("2. サービスアカウントに適切な権限を付与")
        print("3. 環境変数GOOGLE_APPLICATION_CREDENTIALSを設定")
        print()
        print("ログの確認方法：")
        print("1. GCPコンソール → Logging → ログエクスプローラー")
        print("2. フィルタ例：")
        print('   resource.type="gce_instance"')
        print('   jsonPayload.service="wp-auto"')
        print('   jsonPayload.event_type="article_generated"')
        print()
        print("アラート設定：")
        print("1. ログベースのメトリクスを作成")
        print("2. アラートポリシーを設定")
        print("3. 通知チャンネルを設定（メール、Slack等）")
        print("="*60)
        print()

# グローバルインスタンス
log_manager = LogManager()

# 便利な関数
def log_info(message: str, **kwargs):
    """情報ログの便利関数"""
    log_manager.info(message, **kwargs)

def log_error(message: str, error: Exception = None, **kwargs):
    """エラーログの便利関数"""
    log_manager.error(message, error, **kwargs)

def log_warning(message: str, **kwargs):
    """警告ログの便利関数"""
    log_manager.warning(message, **kwargs)

if __name__ == "__main__":
    # 使用例
    if len(sys.argv) > 1 and sys.argv[1] == "guide":
        LogManager.setup_cloud_logging_guide()
    else:
        # テストログ
        log_manager.info("テストログメッセージ", test_param="test_value")
        log_manager.error("テストエラー", error=Exception("テスト例外")) 