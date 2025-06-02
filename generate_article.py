import os
import openai
import json
import re
import csv
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
        "あなたはSEO向け長文ライターです。\n"
        "この記事のリード文（導入部）を日本語で250文字程度、<h2>や<h3>は使わずに書いてください。3文ごとに改行を入れてわかりやすくしてください。\n"
        "「です・ます」調で、共感や具体例も交えてください。\n"
        "・リズムを付けるため極端に長い文を避け、句点で適度に分割。\n"
        "- 想定読者（ペルソナ）：{{今からAIを使い始める幅広い年代層。置いていかれてるかもしれないという不安のあるひとたち}}\n"
        "- 記事の目的（CV）:{{アフィリエイト広告収入}} \n"
        "・ 共感：情報提示 : 3:7〜4:6 程度にしてください\n"
        "・テンプレ的表現（「〜をご存じですか？」「注目されています」など）は避けてください\n"
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
            "あなたはSEO向け長文ライターです。\n"
            f"この記事の第{i}章を日本語で340文字以上、<h2>で章タイトルを付けて書いてください。2文ごとに改行を入れてわかりやすくしてください。\n"
            "「です・ます」調で、共感や具体例も交えてください。プロンプト例が必要な場合はそれも例として文章に含めてください。\n"
            "・リズムを付けるため極端に長い文を避け、句点で適度に分割。\n"
            "- 想定読者（ペルソナ）：{{今からAIを使い始める幅広い年代層。置いていかれてるかもしれないという不安のあるひとたち}}\n"
            "- 記事の目的（CV）:{{アフィリエイト広告収入}} \n"
            "・テンプレ的表現（「〜をご存じですか？」「注目されています」など）は避けてください\n"
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

    # 結合
    content = lead_text + "\n" + "\n".join(sections)
    return {
        "title": title,
        "content": content
    }


def generate_image_prompt(article_body: str) -> str:
    """
    記事本文HTMLから英語の画像生成プロンプトを作成
    """
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたは画像プロンプト作成のエキスパートです。"
                    "以下のHTML形式の記事に合った画像を生成するには"
                    "どんな英語プロンプトが良いか1文だけで答えてください。"
                    "カラフルなのはやめてください。目を引くようでありかつシンプルなカラーリングで"
                )
            },
            {"role": "user", "content": article_body}
        ],
        temperature=0.7,
        max_tokens=500
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


if __name__ == "__main__":
    keyword = get_next_keyword(col=0)  # A列からキーワードを取得
    prompt = f"{keyword}についての記事を書いてください。SEOを意識して、検索ユーザーのニーズに応える内容にしてください。"
    print("★今回のプロンプト:", prompt)
    print(generate_title_variants(prompt, n=3))
    article = generate_article_html(prompt)
    print(article)

