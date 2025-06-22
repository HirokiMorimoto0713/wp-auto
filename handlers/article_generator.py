"""
記事生成を統括するメインクラス
"""

import os
import csv
import pandas as pd
from typing import Dict, List, Optional
from .chatgpt_handler import ChatGPTHandler
from .dalle_handler import DalleHandler
from .seo_optimizer import SEOOptimizer

class ArticleGenerator:
    """記事生成を統括するメインクラス"""
    
    def __init__(self, api_key: str = None):
        """
        記事生成器の初期化
        
        Args:
            api_key: OpenAI APIキー（省略時は環境変数から取得）
        """
        # ハンドラーの初期化
        self.chatgpt_handler = ChatGPTHandler(api_key)
        self.dalle_handler = DalleHandler(api_key)
        self.seo_optimizer = SEOOptimizer(self.chatgpt_handler)
        
        # 設定
        self.keywords_csv = "keywords.csv"
        self.index_file = "current_index.txt"
    
    def get_next_keyword_group(self) -> Dict:
        """
        新しいCSVファイルから次のキーワードグループを取得
        B列が同じ値の行をグループ化して返す
        """
        # インデックス取得
        idx = 0
        if os.path.exists(self.index_file):
            with open(self.index_file) as f:
                idx = int(f.read().strip() or 0)
        
        # CSVファイル読み込み
        try:
            # 現在のディレクトリまたはDocumentsディレクトリ内のファイルを読み込み
            current_dir = os.getcwd()
            print(f"現在のディレクトリ: {current_dir}")
            
            csv_paths = [
                self.keywords_csv,  # 現在のディレクトリ（直接指定）
                os.path.join(current_dir, self.keywords_csv),  # 現在のディレクトリ（絶対パス）
                os.path.expanduser(f"~/Documents/{self.keywords_csv}"),  # Documentsディレクトリ
                os.path.expanduser(f"~/{self.keywords_csv}")  # ホームディレクトリ
            ]
            
            print(f"検索パス: {csv_paths}")
            
            csv_path = None
            for path in csv_paths:
                print(f"チェック中: {path} -> 存在: {os.path.exists(path)}")
                if os.path.exists(path):
                    csv_path = path
                    break
                    
            if not csv_path:
                raise FileNotFoundError(f"CSVファイルが見つかりません: {csv_paths}")
                
            print(f"CSVファイル読み込み: {csv_path}")
            df = pd.read_csv(csv_path, header=None, names=['keyword', 'group_id', 'main_category', 'sub_category'])
            
            # グループIDでソート
            df = df.sort_values('group_id')
            
            # ユニークなグループIDを取得
            unique_groups = df['group_id'].unique()
            unique_groups = sorted([g for g in unique_groups if pd.notna(g)])
            
            if not unique_groups:
                raise ValueError("有効なグループIDが見つかりません")
            
            # 現在のグループID取得
            current_group_id = unique_groups[idx % len(unique_groups)]
            
            # 該当グループの全行を取得
            group_data = df[df['group_id'] == current_group_id]
            
            # 次のインデックスを保存
            with open(self.index_file, "w") as f:
                f.write(str((idx + 1) % len(unique_groups)))
            
            # グループデータを辞書形式で返す
            keywords = group_data['keyword'].tolist()
            main_category = group_data['main_category'].iloc[0] if pd.notna(group_data['main_category'].iloc[0]) else ""
            sub_category = group_data['sub_category'].iloc[0] if pd.notna(group_data['sub_category'].iloc[0]) else ""
            
            return {
                'group_id': current_group_id,
                'keywords': keywords,
                'main_category': main_category,
                'sub_category': sub_category,
                'primary_keyword': keywords[0] if keywords else ""
            }
            
        except Exception as e:
            print(f"⚠️ 新しいCSVファイル読み込みエラー: {e}")
            # フォールバック: 旧システム使用
            return {
                'group_id': 1,
                'keywords': [self.get_next_keyword_legacy()],
                'main_category': "",
                'sub_category': "",
                'primary_keyword': self.get_next_keyword_legacy()
            }
    
    def get_next_keyword_legacy(self, col: int = 0) -> str:
        """
        旧システム用のキーワード取得（フォールバック用）
        """
        idx = 0
        if os.path.exists(self.index_file):
            with open(self.index_file) as f:
                idx = int(f.read().strip() or 0)
        
        # 旧keywords.csvファイル確認
        if not os.path.exists(self.keywords_csv):
            return "ChatGPT 使い方"  # デフォルトキーワード
        
        with open(self.keywords_csv, encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # 1行スキップ
            keywords = [row[col] for row in reader if len(row) > col]
        
        if not keywords:
            return "ChatGPT 使い方"
        
        keyword = keywords[idx % len(keywords)]
        with open(self.index_file, "w") as f:
            f.write(str((idx + 1) % len(keywords)))
        return keyword
    
    def generate_integrated_article_from_keywords(self, 
                                                keyword_group: Dict, 
                                                style_features: Dict = None, 
                                                num_sections: int = 5) -> Dict:
        """
        複数キーワードを統合したSEO効果的な記事を生成
        
        Args:
            keyword_group: キーワードグループ情報
            style_features: スタイル特徴（オプション）
            num_sections: セクション数
            
        Returns:
            生成された記事データ
        """
        keywords = keyword_group['keywords']
        primary_keyword = keyword_group['primary_keyword']
        
        print(f"🎯 統合記事生成開始:")
        print(f"   メインキーワード: {primary_keyword}")
        print(f"   関連キーワード: {', '.join(keywords[1:]) if len(keywords) > 1 else 'なし'}")
        
        # 統合的なプロンプト作成
        integrated_prompt = self._create_integrated_prompt(keywords, primary_keyword)
        
        # 記事生成
        if style_features and not style_features.get('error'):
            print("🎨 スタイルガイド付きで記事生成")
            article = self._generate_article_with_style(integrated_prompt, keywords, style_features, num_sections)
        else:
            print("📝 標準モードで記事生成")
            article = self._generate_standard_article(integrated_prompt, keywords, num_sections)
        
        # 生成された記事に基づいて最適なタイトルを生成
        optimized_title = self._generate_optimized_title_from_content(
            article['content'], keywords, primary_keyword
        )
        article['title'] = optimized_title
        
        # カテゴリ情報を追加
        article['main_category'] = keyword_group['main_category']
        article['sub_category'] = keyword_group['sub_category']
        article['keywords_used'] = keywords
        article['primary_keyword'] = primary_keyword
        article['integrated_article'] = True
        
        # SEO分析を実行
        seo_analysis = self.seo_optimizer.analyze_seo_score(
            article['title'], article['content'], keywords
        )
        article['seo_analysis'] = seo_analysis
        
        return article
    
    def generate_article_with_images(self, article_data: Dict, max_images: int = 3) -> Dict:
        """
        記事に画像を追加
        
        Args:
            article_data: 記事データ
            max_images: 最大画像数
            
        Returns:
            画像付き記事データ
        """
        try:
            # アイキャッチ画像を生成
            featured_image_url = self.dalle_handler.generate_featured_image(
                article_data['title'], 
                article_data['content']
            )
            article_data['featured_image_url'] = featured_image_url
            
            # 記事内の見出しに画像を追加する処理も可能
            # ここでは簡単にアイキャッチのみ
            
        except Exception as e:
            print(f"画像生成エラー: {e}")
            article_data['featured_image_url'] = None
        
        return article_data
    
    def _create_integrated_prompt(self, keywords: List[str], primary_keyword: str) -> str:
        """
        統合記事用のプロンプトを作成
        """
        keywords_text = "、".join(keywords)
        return f"""
{primary_keyword}を中心とした包括的なガイド記事を作成してください。

## 含めるべきキーワード（SEO最適化）
{chr(10).join([f"- {kw}" for kw in keywords])}

## 記事の方針
- 上記のキーワードを自然に統合した内容
- SEO効果的な構成で検索ニーズに対応
- 初心者から上級者まで幅広いレベルに対応
- 実践的で具体的なガイド
- 各キーワードの検索意図を満たす内容を含む
"""
    
    def _generate_standard_article(self, prompt: str, keywords: List[str], num_sections: int) -> Dict:
        """
        標準モードで記事を生成
        """
        # ChatGPTで記事コンテンツを生成
        article_data = self.chatgpt_handler.generate_article_content(prompt, num_sections)
        
        # SEO要素を追加
        article_data['meta_description'] = self.chatgpt_handler.generate_meta_description(
            article_data['content']
        )
        article_data['seo_tags'] = self.chatgpt_handler.generate_seo_tags(
            article_data['content']
        )
        article_data['slug'] = self.seo_optimizer.generate_seo_slug(
            article_data['title']
        )
        
        return article_data
    
    def _generate_article_with_style(self, prompt: str, keywords: List[str], 
                                   style_features: Dict, num_sections: int) -> Dict:
        """
        スタイルガイド付きで記事を生成
        """
        # スタイル情報を含むプロンプトを作成
        styled_prompt = f"""
{prompt}

## スタイルガイド
{self._format_style_features(style_features)}
"""
        
        return self._generate_standard_article(styled_prompt, keywords, num_sections)
    
    def _format_style_features(self, style_features: Dict) -> str:
        """
        スタイル特徴をプロンプト用にフォーマット
        """
        formatted = []
        
        if style_features.get('tone'):
            formatted.append(f"文体: {style_features['tone']}")
        
        if style_features.get('structure'):
            formatted.append(f"構成: {style_features['structure']}")
        
        if style_features.get('keywords'):
            formatted.append(f"重要キーワード: {', '.join(style_features['keywords'])}")
        
        return "\n".join(formatted)
    
    def _generate_optimized_title_from_content(self, content: str, keywords: List[str], 
                                             primary_keyword: str) -> str:
        """
        完成した記事内容に基づいて最適なタイトルを生成
        """
        keywords_text = "、".join(keywords)
        
        title_prompt = f"""
あなたはSEOと読者心理に長けたブログ編集者です。

以下の記事内容と対象キーワードを基に、最適なタイトルを1つ生成してください。

## 対象キーワード
メイン: {primary_keyword}
関連: {', '.join(keywords[1:]) if len(keywords) > 1 else 'なし'}

## 記事内容の要約
{content[:800]}...

## タイトル生成指針
- 既存のタイトルスタイルを参考に魅力的なタイトル
- メインキーワードを必ず含める
- 関連キーワードも自然に含める（可能な限り）
- SEO効果的でクリックされやすい
- 30-60文字程度

タイトルのみを出力してください。
"""
        
        try:
            messages = [
                {"role": "system", "content": "あなたはSEOとマーケティングの専門家です。"},
                {"role": "user", "content": title_prompt}
            ]
            
            optimized_title = self.chatgpt_handler.generate_completion(messages, max_tokens=100)
            return optimized_title.strip().strip('"').strip("'")
            
        except Exception as e:
            print(f"タイトル最適化エラー: {e}")
            return f"{primary_keyword}の完全ガイド" 