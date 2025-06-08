#!/usr/bin/env python3
"""
参考記事機能のテストスクリプト
"""

import os
from dotenv import load_dotenv
from generate_article import (
    extract_article_structure, 
    generate_article_from_reference,
    extract_multiple_article_structures,
    generate_article_from_multiple_references,
    extract_style_features_from_sources,
    generate_article_with_style_guide
)

def test_markdown_extraction():
    """マークダウンファイルからの構造抽出テスト"""
    print("=== マークダウン構造抽出テスト ===")
    
    if not os.path.exists("reference/sample.md"):
        print("❌ reference/sample.md が見つかりません")
        return
        
    with open("reference/sample.md", "r", encoding="utf-8") as f:
        markdown_content = f.read()
    
    structure = extract_article_structure(markdown_content, "markdown")
    
    if "error" in structure:
        print(f"❌ エラー: {structure['error']}")
        return
        
    print(f"✅ タイトル: {structure['title']}")
    print(f"✅ セクション数: {structure['total_sections']}")
    
    for i, section in enumerate(structure['sections'], 1):
        print(f"  {i}. {section['heading']}")
        if section.get('content'):
            print(f"     内容: {section['content'][:50]}...")

def test_url_extraction():
    """URLからの構造抽出テスト"""
    print("\n=== URL構造抽出テスト ===")
    
    # テスト用URL（公開されている記事）
    test_url = "https://note.com/chatgpt_lab/n/nf6d6cb2d6f8e"
    
    print(f"テストURL: {test_url}")
    structure = extract_article_structure(test_url, "url")
    
    if "error" in structure:
        print(f"❌ エラー: {structure['error']}")
        return
        
    print(f"✅ タイトル: {structure['title']}")
    print(f"✅ セクション数: {structure['total_sections']}")
    
    for i, section in enumerate(structure['sections'], 1):
        print(f"  {i}. {section['heading']}")

def test_multiple_sources_extraction():
    """複数ソースからの構造抽出・統合テスト"""
    print("\n=== 複数ソース統合テスト ===")
    
    # 複数のソースを準備
    sources = []
    
    # ローカルファイル
    if os.path.exists("reference/sample.md"):
        sources.append("reference/sample.md")
    if os.path.exists("reference/sample2.md"):
        sources.append("reference/sample2.md")
    
    # URL（テスト用）
    # sources.append("https://note.com/chatgpt_lab/n/nf6d6cb2d6f8e")
    
    if len(sources) < 2:
        print("❌ 複数ソーステストには最低2つのファイルが必要です")
        return
    
    print(f"📚 {len(sources)}つのソースを統合テスト:")
    for i, source in enumerate(sources, 1):
        print(f"  {i}. {source}")
    
    # 複数ソース統合
    integrated_structure = extract_multiple_article_structures(sources)
    
    if "error" in integrated_structure:
        print(f"❌ 統合エラー: {integrated_structure['error']}")
        return
    
    print(f"✅ 統合完了!")
    print(f"📊 統合後タイトル: {integrated_structure.get('title', 'N/A')}")
    print(f"📊 統合セクション数: {integrated_structure['total_sections']}")
    print(f"📊 使用ソース数: {integrated_structure['source_count']}")
    
    print("\n--- 統合されたセクション ---")
    for i, section in enumerate(integrated_structure['sections'], 1):
        print(f"  {i}. {section['heading']}")
        if section.get('sources'):
            print(f"     ソース数: {len(section['sources'])}")

def test_article_generation():
    """参考記事を基にした記事生成テスト"""
    print("\n=== 単一参考記事生成テスト ===")
    
    # 環境変数を読み込み
    load_dotenv()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEYが設定されていません")
        return
    
    # マークダウンから構造抽出
    with open("reference/sample.md", "r", encoding="utf-8") as f:
        markdown_content = f.read()
    
    structure = extract_article_structure(markdown_content, "markdown")
    
    if "error" in structure:
        print(f"❌ 構造抽出エラー: {structure['error']}")
        return
    
    # 記事生成テスト
    theme = "ChatGPTを使った業務効率化"
    print(f"テーマ: {theme}")
    
    try:
        result = generate_article_from_reference(theme, structure)
        
        if "error" in result:
            print(f"❌ 記事生成エラー: {result['error']}")
            return
            
        print(f"✅ 生成タイトル: {result['title']}")
        print(f"✅ 記事長: {len(result['content'])}文字")
        print(f"✅ 参考記事使用: {result.get('reference_used', False)}")
        
        # 生成された記事の冒頭を表示
        print("\n--- 生成記事冒頭 ---")
        print(result['content'][:300] + "...")
        
    except Exception as e:
        print(f"❌ 記事生成例外: {e}")
        import traceback
        traceback.print_exc()

def test_multiple_article_generation():
    """複数参考記事を基にした記事生成テスト"""
    print("\n=== 複数参考記事統合生成テスト ===")
    
    # 環境変数を読み込み
    load_dotenv()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEYが設定されていません")
        return
    
    # 複数ソースを準備
    sources = []
    if os.path.exists("reference/sample.md"):
        sources.append("reference/sample.md")
    if os.path.exists("reference/sample2.md"):
        sources.append("reference/sample2.md")
    
    if len(sources) < 2:
        print("❌ 複数ソーステストには最低2つのファイルが必要です")
        return
    
    print(f"📚 {len(sources)}つのソースから統合記事生成:")
    for source in sources:
        print(f"  - {source}")
    
    # 複数ソース統合
    integrated_structure = extract_multiple_article_structures(sources)
    
    if "error" in integrated_structure:
        print(f"❌ 統合エラー: {integrated_structure['error']}")
        return
    
    # 記事生成テスト
    theme = "AI活用の完全ガイド"
    print(f"テーマ: {theme}")
    
    try:
        result = generate_article_from_multiple_references(theme, integrated_structure)
        
        if "error" in result:
            print(f"❌ 記事生成エラー: {result['error']}")
            return
            
        print(f"✅ 生成タイトル: {result['title']}")
        print(f"✅ 記事長: {len(result['content'])}文字")
        print(f"✅ 複数参考記事使用: {result.get('multiple_references', False)}")
        print(f"✅ ソース数: {result.get('source_count', 0)}")
        
        # 生成された記事の冒頭を表示
        print("\n--- 複数統合記事冒頭 ---")
        print(result['content'][:400] + "...")
        
    except Exception as e:
        print(f"❌ 記事生成例外: {e}")
        import traceback
        traceback.print_exc()

def test_style_extraction():
    """スタイル特徴抽出テスト"""
    print("\n=== スタイル特徴抽出テスト ===")
    
    # 複数ソースを準備
    sources = []
    if os.path.exists("reference/sample.md"):
        sources.append("reference/sample.md")
    if os.path.exists("reference/sample2.md"):
        sources.append("reference/sample2.md")
    
    if len(sources) < 2:
        print("❌ スタイルテストには最低2つのファイルが必要です")
        return
    
    print(f"🎨 {len(sources)}つのソースからスタイル抽出:")
    for source in sources:
        print(f"  - {source}")
    
    # スタイル特徴抽出
    style_features = extract_style_features_from_sources(sources)
    
    if "error" in style_features:
        print(f"❌ スタイル抽出エラー: {style_features['error']}")
        return
    
    print(f"✅ スタイル特徴統合完了!")
    print(f"📊 見出し頻度: {style_features.get('h2_per_1000_words', 0):.1f}/1000語")
    print(f"📊 絵文字率: {style_features.get('emoji_in_headings_ratio', 0)*100:.0f}%")
    print(f"📊 箇条書き密度: {style_features.get('bullet_density', 0)*100:.1f}%")
    print(f"📊 文体: {style_features.get('tone', 'unknown')}")
    print(f"📊 見出しスタイル: {style_features.get('heading_style', 'unknown')}")
    print(f"📊 構造スタイル: {style_features.get('structure_style', 'unknown')}")

def test_style_guided_generation():
    """スタイルガイド付き記事生成テスト"""
    print("\n=== スタイルガイド付き記事生成テスト ===")
    
    # 環境変数を読み込み
    load_dotenv()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEYが設定されていません")
        return
    
    # 複数ソースを準備
    sources = []
    if os.path.exists("reference/sample.md"):
        sources.append("reference/sample.md")
    if os.path.exists("reference/sample2.md"):
        sources.append("reference/sample2.md")
    
    if len(sources) < 2:
        print("❌ スタイルガイドテストには最低2つのファイルが必要です")
        return
    
    print(f"🎨 {len(sources)}つのソースからスタイルガイド付き記事生成:")
    for source in sources:
        print(f"  - {source}")
    
    # 構造統合
    integrated_structure = extract_multiple_article_structures(sources)
    if "error" in integrated_structure:
        print(f"❌ 構造統合エラー: {integrated_structure['error']}")
        return
    
    # スタイル特徴抽出
    style_features = extract_style_features_from_sources(sources)
    if "error" in style_features:
        print(f"❌ スタイル抽出エラー: {style_features['error']}")
        return
    
    # 記事生成テスト
    theme = "AIツール完全活用ガイド"
    print(f"テーマ: {theme}")
    
    try:
        result = generate_article_with_style_guide(theme, integrated_structure, style_features)
        
        if "error" in result:
            print(f"❌ 記事生成エラー: {result['error']}")
            return
            
        print(f"✅ 生成タイトル: {result['title']}")
        print(f"✅ 記事長: {len(result['content'])}文字")
        print(f"✅ スタイルガイド使用: {result.get('style_guided', False)}")
        print(f"✅ ソース数: {result.get('source_count', 0)}")
        
        # 生成されたスタイルYAMLを表示
        print("\n--- 生成されたスタイルガイド ---")
        print(result.get('style_yaml', ''))
        
        # 生成された記事の冒頭を表示
        print("\n--- スタイルガイド統合記事冒頭 ---")
        print(result['content'][:500] + "...")
        
    except Exception as e:
        print(f"❌ 記事生成例外: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 参考記事機能テスト開始")
    
    # 各テストを実行
    test_markdown_extraction()
    test_url_extraction()
    test_multiple_sources_extraction()
    test_article_generation()
    test_multiple_article_generation()
    test_style_extraction()
    test_style_guided_generation()
    
    print("\n✅ 全テスト完了") 