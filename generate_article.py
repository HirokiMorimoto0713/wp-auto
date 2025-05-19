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
                "content": f"この記事のタイトルを日本語で創造的に{n}案、箇条書きで出してください。'titles' 配列で JSON だけ返してください"
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=300,
        response_format={"type":"json_object"}   

    )
    return json.loads(resp.choices[0].message.content)["titles"]


def generate_article_html(prompt: str, num_sections: int = 5) -> dict:
    # タイトル生成
    title = generate_title_variants(prompt, n=1)[0]

    # リード文生成
    lead_msg = (
        "あなたはSEO向け長文ライターです。\n"
        "この記事のリード文（導入部）を日本語で300文字以上、<h2>や<h3>は使わずに書いてください。\n"
        "「です・ます」調で、共感や具体例も交えてください。\n"
        "・リズムを付けるため極端に長い文を避け、句点で適度に分割。\n"
        "- 想定読者（ペルソナ）：{{今からAIを使い始める幅広い年代層。置いていかれてるかもしれないという不安のあるひとたち}}\n"
        "- 記事の目的（CV）:{{アフィリエイト広告収入}} \n"
        "・ 共感：情報提示 : 3:7〜4:6 程度にしてください\n"
        "・ 読者が「これは自分の状況かも」と思えるよう、行動や状況の具体例を挟んでください\n"
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
            f"この記事の第{i}章を日本語で340文字以上、<h2>で章タイトルを付けて書いてください。\n"
            "「です・ます」調で、共感や具体例も交えてください。\n"
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
    return response.data[0].url


if __name__ == "__main__":
    # テスト用
    prompt = "AI初心者に生成AIを紹介する記事を書いてください"
    print(generate_title_variants(prompt, n=3))
    article = generate_article_html(prompt)
    print(article)
