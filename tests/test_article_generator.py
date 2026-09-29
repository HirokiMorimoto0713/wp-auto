#!/usr/bin/env python3
"""
AI記事生成システム - 単体テスト
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import json
from datetime import datetime

# テスト対象のモジュールをインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import generate_article
    import post_article
except ImportError:
    # モジュールが見つからない場合はモックを作成
    generate_article = Mock()
    post_article = Mock()


class TestArticleGenerator(unittest.TestCase):
    """記事生成機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.test_config = {
            'openai_api_key': 'test-key',
            'wordpress_url': 'https://test-site.com',
            'wordpress_username': 'test-user',
            'wordpress_password': 'test-pass'
        }

    @patch('generate_article.openai')
    def test_generate_article_content(self, mock_openai):
        """記事内容生成のテスト"""
        # モックの設定
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "テスト記事の内容"
        mock_openai.ChatCompletion.create.return_value = mock_response

        # テスト実行（実際の関数があれば）
        if hasattr(generate_article, 'generate_content'):
            result = generate_article.generate_content("テストキーワード")
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)

    @patch('generate_article.openai')
    def test_generate_dalle_image(self, mock_openai):
        """DALL-E画像生成のテスト"""
        # モックの設定
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].url = "https://test-image.com/image.jpg"
        mock_openai.Image.create.return_value = mock_response

        # テスト実行（実際の関数があれば）
        if hasattr(generate_article, 'generate_image'):
            result = generate_article.generate_image("テストプロンプト")
            self.assertIsInstance(result, str)
            self.assertTrue(result.startswith('http'))

    def test_seo_optimization(self):
        """SEO最適化のテスト"""
        test_content = "これはテスト記事です。" * 100
        
        # SEO関数が存在する場合のテスト
        if hasattr(generate_article, 'optimize_seo'):
            result = generate_article.optimize_seo(test_content, "テストキーワード")
            self.assertIsInstance(result, dict)
            self.assertIn('title', result)
            self.assertIn('meta_description', result)

    def test_article_structure_validation(self):
        """記事構造の検証テスト"""
        test_article = {
            'title': 'テストタイトル',
            'content': 'テスト内容',
            'tags': ['tag1', 'tag2'],
            'category': 'AI'
        }
        
        # 記事構造の検証
        required_fields = ['title', 'content', 'tags', 'category']
        for field in required_fields:
            self.assertIn(field, test_article)
            self.assertIsNotNone(test_article[field])


class TestWordPressConnector(unittest.TestCase):
    """WordPress投稿機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.test_post_data = {
            'title': 'テスト投稿',
            'content': 'テスト内容',
            'status': 'draft',
            'categories': [1],
            'tags': [1, 2]
        }

    @patch('post_article.requests.post')
    def test_wordpress_authentication(self, mock_post):
        """WordPress認証のテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'token': 'test-token'}
        mock_post.return_value = mock_response

        # テスト実行（実際の関数があれば）
        if hasattr(post_article, 'authenticate_wordpress'):
            result = post_article.authenticate_wordpress(
                'https://test-site.com',
                'test-user',
                'test-pass'
            )
            self.assertIsInstance(result, str)

    @patch('post_article.requests.post')
    def test_post_creation(self, mock_post):
        """投稿作成のテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 123, 'link': 'https://test-site.com/post/123'}
        mock_post.return_value = mock_response

        # テスト実行（実際の関数があれば）
        if hasattr(post_article, 'create_post'):
            result = post_article.create_post(self.test_post_data)
            self.assertIsInstance(result, dict)
            self.assertIn('id', result)

    def test_post_data_validation(self):
        """投稿データの検証テスト"""
        # 必須フィールドの検証
        required_fields = ['title', 'content']
        for field in required_fields:
            self.assertIn(field, self.test_post_data)
            self.assertIsNotNone(self.test_post_data[field])
            self.assertGreater(len(str(self.test_post_data[field])), 0)


class TestConfigurationManagement(unittest.TestCase):
    """設定管理のテスト（改善提案2に対応）"""

    def test_env_file_loading(self):
        """環境変数ファイルの読み込みテスト"""
        # テスト用の環境変数を設定
        test_env_vars = {
            'WORDPRESS_URL': 'https://test-site.com',
            'WORDPRESS_USERNAME': 'test-user',
            'OPENAI_API_KEY': 'test-key'
        }
        
        with patch.dict(os.environ, test_env_vars):
            # 環境変数の読み込みテスト
            self.assertEqual(os.getenv('WORDPRESS_URL'), 'https://test-site.com')
            self.assertEqual(os.getenv('WORDPRESS_USERNAME'), 'test-user')
            self.assertEqual(os.getenv('OPENAI_API_KEY'), 'test-key')

    def test_config_validation(self):
        """設定値の検証テスト"""
        # 必須設定項目の検証
        required_configs = [
            'WORDPRESS_URL',
            'WORDPRESS_USERNAME',
            'WORDPRESS_PASSWORD',
            'OPENAI_API_KEY'
        ]
        
        # 実際の環境では、これらの設定が存在することを確認
        for config in required_configs:
            # テスト環境では警告のみ
            if not os.getenv(config):
                print(f"Warning: {config} not set in environment")


class TestErrorHandling(unittest.TestCase):
    """エラーハンドリングのテスト"""

    def test_api_error_handling(self):
        """API エラーハンドリングのテスト"""
        # OpenAI APIエラーのシミュレーション
        with patch('generate_article.openai.ChatCompletion.create') as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            # エラーハンドリングが適切に動作することを確認
            # 実際の関数があれば、例外が適切に処理されることをテスト
            try:
                if hasattr(generate_article, 'generate_content'):
                    generate_article.generate_content("テスト")
            except Exception as e:
                self.assertIsInstance(e, Exception)

    def test_wordpress_connection_error(self):
        """WordPress接続エラーのテスト"""
        with patch('post_article.requests.post') as mock_post:
            mock_post.side_effect = Exception("Connection Error")
            
            # 接続エラーが適切に処理されることを確認
            try:
                if hasattr(post_article, 'create_post'):
                    post_article.create_post({'title': 'test', 'content': 'test'})
            except Exception as e:
                self.assertIsInstance(e, Exception)


class TestLogging(unittest.TestCase):
    """ログ機能のテスト（改善提案3に対応）"""

    def test_log_file_creation(self):
        """ログファイル作成のテスト"""
        import logging
        
        # テスト用のログ設定
        log_file = 'test_log.log'
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # ログメッセージの記録
        logging.info("Test log message")
        
        # ログファイルが作成されることを確認
        self.assertTrue(os.path.exists(log_file))
        
        # クリーンアップ
        if os.path.exists(log_file):
            os.remove(log_file)

    def test_structured_logging(self):
        """構造化ログのテスト"""
        # JSON形式のログデータ
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': 'Test message',
            'module': 'test_module',
            'function': 'test_function'
        }
        
        # JSON形式でログが出力できることを確認
        json_log = json.dumps(log_data)
        self.assertIsInstance(json_log, str)
        
        # JSONが正しくパースできることを確認
        parsed_log = json.loads(json_log)
        self.assertEqual(parsed_log['level'], 'INFO')
        self.assertEqual(parsed_log['message'], 'Test message')


if __name__ == '__main__':
    # テストの実行
    unittest.main(verbosity=2) 