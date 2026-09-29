"""
DALL-E 3での画像生成を担当するハンドラー
"""

import os
import openai
from dotenv import load_dotenv
from typing import Optional

# 環境変数読み込み
load_dotenv()

class DalleHandler:
    """DALL-E 3での画像生成を管理するクラス"""
    
    def __init__(self, api_key: str = None):
        """
        DALL-Eハンドラーの初期化
        
        Args:
            api_key: OpenAI APIキー（省略時は環境変数から取得）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI APIキーが設定されていません")
        
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def generate_image_prompt(self, article_content: str) -> str:
        """
        記事内容から画像生成プロンプトを作成
        
        Args:
            article_content: 記事コンテンツ
            
        Returns:
            画像生成用プロンプト
        """
        # 記事内容を要約して画像プロンプトを生成
        prompt = f"""
以下の記事内容に最適な画像の説明を英語で作成してください。
DALL-E 3で生成するための具体的で詳細な画像プロンプトを作成してください。

記事内容: {article_content[:500]}

要件:
- 記事の内容を視覚的に表現
- 具体的で詳細な描写
- 英語で出力
- 1-2文程度
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at creating image prompts for DALL-E 3."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"画像プロンプト生成エラー: {e}")
            return "A modern, clean illustration representing technology and innovation"
    
    def generate_image_url(self, image_prompt: str, size: str = "1024x1024") -> str:
        """
        DALL-E 3で画像を生成
        
        Args:
            image_prompt: 画像生成プロンプト
            size: 画像サイズ
            
        Returns:
            生成された画像のURL
        """
        try:
            print(f"🎨 画像生成中: {image_prompt[:50]}...")
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size=size,
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            print(f"✅ 画像生成成功: {image_url}")
            return image_url
            
        except Exception as e:
            print(f"❌ 画像生成エラー: {e}")
            raise
    
    def generate_heading_image(self, heading_text: str) -> str:
        """
        見出しテキストから画像を生成
        
        Args:
            heading_text: 見出しテキスト
            
        Returns:
            生成された画像のURL
        """
        # 見出しから画像プロンプトを生成
        image_prompt = self.generate_image_prompt(f"Section about: {heading_text}")
        
        # 画像を生成
        return self.generate_image_url(image_prompt)
    
    def generate_featured_image(self, title: str, content: str) -> str:
        """
        記事のアイキャッチ画像を生成
        
        Args:
            title: 記事タイトル
            content: 記事コンテンツ
            
        Returns:
            生成された画像のURL
        """
        # タイトルとコンテンツから画像プロンプトを生成
        combined_content = f"Title: {title}\n\nContent: {content[:300]}"
        image_prompt = self.generate_image_prompt(combined_content)
        
        # 画像を生成
        return self.generate_image_url(image_prompt) 