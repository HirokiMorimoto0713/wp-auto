"""
ChatGPTとのやり取りを担当するハンドラー
"""

import os
import openai
from dotenv import load_dotenv
from typing import List, Dict, Optional

# 環境変数読み込み
load_dotenv()

class ChatGPTHandler:
    """ChatGPTとのやり取りを管理するクラス"""
    
    def __init__(self, api_key: str = None):
        """
        ChatGPTハンドラーの初期化
        
        Args:
            api_key: OpenAI APIキー（省略時は環境変数から取得）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI APIキーが設定されていません")
        
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def generate_completion(self, 
                          messages: List[Dict[str, str]], 
                          model: str = "gpt-3.5-turbo",
                          max_tokens: int = 2000,
                          temperature: float = 0.7) -> str:
        """
        ChatGPTからの応答を生成
        
        Args:
            messages: 会話のメッセージリスト
            model: 使用するモデル
            max_tokens: 最大トークン数
            temperature: 温度パラメータ
            
        Returns:
            生成されたテキスト
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"ChatGPT API エラー: {e}")
            raise
    
    def generate_article_content(self, prompt: str, num_sections: int = 5) -> Dict[str, str]:
        """
        記事コンテンツを生成
        
        Args:
            prompt: 記事生成プロンプト
            num_sections: セクション数
            
        Returns:
            記事データ（title, content, meta_description等）
        """
        messages = [
            {"role": "system", "content": "あなたは優秀なライターです。SEOに配慮した高品質な記事を作成してください。"},
            {"role": "user", "content": prompt}
        ]
        
        content = self.generate_completion(messages, max_tokens=3000)
        
        # コンテンツからタイトルを抽出（簡易実装）
        lines = content.split('\n')
        title = lines[0].strip('# ').strip() if lines else "記事タイトル"
        
        return {
            'title': title,
            'content': content,
            'meta_description': self._extract_meta_description(content),
            'sections': num_sections
        }
    
    def generate_title_variants(self, prompt: str, n: int = 5) -> List[str]:
        """
        タイトルのバリエーションを生成
        
        Args:
            prompt: タイトル生成プロンプト
            n: 生成するタイトル数
            
        Returns:
            タイトルのリスト
        """
        title_prompt = f"""
以下のプロンプトに基づいて、{n}つの魅力的なタイトルを生成してください：

{prompt}

各タイトルは以下の形式で出力してください：
1. タイトル1
2. タイトル2
...
"""
        
        messages = [
            {"role": "system", "content": "あなたはSEOとマーケティングに精通したコピーライターです。"},
            {"role": "user", "content": title_prompt}
        ]
        
        response = self.generate_completion(messages)
        
        # タイトルを抽出
        titles = []
        for line in response.split('\n'):
            if line.strip() and (line.strip().startswith(('1.', '2.', '3.', '4.', '5.')) or 
                               line.strip().startswith('- ')):
                title = line.split('.', 1)[-1].strip() if '.' in line else line.strip('- ').strip()
                if title:
                    titles.append(title)
        
        return titles[:n]
    
    def generate_meta_description(self, content: str, max_length: int = 160) -> str:
        """
        メタディスクリプションを生成
        
        Args:
            content: 記事コンテンツ
            max_length: 最大文字数
            
        Returns:
            メタディスクリプション
        """
        prompt = f"""
以下の記事内容から、{max_length}文字以内でSEO効果的なメタディスクリプションを生成してください：

{content[:1000]}

要件：
- 検索結果でクリックされやすい内容
- 記事の要点を簡潔に表現
- {max_length}文字以内
"""
        
        messages = [
            {"role": "system", "content": "あなたはSEOの専門家です。"},
            {"role": "user", "content": prompt}
        ]
        
        return self.generate_completion(messages, max_tokens=200)
    
    def generate_seo_tags(self, content: str, max_tags: int = 10) -> List[str]:
        """
        SEOタグを生成
        
        Args:
            content: 記事コンテンツ
            max_tags: 最大タグ数
            
        Returns:
            タグのリスト
        """
        prompt = f"""
以下の記事内容から、SEO効果的なタグを{max_tags}個生成してください：

{content[:1000]}

要件：
- 記事の内容に関連するキーワード
- 検索されやすいタグ
- カンマ区切りで出力
"""
        
        messages = [
            {"role": "system", "content": "あなたはSEOの専門家です。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.generate_completion(messages, max_tokens=200)
        
        # タグを抽出
        tags = [tag.strip() for tag in response.split(',')]
        return tags[:max_tags]
    
    def _extract_meta_description(self, content: str) -> str:
        """
        コンテンツから簡易的なメタディスクリプションを抽出
        
        Args:
            content: 記事コンテンツ
            
        Returns:
            メタディスクリプション
        """
        # 最初の段落を取得
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#'):
                return line.strip()[:160]
        
        return "記事の詳細な説明です。" 