#!/usr/bin/env python3
"""
改善されたWordPress自動記事投稿システム
- クラス化されたコード構造
- 統一された設定管理
- 改善されたログ管理
- Cron多重起動防止
"""

import os
import sys
import time
import requests
from io import BytesIO
from bs4 import BeautifulSoup

# 新しいモジュールをインポート
from handlers import ArticleGenerator
from utils import CronManager, LogManager, ConfigManager

# 後方互換性のため、既存の関数もインポート
from post_article import (
    upload_image_to_wp,
    insert_images_to_html,
    get_or_create_categories,
    get_or_create_tags,
    post_to_wp
)

class ImprovedArticlePublisher:
    """改善された記事投稿システム"""
    
    def __init__(self):
        """初期化"""
        # 設定管理の初期化
        self.config = ConfigManager()
        
        # ログ管理の初期化
        self.logger = LogManager(
            service_name="wp-auto-improved",
            enable_cloud_logging=True,
            enable_file_logging=True
        )
        
        # 記事生成器の初期化
        openai_config = self.config.get_openai_config()
        self.article_generator = ArticleGenerator(openai_config['api_key'])
        
        # WordPress設定
        self.wp_config = self.config.get_wordpress_config()
        
        # システム設定
        self.system_config = self.config.get_system_config()
        
        # 設定検証
        self._validate_configuration()
    
    def _validate_configuration(self):
        """設定の検証"""
        missing = self.config.validate_required_settings()
        if missing:
            self.logger.error(f"必須設定が不足しています: {', '.join(missing)}")
            raise ValueError(f"必須設定が不足しています: {', '.join(missing)}")
        
        self.logger.info("設定検証完了", 
                        wp_url=self.wp_config['wp_url'],
                        openai_model=self.config.get_openai_config()['model'])
    
    def generate_article(self) -> dict:
        """記事を生成"""
        try:
            # キーワードグループを取得
            keyword_group = self.article_generator.get_next_keyword_group()
            
            self.logger.log_process_start("記事生成", 
                                        keyword_group=keyword_group['primary_keyword'])
            
            # 記事を生成
            article_data = self.article_generator.generate_integrated_article_from_keywords(
                keyword_group=keyword_group,
                num_sections=self.system_config['num_sections']
            )
            
            # SEO分析ログ
            if 'seo_analysis' in article_data:
                seo = article_data['seo_analysis']
                self.logger.log_seo_analysis(
                    article_data['title'],
                    seo['score'],
                    seo['grade']
                )
            
            self.logger.log_article_generation(
                keyword_group['primary_keyword'],
                article_data['title'],
                success=True
            )
            
            return article_data
            
        except Exception as e:
            self.logger.log_article_generation(
                keyword_group.get('primary_keyword', 'unknown'),
                '',
                success=False,
                error=str(e)
            )
            raise
    
    def add_images_to_article(self, article_data: dict) -> tuple:
        """記事に画像を追加"""
        try:
            html_content = article_data['content']
            max_images = self.system_config['max_images']
            
            self.logger.info(f"画像追加開始 (最大{max_images}枚)")
            
            # 画像を挿入
            updated_html, media_ids = insert_images_to_html(html_content, max_images)
            
            self.logger.info(f"画像追加完了 ({len(media_ids)}枚追加)")
            
            return updated_html, media_ids
            
        except Exception as e:
            self.logger.error("画像追加エラー", error=e)
            # 画像なしで続行
            return article_data['content'], []
    
    def publish_to_wordpress(self, article_data: dict, content_with_images: str, media_ids: list) -> dict:
        """WordPressに投稿"""
        try:
            # カテゴリを取得または作成
            category_ids = get_or_create_categories(
                article_data.get('main_category', ''),
                article_data.get('sub_category', '')
            )
            
            # タグを取得または作成
            tag_names = article_data.get('seo_tags', [])
            tag_ids = get_or_create_tags(tag_names) if tag_names else []
            
            # メタディスクリプション
            meta_description = article_data.get('meta_description', '')
            
            # スラッグ
            slug = article_data.get('slug', '')
            
            # アイキャッチ画像ID
            featured_id = media_ids[0] if media_ids else None
            
            # WordPressに投稿
            result = post_to_wp(
                title=article_data['title'],
                content=content_with_images,
                meta_description=meta_description,
                slug=slug,
                tag_ids=tag_ids,
                category_ids=category_ids,
                featured_id=featured_id
            )
            
            if result.get('success'):
                self.logger.log_wordpress_post(
                    article_data['title'],
                    result.get('post_id'),
                    success=True,
                    post_url=result.get('post_url'),
                    categories=len(category_ids),
                    tags=len(tag_ids),
                    images=len(media_ids)
                )
            else:
                self.logger.log_wordpress_post(
                    article_data['title'],
                    success=False,
                    error=result.get('error')
                )
            
            return result
            
        except Exception as e:
            self.logger.log_wordpress_post(
                article_data['title'],
                success=False,
                error=str(e)
            )
            raise
    
    def run_single_article_generation(self) -> dict:
        """単一記事の生成・投稿を実行"""
        start_time = time.time()
        
        try:
            self.logger.log_process_start("記事生成・投稿プロセス")
            
            # 1. 記事生成
            article_data = self.generate_article()
            
            # 2. 画像追加
            content_with_images, media_ids = self.add_images_to_article(article_data)
            
            # 3. WordPress投稿
            result = self.publish_to_wordpress(article_data, content_with_images, media_ids)
            
            # 実行時間計算
            execution_time = time.time() - start_time
            
            self.logger.log_process_end(
                "記事生成・投稿プロセス",
                execution_time=execution_time,
                success=result.get('success', False),
                post_id=result.get('post_id')
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.log_process_end(
                "記事生成・投稿プロセス",
                execution_time=execution_time,
                success=False,
                error=str(e)
            )
            raise

def main():
    """メイン処理"""
    try:
        # 記事投稿システムを初期化
        publisher = ImprovedArticlePublisher()
        
        # 記事生成・投稿を実行
        result = publisher.run_single_article_generation()
        
        if result.get('success'):
            print(f"✅ 記事投稿成功: {result.get('post_url', 'URL不明')}")
            return 0
        else:
            print(f"❌ 記事投稿失敗: {result.get('error', '原因不明')}")
            return 1
            
    except Exception as e:
        print(f"❌ システムエラー: {e}")
        return 1

def main_with_cron_protection():
    """Cron多重起動防止付きメイン処理"""
    cron_manager = CronManager()
    
    def protected_main():
        return main()
    
    try:
        result = cron_manager.run_with_lock(protected_main)
        return result if result is not None else 0
    except Exception as e:
        print(f"❌ Cron実行エラー: {e}")
        return 1

if __name__ == "__main__":
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        if sys.argv[1] == "config":
            # 設定概要を表示
            config = ConfigManager()
            config.print_config_summary()
            sys.exit(0)
        elif sys.argv[1] == "cron-guide":
            # Cron設定ガイドを表示
            CronManager.print_cron_setup_guide("post_article_improved.py")
            sys.exit(0)
        elif sys.argv[1] == "log-guide":
            # ログ設定ガイドを表示
            LogManager.setup_cloud_logging_guide()
            sys.exit(0)
        elif sys.argv[1] == "test":
            # テスト実行（Cron保護なし）
            sys.exit(main())
    
    # 通常実行（Cron多重起動防止付き）
    sys.exit(main_with_cron_protection()) 