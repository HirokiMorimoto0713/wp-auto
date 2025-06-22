"""
wp-auto用の統一設定管理
環境変数とJSONファイルの両方に対応
"""

import os
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

class ConfigManager:
    """wp-auto用の設定管理クラス"""
    
    def __init__(self, env_file: str = ".env"):
        """
        設定管理器の初期化
        
        Args:
            env_file: .envファイルのパス
        """
        self.env_file = env_file
        
        # .envファイルを読み込み
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"✅ 環境変数ファイル読み込み: {env_file}")
        else:
            print(f"⚠️ 環境変数ファイルが見つかりません: {env_file}")
            print("   .envファイルを作成してください。")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key: 設定キー
            default: デフォルト値
            
        Returns:
            設定値
        """
        value = os.getenv(key, default)
        return self._convert_value(value) if isinstance(value, str) else value
    
    def _convert_value(self, value: str) -> Any:
        """
        文字列値を適切な型に変換
        """
        if value.lower() in ('true', 'yes', 'on', '1'):
            return True
        elif value.lower() in ('false', 'no', 'off', '0'):
            return False
        elif value.lower() == 'none' or value.lower() == 'null':
            return None
        elif ',' in value:
            # カンマ区切りの場合はリストに変換
            return [item.strip() for item in value.split(',')]
        elif value.isdigit():
            return int(value)
        elif self._is_float(value):
            return float(value)
        else:
            return value
    
    def _is_float(self, value: str) -> bool:
        """文字列が浮動小数点数かチェック"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def get_openai_config(self) -> Dict[str, Any]:
        """
        OpenAI設定を取得
        
        Returns:
            OpenAI設定辞書
        """
        return {
            'api_key': self.get('OPENAI_API_KEY', ''),
            'model': self.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            'max_tokens': self.get('OPENAI_MAX_TOKENS', 2000),
            'temperature': self.get('OPENAI_TEMPERATURE', 0.7)
        }
    
    def get_wordpress_config(self) -> Dict[str, Any]:
        """
        WordPress設定を取得
        
        Returns:
            WordPress設定辞書
        """
        return {
            'wp_url': self.get('WP_URL', '').rstrip('/'),
            'wp_user': self.get('WP_USER', ''),
            'wp_app_pass': self.get('WP_APP_PASS', ''),
            'post_status': self.get('WP_POST_STATUS', 'publish'),
            'category_id': self.get('WP_CATEGORY_ID', 1),
            'author_id': self.get('WP_AUTHOR_ID', 1)
        }
    
    def get_system_config(self) -> Dict[str, Any]:
        """
        システム設定を取得
        
        Returns:
            システム設定辞書
        """
        return {
            'log_level': self.get('LOG_LEVEL', 'INFO'),
            'debug_mode': self.get('DEBUG_MODE', False),
            'max_images': self.get('MAX_IMAGES', 6),
            'num_sections': self.get('NUM_SECTIONS', 5)
        }
    
    def validate_required_settings(self) -> List[str]:
        """
        必須設定の検証
        
        Returns:
            不足しているキーのリスト
        """
        required_keys = [
            'OPENAI_API_KEY',
            'WP_URL',
            'WP_USER',
            'WP_APP_PASS'
        ]
        
        missing_keys = []
        for key in required_keys:
            if not self.get(key):
                missing_keys.append(key)
        
        return missing_keys
    
    def print_config_summary(self):
        """設定の概要を表示"""
        print("\n=== wp-auto 設定概要 ===")
        
        # WordPress設定
        wp_config = self.get_wordpress_config()
        print(f"WordPress URL: {wp_config['wp_url']}")
        print(f"WordPress User: {wp_config['wp_user']}")
        print(f"投稿ステータス: {wp_config['post_status']}")
        
        # OpenAI設定
        openai_config = self.get_openai_config()
        api_key = openai_config['api_key']
        print(f"OpenAI API Key: {'設定済み' if api_key else '未設定'}")
        print(f"OpenAI Model: {openai_config['model']}")
        
        # システム設定
        system_config = self.get_system_config()
        print(f"ログレベル: {system_config['log_level']}")
        print(f"デバッグモード: {system_config['debug_mode']}")
        print(f"最大画像数: {system_config['max_images']}")
        
        # 必須設定の検証
        missing = self.validate_required_settings()
        if missing:
            print(f"\n⚠️ 不足している設定: {', '.join(missing)}")
        else:
            print("\n✅ 必須設定は全て完了しています")
        
        print("========================\n")
    
    def create_sample_env_file(self, filename: str = ".env.sample"):
        """
        サンプル.envファイルを作成
        
        Args:
            filename: 作成するファイル名
        """
        sample_content = """# WordPress自動記事生成システム設定

# OpenAI API設定
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# WordPress設定
WP_URL=https://your-wordpress-site.com
WP_USER=your_wp_user
WP_APP_PASS=your_app_password
WP_POST_STATUS=publish
WP_CATEGORY_ID=1
WP_AUTHOR_ID=1

# システム設定
LOG_LEVEL=INFO
DEBUG_MODE=false
MAX_IMAGES=6
NUM_SECTIONS=5
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        
        print(f"✅ サンプル設定ファイルを作成しました: {filename}")
        print("   このファイルをコピーして.envファイルを作成し、適切な値を設定してください。")

# グローバルインスタンス
config_manager = ConfigManager()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "summary":
            config_manager.print_config_summary()
        elif sys.argv[1] == "sample":
            config_manager.create_sample_env_file()
        elif sys.argv[1] == "validate":
            missing = config_manager.validate_required_settings()
            if missing:
                print(f"❌ 不足している設定: {', '.join(missing)}")
                sys.exit(1)
            else:
                print("✅ 設定は正常です")
    else:
        config_manager.print_config_summary() 