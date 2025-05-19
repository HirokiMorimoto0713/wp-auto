import os
import openai
import json
import re
from dotenv import load_dotenv

# .env から APIキーを読み込む
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_title_variants(prompt: str, n: int = 5) -> list[str]:
    """
    テーマ(prompt)に合う日本語タイトル案をn個返す
    """
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"この記事のタイトルを日本語で創造的に{n}案、箇条書きで出してください。冒頭にナンバリングや記号の類は必要ありません"
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=300
    )
    lines = resp.choices[0].message.content.splitlines()
    variants = [line.strip("• ") for line in lines if line.strip()]
    return variants


def generate_article_html(prompt: str) -> dict:
    """
    AI に「タイトルとHTML形式本文」をJSONで返してもらい、
    JSON 部分だけを抜き出して返す。
    戻り値: {'title': str, 'content': str(html)}
    """
    system_msg = (
    # ─────────【絶対条件】─────────
    "あなたはSEO向け長文ライターです。\n"
    "本文は必ず日本語で3000文字以上、絶対に3000文字未満で終わらせないでください。"
    "もし3000文字未満の場合は「ERROR: 文字数不足」とだけ出力してください。\n"
    "冒頭リード文300文字、その後<h2>章立てを複数。"
    "読みやすいように積極的に改行を使ってください。\n"
    "本文に<h1>タグは使わず、最上位は<h2>。必要なら<h3>以降。\n"
    "JSONのみで返す →  {\"title\":\"…\",\"content\":\"…\"}\n"
    # ─────────【その他の条件】─────────
    "・リズムを付けるため極端に長い文を避け、句点で適度に分割。\n"
    "- 想定読者（ペルソナ）：{{今からAIを使い始める幅広い年代層。置いていかれてるかもしれないという不安のあるひとたち}}"
    "- 記事の目的（CV）:{{アフィリエイト広告収入}} " 
    "・ 共感：情報提示 : 3:7〜4:6 程度にしてください"
    "・ 読者が「これは自分の状況かも」と思えるよう、行動や状況の具体例を挟んでください"
    "・テンプレ的表現（「〜をご存じですか？」「注目されています」など）は避けてください"
    "・「です」「ます」調を守ってください。"
    )

    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.7,
        max_tokens=8000      # 日本語3000字を生成するために十分なトークン数を確保
    )

    text = resp.choices[0].message.content.strip()

    # ────── 生テキスト確認（デバッグ） ──────
    #print("── AI Raw Text ──")
    #print(text)
    #print("─────────────────\n")

# ───────── フォールバック付き JSON 抜き出し ─────────

    # 1) まず「先頭が { かつ 末尾が } 」なら全体を JSON とみなす
    if text.startswith("{") and text.endswith("}"):
        json_text = text
    else:
        # 2) それ以外は、本文中の最初の {…} 部分だけを抜き出す
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise ValueError(f"JSON 部分が見つかりませんでした:\n{text}")
        json_text = m.group(0)

    data = json.loads(json_text)

    return {
        "title": data["title"],
        "content": data["content"]
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
        size="1024x1024",
        n=1
    )
    return response.data[0].url


if __name__ == "__main__":
    # テスト用
    prompt = "春におすすめの東京のカフェを5つ紹介する記事を書いてください"
    print(generate_title_variants(prompt, n=3))
    article = generate_article_html(prompt)
    print(article)
