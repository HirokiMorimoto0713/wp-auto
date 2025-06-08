import os
import openai
import json
import re
import csv
import requests
import yaml
import statistics as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# .env から APIキーを読み込む
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

KEYWORDS_CSV = "keywords.csv"
INDEX_FILE = "last_index.txt"

def get_next_keyword(col: int = 0) -> str:
    idx = 0
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE) as f:
            idx = int(f.read().strip() or 0)
    with open(KEYWORDS_CSV, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # 1行スキップ
        keywords = [row[col] for row in reader if len(row) > col]
    keyword = keywords[idx % len(keywords)]
    with open(INDEX_FILE, "w") as f:
        f.write(str((idx + 1) % len(keywords)))
    return keyword

def generate_title_variants(prompt: str, n: int = 5) -> list[str]:
    """
    テーマ(prompt)に合う"イケてる"日本語タイトルをn個生成
    """
    style_examples = [
        "もう迷わない。初心者でもできる〇〇の始め方",
        "これを知らずに〇〇始めるのは損してる",
        "正直しんどい。でも〇〇で人生変わった話",
        "2年間の失敗を経て、やっと見つけた〇〇",
        "厳選7選｜2024年最新のおすすめ〇〇を紹介"
    ]

    examples_text = "\n".join([f"- {ex}" for ex in style_examples])

    system_prompt = (
        "あなたはSEOと読者心理に長けたブログ編集者です。\n"
        "以下のタイトル例の文体・構成・語感・テンションを参考に、\n"
        "与えられたテーマに対する魅力的な日本語タイトルを複数生成してください。タイトル例をそのまま使うことは許しません。\n"
        "タイトル例:\n" + examples_text + "\n"
        "出力はJSON形式で → {\"titles\": [\"…\", \"…\", …]}"
    )

    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.95,
        max_tokens=500,
        response_format={"type": "json_object"}
    )
    return json.loads(resp.choices[0].message.content)["titles"]

def generate_article_html(prompt: str, num_sections: int = 5) -> dict:
    # タイトル生成
    title = generate_title_variants(prompt, n=1)[0]

    # リード文生成
    lead_msg = (
    "あなたは初心者にやさしいSEOライターです。\n"
        "この記事のリード文（導入部）を日本語で250文字程度、<h2>や<h3>は使わずに書いてください。3文ごとに改行を入れてわかりやすくしてください。\n"
        "「です・ます」調で、共感や具体例も交えてください。\n\n"
        "🎨 絵文字の使用ガイドライン：\n"
        "- 文章の約20%に適切な絵文字を自然に配置\n"
        "- 親しみやすさを演出する絵文字（😊 💡 ✨ 🎯 📝 🚀など）を効果的に活用\n\n"
    "・リズムを付けるため極端に長い文を避け、句点で適度に分割\n"
        "・想定読者：今からAIを使い始める幅広い年代層（初心者向け）\n"
        "・共感：情報提示 = 3:7〜4:6 程度\n"
        "・テンプレ的表現は避け、親しみやすい表現を使用\n"
        "JSONで{\"lead\": \"...\"}の形で返してください。"
    )
    lead_resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": lead_msg},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800,
        response_format={"type": "json_object"}
    )
    lead_text = json.loads(lead_resp.choices[0].message.content)["lead"]


    # 章ごと生成
    sections = []
    for i in range(1, num_sections + 1):
        section_msg = (
            "あなたは初心者にやさしいSEOライターです。\n"
            "この記事の第{i}章を日本語で340文字以上、<h2>で章タイトルを付けて書いてください。2文ごとに改行を入れてわかりやすくしてください。\n"
            "「です・ます」調で、共感や具体例も交えてください。\n\n"
            "🎨 絵文字の使用ガイドライン：\n"
            "- 本文の約20%の文に適切な絵文字を自然に配置\n"
            "- 感情表現（😊 🤔 😅）、強調（✨ 🎯 💡）、視覚的アクセント（📝 🚀 ⭐）を効果的に活用\n"
            "- 文末や重要なポイントで絵文字を使用して親しみやすさを演出\n\n"
            "プロンプト例が必要な場合は、以下の形式で対話形式で表現してください：\n"
            "❌ コード風: ```プロンプト例```\n"
            "✅ 対話風: 「ChatGPTに『〜について教えて』と聞いてみましょう」\n\n"
            "表を使用する場合は、以下のスタイルを参考にしてください：\n"
            "- 「NG例」「改善例」「効果・ポイント」の3列構成\n"
            "- 「Q: 質問」「A: 回答」のFAQ形式\n"
            "- 「ステップ」「内容」「ポイント」の手順表\n\n"
            "・リズムを付けるため極端に長い文を避け、句点で適度に分割\n"
            "・想定読者：今からAIを使い始める幅広い年代層（初心者向け）\n"
            "・テンプレ的表現は避け、親しみやすい表現を使用\n"
            "JSONで{\"section\": \"...\"}の形で返してください。"
        )
        section_resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": section_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        section_text = json.loads(section_resp.choices[0].message.content)["section"]
        sections.append(section_text)

    # FAQ生成
    faq_section = generate_faq_section(prompt, lead_text + "\n".join(sections[:2]))  # 最初の2章を参考に
    
    # 結合
    content = lead_text + "\n" + "\n".join(sections) + "\n" + faq_section
    return {
        "title": title,
        "content": content
    }


def generate_image_prompt(article_body: str) -> str:
    """
    記事本文HTMLから英語の画像生成プロンプトを作成（シンプルスタイル）
    """
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたは画像プロンプト作成のエキスパートです。"
                    "以下のHTML形式の記事に合った、非常にシンプルでミニマルな画像を生成するための"
                    "英語プロンプトを1文だけで答えてください。\n\n"
                    "要件：\n"
                    "- flat design, minimalist style を必ず含める\n"
                    "- 複雑な要素は避け、2-3個の基本的な要素のみ\n"
                    "- パステルカラーまたは白背景を使用\n"
                    "- アイコンやイラスト風のシンプルなデザイン\n"
                    "- 文字やテキストは含めない\n"
                    "- 例: 'Simple flat design icon of a lightbulb on white background, minimalist style, pastel colors'"
                )
            },
            {"role": "user", "content": article_body}
        ],
        temperature=0.5,
        max_tokens=200
    )
    return resp.choices[0].message.content.strip()


def generate_image_url(image_prompt: str) -> str:
    """
    DALL·E 3 に画像生成を頼み、URLを返す
    """
    response = openai.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        size="1792x1024",
        n=1
    )
    image_url = response.data[0].url
    return image_url


def generate_meta_description(prompt: str, content: str) -> str:
    """
    記事のmeta descriptionを生成（150-160文字程度）
    """
    desc_msg = (
        "あなたはSEO専門ライターです。\n"
        "この記事のmeta description（検索結果に表示される説明文）を日本語で150文字以内で書いてください。\n"
        "・検索ユーザーがクリックしたくなるような魅力的な文章\n"
        "・記事の要点を簡潔にまとめる\n"
        "・キーワードを自然に含める\n"
        "・「です・ます」調で統一\n"
        "JSONで{\"description\": \"...\"}の形で返してください。"
    )
    desc_resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": desc_msg},
            {"role": "user", "content": f"テーマ: {prompt}\n記事内容: {content[:500]}..."}
        ],
        temperature=0.5,
        max_tokens=300,
        response_format={"type": "json_object"}
    )
    return json.loads(desc_resp.choices[0].message.content)["description"]


def generate_seo_tags(prompt: str, content: str) -> list[str]:
    """
    記事のSEO効果的なWordPressタグを3つ生成
    """
    tags_msg = (
        "あなたはSEO専門家です。\n"
        "この記事に最適なWordPressタグを3つ選んでください。\n"
        "・SEO効果が高く、検索されやすいキーワード\n"
        "・記事内容と関連性が高いもの\n"
        "・一般的すぎず、具体的すぎない適度な粒度\n"
        "・日本語で、各タグは2-4文字程度\n"
        "・例: 'AI', 'ChatGPT', '無料ツール', '初心者向け' など\n"
        "JSONで{\"tags\": [\"タグ1\", \"タグ2\", \"タグ3\"]}の形で返してください。"
    )
    tags_resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": tags_msg},
            {"role": "user", "content": f"テーマ: {prompt}\n記事内容: {content[:300]}..."}
        ],
        temperature=0.5,
        max_tokens=200,
        response_format={"type": "json_object"}
    )
    return json.loads(tags_resp.choices[0].message.content)["tags"]


def generate_seo_slug(prompt: str, title: str) -> str:
    """
    記事のSEO効果的なアルファベットスラッグを生成（3-5語程度）
    """
    slug_msg = (
        "あなたはSEO専門家です。\n"
        "この記事のWordPressスラッグ（URL）を英語で生成してください。\n"
        "・3-5語程度の短いフレーズ\n"
        "・ハイフンで区切る（例: chatgpt-free-guide）\n"
        "・SEOキーワードを含む\n"
        "・記事内容を表す分かりやすい英語\n"
        "・小文字のみ使用\n"
        "・数字は使用可能\n"
        "JSONで{\"slug\": \"...\"}の形で返してください。"
    )
    slug_resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": slug_msg},
            {"role": "user", "content": f"キーワード: {prompt}\nタイトル: {title}"}
        ],
        temperature=0.3,
        max_tokens=150,
        response_format={"type": "json_object"}
    )
    return json.loads(slug_resp.choices[0].message.content)["slug"]


def extract_article_structure(url_or_content: str, content_type: str = "url") -> dict:
    """
    参考記事からHTMLまたはマークダウンの構造を抽出
    content_type: "url", "html", "markdown"
    """
    if content_type == "url":
        # URLから記事を取得
        try:
            response = requests.get(url_or_content, timeout=30)
            response.raise_for_status()
            html_content = response.text
        except Exception as e:
            print(f"URL取得エラー: {e}")
            return {"error": str(e)}
            
        # HTMLから構造抽出
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 不要な要素を削除
        for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
            
        # タイトル抽出
        title = ""
        if soup.find('h1'):
            title = soup.find('h1').get_text().strip()
        elif soup.find('title'):
            title = soup.find('title').get_text().strip()
            
        # 見出しと内容抽出
        sections = []
        for i, heading in enumerate(soup.find_all(['h2', 'h3', 'h4'])):
            heading_text = heading.get_text().strip()
            
            # 見出し後の内容を取得
            content_parts = []
            current = heading.next_sibling
            while current and current.name not in ['h1', 'h2', 'h3', 'h4']:
                if hasattr(current, 'get_text'):
                    text = current.get_text().strip()
                    if text and len(text) > 10:  # 短すぎるテキストは除外
                        content_parts.append(text)
                current = current.next_sibling
                if len(content_parts) > 3:  # 長すぎる場合は制限
                    break
                    
            sections.append({
                "heading": heading_text,
                "content": " ".join(content_parts)[:200] + "..." if content_parts else ""
            })
            
            if len(sections) >= 5:  # 最大5つまで
                break
        
        return {
            "title": title,
            "sections": sections,
            "total_sections": len(sections)
        }
        
    elif content_type == "html":
        # HTMLコンテンツから直接抽出
        soup = BeautifulSoup(url_or_content, 'html.parser')
        # 上記と同じ処理...
        
    elif content_type == "markdown":
        # マークダウンから構造抽出
        lines = url_or_content.split('\n')
        sections = []
        current_section = None
        
        for line in lines:
            if line.startswith('#'):
                if current_section:
                    sections.append(current_section)
                    
                level = len(line) - len(line.lstrip('#'))
                heading = line.lstrip('# ').strip()
                current_section = {
                    "heading": heading,
                    "content": "",
                    "level": level
                }
            elif current_section and line.strip():
                current_section["content"] += line + " "
                
        if current_section:
            sections.append(current_section)
            
        # h2レベルのセクションのみ抽出
        h2_sections = [s for s in sections if s.get("level", 0) == 2][:5]
        
        return {
            "title": next((s["heading"] for s in sections if s.get("level", 0) == 1), ""),
            "sections": h2_sections,
            "total_sections": len(h2_sections)
        }
    
    return {"error": "サポートされていないコンテンツタイプ"}

def generate_article_from_reference(prompt: str, reference_structure: dict, num_sections: int = 5) -> dict:
    """
    参考記事の構造に基づいて記事を生成
    """
    if "error" in reference_structure:
        return {"error": "参考記事の構造取得に失敗しました"}
    
    # 参考記事の構造をプロンプトに組み込み
    structure_text = f"参考記事のタイトル: {reference_structure.get('title', '')}\n\n"
    structure_text += "参考記事の見出し構成:\n"
    
    for i, section in enumerate(reference_structure.get('sections', [])[:num_sections], 1):
        structure_text += f"{i}. {section['heading']}\n"
        if section.get('content'):
            structure_text += f"   内容の概要: {section['content'][:100]}...\n"
    
    # タイトル生成（参考記事を考慮）
    title_prompt = f"""
以下の参考記事の構成を参考に、「{prompt}」というテーマで魅力的な日本語タイトルを生成してください。

{structure_text}

参考記事の構成やアプローチを参考にしつつ、独自性のあるタイトルを作成してください。
"""
    
    title = generate_title_variants(title_prompt, n=1)[0]

    # リード文生成（参考記事を考慮）
    lead_msg = (
        "あなたはSEO向け長文ライターです。\n"
        f"「{prompt}」についての記事のリード文（導入部）を日本語で250文字程度、<h2>や<h3>は使わずに書いてください。\n"
        "以下の参考記事の構成やアプローチを参考にしてください：\n\n"
        f"{structure_text}\n\n"
        "・3文ごとに改行を入れてわかりやすくしてください\n"
        "・「です・ます」調で、共感や具体例も交えてください\n"
        "・リズムを付けるため極端に長い文を避け、句点で適度に分割\n"
        "・想定読者：今からAIを使い始める幅広い年代層\n"
        "・テンプレ的表現は避けてください\n"
        "JSONで{\"lead\": \"...\"}の形で返してください。"
    )
    
    lead_resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": lead_msg},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800,
        response_format={"type": "json_object"}
    )
    lead_text = json.loads(lead_resp.choices[0].message.content)["lead"]

    # 章ごと生成（参考記事の構造を活用）
    sections = []
    ref_sections = reference_structure.get('sections', [])
    
    for i in range(1, num_sections + 1):
        # 参考記事の対応する章があれば参考にする
        ref_section = ref_sections[i-1] if i-1 < len(ref_sections) else None
        
        section_msg = (
            "あなたはSEO向け長文ライターです。\n"
            f"「{prompt}」についての記事の第{i}章を日本語で340文字以上、<h2>で章タイトルを付けて書いてください。\n"
        )
        
        if ref_section:
            section_msg += f"参考となる章の見出し: 「{ref_section['heading']}」\n"
            if ref_section.get('content'):
                section_msg += f"参考章の内容概要: {ref_section['content'][:150]}...\n"
            section_msg += "上記を参考にしつつ、独自性のある内容で章を作成してください。\n\n"
            
        section_msg += (
            "・2文ごとに改行を入れてわかりやすくしてください\n"
            "・「です・ます」調で、共感や具体例も交えてください\n"
            "・想定読者：今からAIを使い始める幅広い年代層\n"
            "・テンプレ的表現は避けてください\n"
            "JSONで{\"section\": \"...\"}の形で返してください。"
        )
        
        section_resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": section_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        section_text = json.loads(section_resp.choices[0].message.content)["section"]
        sections.append(section_text)

    # FAQ生成
    faq_section = generate_faq_section(prompt, lead_text + "\n".join(sections[:2]))  # 最初の2章を参考に
    
    # 結合
    content = lead_text + "\n" + "\n".join(sections) + "\n" + faq_section
    return {
        "title": title,
        "content": content,
        "reference_used": True
    }

def extract_multiple_article_structures(sources: list, content_types: list = None) -> dict:
    """
    複数の参考記事から構造を抽出・統合
    sources: URLまたはファイルパスのリスト
    content_types: 各ソースのタイプリスト ["url", "file", "markdown", "html"]
    """
    if content_types is None:
        # 自動判定
        content_types = []
        for source in sources:
            if source.startswith(('http://', 'https://')):
                content_types.append('url')
            elif source.endswith('.md'):
                content_types.append('markdown')
            else:
                content_types.append('html')
    
    all_structures = []
    successful_sources = []
    
    for i, (source, content_type) in enumerate(zip(sources, content_types)):
        print(f"📖 参考記事 {i+1}/{len(sources)} を処理中: {source}")
        
        try:
            if content_type == 'url':
                structure = extract_article_structure(source, "url")
            elif content_type in ['markdown', 'html']:
                if content_type == 'markdown':
                    with open(source, 'r', encoding='utf-8') as f:
                        content = f.read()
                    structure = extract_article_structure(content, "markdown")
                else:
                    with open(source, 'r', encoding='utf-8') as f:
                        content = f.read()
                    structure = extract_article_structure(content, "html")
            
            if "error" not in structure:
                all_structures.append({
                    'source': source,
                    'structure': structure,
                    'weight': 1.0  # 将来的に重み付けも可能
                })
                successful_sources.append(source)
                print(f"✅ 成功: {structure['total_sections']}セクション抽出")
            else:
                print(f"❌ エラー: {structure['error']}")
                
        except Exception as e:
            print(f"❌ 例外: {source} - {e}")
    
    if not all_structures:
        return {"error": "すべての参考記事の処理に失敗しました"}
    
    # 複数構造を統合
    return integrate_multiple_structures(all_structures)

def integrate_multiple_structures(structures_data: list) -> dict:
    """
    複数の記事構造を統合して最適化された構造を作成
    """
    if len(structures_data) == 1:
        # 1つの場合はそのまま返す
        return structures_data[0]['structure']
    
    # 全てのセクションを収集
    all_sections = []
    all_titles = []
    
    for data in structures_data:
        structure = data['structure']
        source = data['source']
        
        all_titles.append(structure.get('title', ''))
        
        for section in structure.get('sections', []):
            all_sections.append({
                'heading': section['heading'],
                'content': section.get('content', ''),
                'source': source,
                'weight': data['weight']
            })
    
    # セクションを分析・統合
    integrated_sections = optimize_section_combination(all_sections)
    
    # 代表タイトルを選択（最も長いものか、最初のもの）
    representative_title = max(all_titles, key=len) if all_titles else ""
    
    return {
        "title": representative_title,
        "sections": integrated_sections[:5],  # 最大5セクション
        "total_sections": len(integrated_sections[:5]),
        "source_count": len(structures_data),
        "sources": [data['source'] for data in structures_data]
    }

def optimize_section_combination(all_sections: list) -> list:
    """
    複数記事のセクションを最適に組み合わせ
    """
    # セクションの類似性を分析
    section_clusters = cluster_similar_sections(all_sections)
    
    # 各クラスターから最適なセクションを選択
    optimized_sections = []
    
    for cluster in section_clusters:
        # クラスター内で最も内容が豊富なセクションを選択
        best_section = max(cluster, key=lambda s: len(s.get('content', '')))
        
        # 他のセクションの良い要素も統合
        enhanced_content = enhance_section_with_cluster(best_section, cluster)
        
        optimized_sections.append({
            'heading': best_section['heading'],
            'content': enhanced_content,
            'sources': [s['source'] for s in cluster]
        })
    
    # 重要度でソート（内容の長さ等で判定）
    optimized_sections.sort(key=lambda s: len(s['content']), reverse=True)
    
    return optimized_sections

def cluster_similar_sections(sections: list) -> list:
    """
    類似するセクションをクラスター化
    """
    clusters = []
    processed = set()
    
    for i, section in enumerate(sections):
        if i in processed:
            continue
            
        cluster = [section]
        processed.add(i)
        
        # 類似セクションを探す
        for j, other_section in enumerate(sections[i+1:], i+1):
            if j in processed:
                continue
                
            if are_sections_similar(section, other_section):
                cluster.append(other_section)
                processed.add(j)
        
        clusters.append(cluster)
    
    return clusters

def are_sections_similar(section1: dict, section2: dict) -> bool:
    """
    2つのセクションが類似しているかを判定
    """
    heading1 = section1['heading'].lower()
    heading2 = section2['heading'].lower()
    
    # 簡単な類似度判定（より高度な手法も可能）
    common_words = set(heading1.split()) & set(heading2.split())
    
    # 共通単語が多い、または片方が他方を含む場合は類似とみなす
    return len(common_words) >= 2 or heading1 in heading2 or heading2 in heading1

def enhance_section_with_cluster(main_section: dict, cluster: list) -> str:
    """
    クラスター内の他のセクションの要素を使って内容を拡充
    """
    enhanced_content = main_section.get('content', '')
    
    # 他のセクションから有用な要素を抽出
    additional_insights = []
    for section in cluster:
        if section != main_section and section.get('content'):
            content = section['content']
            if len(content) > 50 and content not in enhanced_content:
                additional_insights.append(content[:100] + "...")
    
    if additional_insights:
        enhanced_content += " [追加の視点: " + " / ".join(additional_insights) + "]"
    
    return enhanced_content

def generate_article_from_multiple_references(prompt: str, integrated_structure: dict, num_sections: int = 5) -> dict:
    """
    複数の参考記事を統合した構造に基づいて記事を生成
    """
    if "error" in integrated_structure:
        return {"error": "参考記事の統合に失敗しました"}
    
    source_count = integrated_structure.get('source_count', 1)
    sources = integrated_structure.get('sources', [])
    
    # 参考記事の構造をプロンプトに組み込み
    structure_text = f"統合された参考記事情報（{source_count}つのソースから統合）:\n"
    structure_text += f"参考記事のタイトル: {integrated_structure.get('title', '')}\n\n"
    structure_text += "統合された見出し構成:\n"
    
    for i, section in enumerate(integrated_structure.get('sections', [])[:num_sections], 1):
        structure_text += f"{i}. {section['heading']}\n"
        if section.get('content'):
            structure_text += f"   内容の概要: {section['content'][:150]}...\n"
        if section.get('sources'):
            structure_text += f"   ソース: {len(section['sources'])}つの記事から統合\n"
    
    structure_text += f"\n参考にしたソース:\n"
    for i, source in enumerate(sources, 1):
        source_name = source.split('/')[-1] if '/' in source else source
        structure_text += f"- {source_name}\n"
    
    # タイトル生成（複数参考記事を考慮）
    title_prompt = f"""
以下の複数の参考記事を統合した構成を参考に、「{prompt}」というテーマで魅力的な日本語タイトルを生成してください。

{structure_text}

複数の記事のアプローチを融合し、より包括的で魅力的なタイトルを作成してください。
"""
    
    title = generate_title_variants(title_prompt, n=1)[0]

    # リード文生成（複数参考記事を考慮）
    lead_msg = (
        "あなたはSEO向け長文ライターです。\n"
        f"「{prompt}」についての記事のリード文（導入部）を日本語で250文字程度、<h2>や<h3>は使わずに書いてください。\n"
        f"以下の{source_count}つの参考記事を統合した構成やアプローチを参考にしてください：\n\n"
        f"{structure_text}\n\n"
        "・複数の視点を統合した包括的な導入にしてください\n"
        "・3文ごとに改行を入れてわかりやすくしてください\n"
        "・「です・ます」調で、共感や具体例も交えてください\n"
        "・想定読者：今からAIを使い始める幅広い年代層\n"
        "・テンプレ的表現は避けてください\n"
        "JSONで{\"lead\": \"...\"}の形で返してください。"
    )
    
    lead_resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": lead_msg},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800,
        response_format={"type": "json_object"}
    )
    lead_text = json.loads(lead_resp.choices[0].message.content)["lead"]

    # 章ごと生成（統合された構造を活用）
    sections = []
    integrated_sections = integrated_structure.get('sections', [])
    
    for i in range(1, num_sections + 1):
        # 統合された対応する章があれば参考にする
        ref_section = integrated_sections[i-1] if i-1 < len(integrated_sections) else None
        
        section_msg = (
            "あなたはSEO向け長文ライターです。\n"
            f"「{prompt}」についての記事の第{i}章を日本語で340文字以上、<h2>で章タイトルを付けて書いてください。\n"
        )
        
        if ref_section:
            section_msg += f"参考となる統合章の見出し: 「{ref_section['heading']}」\n"
            if ref_section.get('content'):
                section_msg += f"統合された内容概要: {ref_section['content'][:200]}...\n"
            if ref_section.get('sources'):
                section_msg += f"この章は{len(ref_section['sources'])}つのソースから統合されています。\n"
            section_msg += "上記の統合された情報を参考にしつつ、独自性と包括性のある内容で章を作成してください。\n\n"
            
        section_msg += (
            "・複数の視点を統合した豊富な内容にしてください\n"
            "・2文ごとに改行を入れてわかりやすくしてください\n"
            "・「です・ます」調で、共感や具体例も交えてください\n"
            "・想定読者：今からAIを使い始める幅広い年代層\n"
            "・テンプレ的表現は避けてください\n"
            "JSONで{\"section\": \"...\"}の形で返してください。"
        )
        
        section_resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": section_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        section_text = json.loads(section_resp.choices[0].message.content)["section"]
        sections.append(section_text)

    # FAQ生成
    faq_section = generate_faq_section(prompt, lead_text + "\n".join(sections[:2]))  # 最初の2章を参考に
    
    # 結合
    content = lead_text + "\n" + "\n".join(sections) + "\n" + faq_section
    return {
        "title": title,
        "content": content,
        "reference_used": True,
        "multiple_references": True,
        "source_count": source_count,
        "sources": sources
    }

def extract_style_features_from_sources(sources: list, content_types: list = None) -> dict:
    """
    複数ソースからスタイル特徴を抽出
    """
    if content_types is None:
        content_types = []
        for source in sources:
            if source.startswith(('http://', 'https://')):
                content_types.append('url')
            elif source.endswith('.md'):
                content_types.append('markdown')
            else:
                content_types.append('html')
    
    all_style_features = []
    
    for i, (source, content_type) in enumerate(zip(sources, content_types)):
        print(f"🎨 スタイル分析 {i+1}/{len(sources)}: {source}")
        
        try:
            # コンテンツを取得
            if content_type == 'url':
                response = requests.get(source, timeout=30)
                response.raise_for_status()
                raw_content = response.text
                # HTMLからテキストを抽出
                soup = BeautifulSoup(raw_content, 'html.parser')
                for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
                    tag.decompose()
                content = soup.get_text('\n')
            elif content_type == 'markdown':
                with open(source, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:  # html
                with open(source, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
                soup = BeautifulSoup(raw_content, 'html.parser')
                content = soup.get_text('\n')
            
            # スタイル特徴を抽出
            features = analyze_style_features(content, source)
            if features:
                all_style_features.append(features)
                print(f"✅ スタイル特徴抽出完了")
            
        except Exception as e:
            print(f"❌ スタイル抽出エラー: {source} - {e}")
    
    if not all_style_features:
        return {"error": "スタイル特徴の抽出に失敗しました"}
    
    # 複数記事のスタイル特徴を統合
    return merge_style_features(all_style_features)

def analyze_style_features(content: str, source: str) -> dict:
    """
    単一コンテンツからスタイル特徴を分析
    """
    lines = content.split('\n')
    total_chars = len(content)
    total_lines = len(lines)
    
    # 見出し分析
    h1_pattern = re.compile(r'^#\s+(.+)', re.MULTILINE)
    h2_pattern = re.compile(r'^##\s+(.+)', re.MULTILINE)
    h3_pattern = re.compile(r'^###\s+(.+)', re.MULTILINE)
    
    h1_matches = h1_pattern.findall(content)
    h2_matches = h2_pattern.findall(content)
    h3_matches = h3_pattern.findall(content)
    
    all_headings = h1_matches + h2_matches + h3_matches
    
    # 絵文字分析
    emoji_pattern = re.compile(r'[🚀🔥💡📊🎯⚡🌟✨📈🎉💪🔧📝🆕👍🔍📚🎨🎪]')
    emoji_in_headings = sum(1 for h in all_headings if emoji_pattern.search(h))
    total_emojis = len(emoji_pattern.findall(content))
    
    # 箇条書き分析
    bullet_patterns = [
        re.compile(r'^\s*[-•*]\s+', re.MULTILINE),
        re.compile(r'^\s*\d+\.\s+', re.MULTILINE),
    ]
    total_bullets = sum(len(pattern.findall(content)) for pattern in bullet_patterns)
    
    # 文体分析
    sentences = re.split(r'[。！？]', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    avg_sentence_length = sum(len(s) for s in sentences) / max(1, len(sentences))
    
    # 専門用語・英語分析
    english_words = re.findall(r'\b[A-Za-z]{3,}\b', content)
    english_ratio = len(english_words) / max(1, len(content.split()))
    
    # コードブロック・表の分析
    code_blocks = len(re.findall(r'```[\s\S]*?```', content))
    tables = len(re.findall(r'\|.+\|', content))
    
    # 語尾分析（です・ます調 vs である調）
    desu_masu = len(re.findall(r'(です|ます|でしょう)。', content))
    de_aru = len(re.findall(r'(である|だ)。', content))
    
    word_count = len(content.split())
    
    return {
        "source": source,
        "total_chars": total_chars,
        "word_count": word_count,
        "h1_count": len(h1_matches),
        "h2_count": len(h2_matches),
        "h3_count": len(h3_matches),
        "h2_per_1000_words": (len(h2_matches) * 1000) / max(1, word_count),
        "emoji_in_headings": emoji_in_headings,
        "emoji_in_headings_ratio": emoji_in_headings / max(1, len(all_headings)),
        "total_emojis": total_emojis,
        "emoji_density": total_emojis / max(1, total_chars / 1000),
        "bullet_count": total_bullets,
        "bullet_density": total_bullets / max(1, total_lines),
        "avg_sentence_length": avg_sentence_length,
        "english_word_ratio": english_ratio,
        "code_blocks": code_blocks,
        "tables": tables,
        "desu_masu_ratio": desu_masu / max(1, desu_masu + de_aru),
        "formality_score": desu_masu / max(1, len(sentences))
    }

def merge_style_features(style_features_list: list) -> dict:
    """
    複数記事のスタイル特徴を統合
    """
    if len(style_features_list) == 1:
        return style_features_list[0]
    
    # 数値特徴の平均を計算
    numeric_features = [
        'h2_per_1000_words', 'emoji_in_headings_ratio', 'emoji_density',
        'bullet_density', 'avg_sentence_length', 'english_word_ratio',
        'desu_masu_ratio', 'formality_score'
    ]
    
    merged = {"source_count": len(style_features_list), "sources": []}
    
    for feature in numeric_features:
        values = [sf[feature] for sf in style_features_list if feature in sf]
        if values:
            merged[feature] = round(st.mean(values), 3)
    
    # カテゴリ特徴の統合
    merged['total_code_blocks'] = sum(sf.get('code_blocks', 0) for sf in style_features_list)
    merged['total_tables'] = sum(sf.get('tables', 0) for sf in style_features_list)
    merged['sources'] = [sf.get('source', '') for sf in style_features_list]
    
    # スタイル判定
    if merged.get('emoji_in_headings_ratio', 0) > 0.5:
        merged['heading_style'] = 'emoji_rich'
    elif merged.get('emoji_in_headings_ratio', 0) > 0.2:
        merged['heading_style'] = 'moderate_emoji'
    else:
        merged['heading_style'] = 'minimal_emoji'
    
    if merged.get('desu_masu_ratio', 0) > 0.7:
        merged['tone'] = 'polite'
    elif merged.get('desu_masu_ratio', 0) > 0.3:
        merged['tone'] = 'mixed'
    else:
        merged['tone'] = 'casual'
    
    if merged.get('bullet_density', 0) > 0.1:
        merged['structure_style'] = 'list_heavy'
    elif merged.get('bullet_density', 0) > 0.05:
        merged['structure_style'] = 'moderate_lists'
    else:
        merged['structure_style'] = 'paragraph_focused'
    
    return merged

def generate_style_yaml(merged_features: dict) -> str:
    """
    統合されたスタイル特徴からYAMLガイドを生成
    """
    style_guide = {
        "document_style": {
            "heading_frequency": f"{merged_features.get('h2_per_1000_words', 3):.1f} H2見出し per 1000語",
            "emoji_usage": {
                "in_headings": f"{merged_features.get('emoji_in_headings_ratio', 0)*100:.0f}%の見出しに絵文字",
                "overall_density": f"{merged_features.get('emoji_density', 0):.2f} 絵文字 per 1000文字",
                "style": merged_features.get('heading_style', 'moderate_emoji')
            },
            "structure": {
                "bullet_density": f"{merged_features.get('bullet_density', 0)*100:.1f}%の行が箇条書き",
                "style": merged_features.get('structure_style', 'moderate_lists'),
                "code_blocks": merged_features.get('total_code_blocks', 0) > 0,
                "tables": merged_features.get('total_tables', 0) > 0
            },
            "writing_style": {
                "tone": merged_features.get('tone', 'polite'),
                "avg_sentence_length": f"{merged_features.get('avg_sentence_length', 30):.0f}文字",
                "formality": merged_features.get('formality_score', 0.5),
                "english_ratio": f"{merged_features.get('english_word_ratio', 0)*100:.1f}%"
            }
        },
        "generation_rules": {
            "見出し": "H2見出しに絵文字を適度に使用",
            "箇条書き": "• を使用し、適度な密度で配置",
            "語調": "です・ます調" if merged_features.get('tone') == 'polite' else "混合調",
            "文長": "読みやすい長さに調整",
            "構成": "視覚的にわかりやすく整理"
        },
        "reference_info": {
            "source_count": merged_features.get('source_count', 1),
            "analyzed_sources": merged_features.get('sources', [])
        }
    }
    
    return yaml.dump(style_guide, allow_unicode=True, default_flow_style=False, sort_keys=False)

def generate_article_with_style_guide(prompt: str, integrated_structure: dict, style_features: dict, num_sections: int = 5) -> dict:
    """
    スタイルガイドを使用して記事を生成
    """
    if "error" in integrated_structure:
        return {"error": "参考記事の統合に失敗しました"}
    
    if "error" in style_features:
        return {"error": "スタイル特徴の抽出に失敗しました"}
    
    # スタイルガイドYAMLを生成
    style_yaml = generate_style_yaml(style_features)
    
    source_count = integrated_structure.get('source_count', 1)
    sources = integrated_structure.get('sources', [])
    
    # 構造情報
    structure_text = f"統合された参考記事情報（{source_count}つのソースから統合）:\n"
    structure_text += f"参考記事のタイトル: {integrated_structure.get('title', '')}\n\n"
    structure_text += "統合された見出し構成:\n"
    
    for i, section in enumerate(integrated_structure.get('sections', [])[:num_sections], 1):
        structure_text += f"{i}. {section['heading']}\n"
        if section.get('content'):
            structure_text += f"   内容の概要: {section['content'][:150]}...\n"
    
    # スタイルガイド付きシステムプロンプト
    system_prompt = f"""
あなたは視覚的にわかりやすい技術ライターです。

## スタイルガイド（統合された参考記事の特徴）
```yaml
{style_yaml}
```

## 出力要件
- 上記YAMLのスタイル特徴を**厳密に反映**して記事を生成
- すべて **HTML** で書く（WordPressに適した形式）
- 見出しは &lt;h2&gt;タグを使用（絵文字込み）
- 見出し頻度: {style_features.get('h2_per_1000_words', 3):.1f}本/1000語 程度
- 絵文字使用: {style_features.get('emoji_in_headings_ratio', 0)*100:.0f}%の見出しに適切な絵文字
- 箇条書きは &lt;ul&gt;&lt;li&gt;タグを使用
- 箇条書き密度: {style_features.get('bullet_density', 0)*100:.1f}%程度
- 語調: {"です・ます調" if style_features.get('tone') == 'polite' else "自然な混合調"}
- 文長: 平均{style_features.get('avg_sentence_length', 30):.0f}文字程度

## 参考構造
{structure_text}

上記の構造とスタイルを融合し、「{prompt}」について包括的で読みやすい記事を生成してください。
"""

    # タイトル生成
    title_resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"「{prompt}」というテーマで、上記スタイルガイドに従った魅力的なタイトルを1つ生成してください。JSONで{{\"title\": \"...\"}}の形で返してください。"}
        ],
        temperature=0.7,
        max_tokens=200,
        response_format={"type": "json_object"}
    )
    title = json.loads(title_resp.choices[0].message.content)["title"]

    # 記事本文生成
    content_resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"「{prompt}」について、統合されたスタイルガイドに従って2000文字程度の記事を生成してください。参考構造を活用し、{num_sections}つの主要セクションで構成してください。"}
        ],
        temperature=0.7,
        max_tokens=3000
    )
    content = content_resp.choices[0].message.content

    # FAQ生成
    faq_section = generate_faq_section(prompt, content[:1000])  # 記事の最初の1000文字を参考に
    
    # FAQを記事に追加
    content += "\n" + faq_section
    
    return {
        "title": title,
        "content": content,
        "reference_used": True,
        "multiple_references": True,
        "style_guided": True,
        "source_count": source_count,
        "sources": sources,
        "style_features": style_features,
        "style_yaml": style_yaml
    }

def generate_keyword_article_with_style(keyword: str, style_features: dict, num_sections: int = 5) -> dict:
    """
    キーワードベースでスタイルガイドを適用した記事を生成
    """
    if "error" in style_features:
        return {"error": "スタイル特徴の抽出に失敗しました"}
    
    # スタイルガイドYAMLを生成
    style_yaml = generate_style_yaml(style_features)
    
    # スタイルガイド付きシステムプロンプト
    system_prompt = f"""
あなたは視覚的にわかりやすい技術ライターです。

## スタイルガイド（参考記事から抽出されたスタイル特徴）
```yaml
{style_yaml}
```

## 出力要件
- 上記YAMLのスタイル特徴を**厳密に反映**して記事を生成
- すべて **HTML** で書く（WordPressに適した形式）
- 見出しは &lt;h2&gt;タグを使用（絵文字込み）
- 見出し頻度: {style_features.get('h2_per_1000_words', 3):.1f}本/1000語 程度
- 絵文字使用: {style_features.get('emoji_in_headings_ratio', 0)*100:.0f}%の見出しに適切な絵文字
- 箇条書きは &lt;ul&gt;&lt;li&gt;タグを使用
- 箇条書き密度: {style_features.get('bullet_density', 0)*100:.1f}%程度
- **リッチな表を積極活用**: 比較・手順・データは&lt;table&gt;&lt;tr&gt;&lt;td&gt;タグで構造化
- **対話形式のプロンプト例**: 実際の会話形式で表現（例：「〜について教えて」）
- 語調: {"です・ます調" if style_features.get('tone') == 'polite' else "自然な混合調"}
- 文長: 平均{style_features.get('avg_sentence_length', 30):.0f}文字程度
- **本文絵文字**: 文章の約20%に適切な絵文字を自然に配置（感情表現・強調・視覚的アクセント）

## 記事生成指針（AI-GENEスタイル準拠）
以下の要素を必ず含めてください：
1. **比較表（リッチスタイル）**: 「NG例」「改善例」「効果」の3列構成でわかりやすく
2. **対話形式の例**: プロンプトは会話形式で表現（「ChatGPTに『〜について教えて』と聞いてみましょう」）
3. **FAQ形式**: Q&A形式で読みやすく情報を整理
4. **段階的な手順**: 初心者でもわかるステップバイステップ構成
5. **具体的な事例**: 実際に使える例を豊富に提供

## キーワードベース記事生成
「{keyword}」というキーワードをテーマに、上記スタイルガイドに従った記事を生成してください。
- SEOを意識した構成
- 検索ユーザーのニーズに応える内容
- 参考記事のスタイルを忠実に再現
- 表・プロンプト例・具体例を積極的に活用
"""

    # タイトル生成
    title_resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"「{keyword}」というキーワードで、上記スタイルガイドに従った魅力的なタイトルを1つ生成してください。JSONで{{\"title\": \"...\"}}の形で返してください。"}
        ],
        temperature=0.7,
        max_tokens=200,
        response_format={"type": "json_object"}
    )
    title = json.loads(title_resp.choices[0].message.content)["title"]

    # リード文生成
    lead_resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"「{keyword}」について、スタイルガイドに従ったリード文（導入部）を250文字程度で生成してください。JSONで{{\"lead\": \"...\"}}の形で返してください。"}
        ],
        temperature=0.7,
        max_tokens=800,
        response_format={"type": "json_object"}
    )
    lead_text = json.loads(lead_resp.choices[0].message.content)["lead"]

    # 実践的な例・プロンプト例を生成
    try:
        practical_examples = generate_practical_examples(keyword)
        print(f"✅ 実践例生成完了: {len(practical_examples)}文字")
    except Exception as e:
        print(f"⚠️ 実践例生成失敗: {e}")
        practical_examples = ""

    # 章ごと生成
    sections = []
    for i in range(1, num_sections + 1):
        # 3章目に実践例を挿入
        if i == 3 and practical_examples:
            user_content = f"「{keyword}」についての記事の第{i}章を、スタイルガイドに従って340文字以上で生成してください。見出しは&lt;h2&gt;&lt;/h2&gt;タグで囲んでください。\n\n🎨 絵文字ガイドライン：本文の約20%の文に自然に絵文字を配置（😊 ✨ 🎯 💡 📝 🚀など）\n\n以下の実践例を活用して実用的な内容にしてください。\n\n実践例:\n{practical_examples}\n\nJSONで{{\"section\": \"...\"}}の形で返してください。"
        else:
            user_content = f"「{keyword}」についての記事の第{i}章を、スタイルガイドに従って340文字以上で生成してください。見出しは&lt;h2&gt;&lt;/h2&gt;タグで囲んでください。\n\n🎨 絵文字ガイドライン：本文の約20%の文に自然に絵文字を配置（😊 ✨ 🎯 💡 📝 🚀など）\n\n可能な限り表・具体例・プロンプト例を含めて実践的な内容にしてください。JSONで{{\"section\": \"...\"}}の形で返してください。"
        
        section_resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        section_text = json.loads(section_resp.choices[0].message.content)["section"]
        sections.append(section_text)

    # FAQ生成
    faq_section = generate_faq_section(keyword, lead_text + "\n".join(sections[:2]))  # 最初の2章を参考に
    
    # 結合
    content = lead_text + "\n" + "\n".join(sections) + "\n" + faq_section
    
    return {
        "title": title,
        "content": content,
        "reference_used": True,
        "style_guided": True,
        "keyword_based": True,
        "keyword": keyword,
        "style_features": style_features,
        "style_yaml": style_yaml
    }

def generate_practical_examples(keyword: str) -> str:
    """
    キーワードに応じた実践的な例・プロンプト例を生成
    """
    example_resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system", 
                "content": """
あなたは初心者にやさしい実践例・対話例の専門家です。
与えられたキーワードに応じて、読者が実際に試せる具体的な例を生成してください。

## 出力形式（AI-GENEスタイル準拠）
以下の要素を含むHTMLで返してください：
1. **比較表（3列構成）**: 「NG例」「改善例」「効果・ポイント」の構成で視覚的にわかりやすく
2. **対話形式の例**: 「ChatGPTに『〜について教えて』と聞いてみましょう」形式
3. **FAQ形式**: 「Q: よくある質問」「A: わかりやすい回答」形式
4. **段階的な手順**: 初心者でも迷わない1-2-3ステップ構成

## 重要な指針
- プロンプト例は必ず対話形式で表現（コード風ではなく、自然な会話）
- 表は情報が整理され、初心者が一目で理解できるスタイル
- 専門用語は使わず、やさしい言葉で説明

JSONで{"examples": "..."}の形で返してください。
"""
            },
            {"role": "user", "content": f"「{keyword}」に関する実践的な例・比較表・プロンプト例を生成してください。"}
        ],
        temperature=0.7,
        max_tokens=1000,
        response_format={"type": "json_object"}
    )
    
    return json.loads(example_resp.choices[0].message.content)["examples"]

def generate_faq_section(prompt: str, article_content: str) -> str:
    """
    記事のテーマに関連したFAQ 3つを生成（AI-GENEスタイル）
    """
    faq_resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
あなたは読者の疑問を先読みするFAQ専門ライターです。
与えられた記事テーマと内容から、読者が必ず抱く質問を3つ選んで、Q&A形式で回答してください。

## 出力要件
- HTMLで&lt;h3&gt;タグを使用してFAQセクションを作成
- 各質問は&lt;h4&gt;タグで「Q: 質問内容」形式
- 各回答は&lt;p&gt;タグで「A: 回答内容」形式  
- 絵文字を効果的に活用（質問に❓、回答に✅など）
- 初心者でもわかりやすい言葉で回答
- 実践的で具体的な内容

## FAQ選定基準
1. 初心者が必ず疑問に思うこと
2. 記事を読んだ後の次のアクション
3. よくある誤解や注意点

JSONで{"faq": "..."}の形で返してください。
"""
            },
            {"role": "user", "content": f"記事テーマ: {prompt}\n\n記事内容の要約: {article_content[:500]}..."}
        ],
        temperature=0.7,
        max_tokens=800,
        response_format={"type": "json_object"}
    )
    return json.loads(faq_resp.choices[0].message.content)["faq"]

if __name__ == "__main__":
    keyword = get_next_keyword(col=0)  # A列からキーワードを取得
    prompt = f"{keyword}についての記事を書いてください。SEOを意識して、検索ユーザーのニーズに応える内容にしてください。"
    print("★今回のプロンプト:", prompt)
    print(generate_title_variants(prompt, n=3))
    article = generate_article_html(prompt)
    print(article)

