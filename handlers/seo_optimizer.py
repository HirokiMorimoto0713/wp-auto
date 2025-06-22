"""
SEO関連の処理を担当するオプティマイザー
"""

import re
import os
from typing import List, Dict, Optional
from .chatgpt_handler import ChatGPTHandler

class SEOOptimizer:
    """SEO最適化を管理するクラス"""
    
    def __init__(self, chatgpt_handler: ChatGPTHandler):
        """
        SEOオプティマイザーの初期化
        
        Args:
            chatgpt_handler: ChatGPTハンドラーのインスタンス
        """
        self.chatgpt_handler = chatgpt_handler
    
    def generate_seo_slug(self, title: str) -> str:
        """
        SEO効果的なスラッグを生成
        
        Args:
            title: 記事タイトル
            
        Returns:
            SEOスラッグ
        """
        # 基本的なスラッグ生成
        slug = title.lower()
        
        # 日本語文字を除去し、英数字とハイフンのみに
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        
        # 長すぎる場合は短縮
        if len(slug) > 50:
            slug = slug[:50].rstrip('-')
        
        # ChatGPTでより良いスラッグを生成
        try:
            prompt = f"""
以下のタイトルから、SEO効果的な英語のスラッグを生成してください：

タイトル: {title}

要件:
- 英語のみ使用
- 小文字とハイフンのみ
- 50文字以内
- 検索エンジンに最適化
- 内容を適切に表現

スラッグのみを出力してください。
"""
            
            messages = [
                {"role": "system", "content": "あなたはSEOの専門家です。"},
                {"role": "user", "content": prompt}
            ]
            
            ai_slug = self.chatgpt_handler.generate_completion(messages, max_tokens=100)
            
            # AI生成スラッグの検証
            if ai_slug and re.match(r'^[a-z0-9-]+$', ai_slug.strip()) and len(ai_slug.strip()) <= 50:
                return ai_slug.strip()
            
        except Exception as e:
            print(f"AI スラッグ生成エラー: {e}")
        
        # フォールバック: 基本スラッグを返す
        return slug or "article"
    
    def optimize_content_for_seo(self, content: str, keywords: List[str]) -> str:
        """
        コンテンツをSEO最適化
        
        Args:
            content: 元のコンテンツ
            keywords: 対象キーワードリスト
            
        Returns:
            SEO最適化されたコンテンツ
        """
        # キーワード密度の確認と調整
        optimized_content = content
        
        for keyword in keywords:
            # キーワードの出現回数をカウント
            keyword_count = content.lower().count(keyword.lower())
            content_length = len(content.split())
            
            # キーワード密度が低い場合は追加を提案
            if content_length > 0:
                density = (keyword_count / content_length) * 100
                if density < 1.0:  # 1%未満の場合
                    print(f"キーワード '{keyword}' の密度が低いです ({density:.2f}%)")
        
        return optimized_content
    
    def generate_structured_data(self, article_data: Dict) -> Dict:
        """
        構造化データ（JSON-LD）を生成
        
        Args:
            article_data: 記事データ
            
        Returns:
            構造化データ
        """
        structured_data = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": article_data.get('title', ''),
            "description": article_data.get('meta_description', ''),
            "author": {
                "@type": "Person",
                "name": "AI記事生成システム"
            },
            "publisher": {
                "@type": "Organization",
                "name": "AI記事サイト"
            },
            "datePublished": article_data.get('date_published', ''),
            "dateModified": article_data.get('date_modified', ''),
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": article_data.get('url', '')
            }
        }
        
        # 画像情報があれば追加
        if article_data.get('featured_image'):
            structured_data["image"] = {
                "@type": "ImageObject",
                "url": article_data['featured_image']
            }
        
        return structured_data
    
    def analyze_seo_score(self, title: str, content: str, keywords: List[str]) -> Dict:
        """
        SEOスコアを分析
        
        Args:
            title: 記事タイトル
            content: 記事コンテンツ
            keywords: 対象キーワード
            
        Returns:
            SEO分析結果
        """
        score = 0
        max_score = 100
        feedback = []
        
        # タイトルの長さチェック
        if 30 <= len(title) <= 60:
            score += 15
            feedback.append("✅ タイトルの長さが適切です")
        else:
            feedback.append("⚠️ タイトルの長さを30-60文字に調整してください")
        
        # メインキーワードがタイトルに含まれているかチェック
        if keywords and keywords[0].lower() in title.lower():
            score += 20
            feedback.append("✅ メインキーワードがタイトルに含まれています")
        else:
            feedback.append("⚠️ メインキーワードをタイトルに含めてください")
        
        # コンテンツの長さチェック
        word_count = len(content.split())
        if word_count >= 300:
            score += 15
            feedback.append(f"✅ コンテンツの長さが適切です ({word_count}語)")
        else:
            feedback.append(f"⚠️ コンテンツをもう少し詳しく書いてください ({word_count}語)")
        
        # 見出しの使用チェック
        h2_count = content.count('<h2>')
        h3_count = content.count('<h3>')
        if h2_count >= 2:
            score += 10
            feedback.append("✅ 見出し構造が適切です")
        else:
            feedback.append("⚠️ H2見出しを2つ以上使用してください")
        
        # キーワード密度チェック
        for keyword in keywords[:3]:  # 上位3キーワードのみチェック
            keyword_count = content.lower().count(keyword.lower())
            if word_count > 0:
                density = (keyword_count / word_count) * 100
                if 1.0 <= density <= 3.0:
                    score += 10
                    feedback.append(f"✅ キーワード '{keyword}' の密度が適切です ({density:.2f}%)")
                else:
                    feedback.append(f"⚠️ キーワード '{keyword}' の密度を調整してください ({density:.2f}%)")
        
        return {
            'score': min(score, max_score),
            'max_score': max_score,
            'feedback': feedback,
            'grade': self._get_seo_grade(score)
        }
    
    def _get_seo_grade(self, score: int) -> str:
        """
        SEOスコアからグレードを取得
        
        Args:
            score: SEOスコア
            
        Returns:
            SEOグレード
        """
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C"
        else:
            return "D" 