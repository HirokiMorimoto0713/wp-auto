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
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"この記事のタイトルを日本語で創造的に{n}案、箇条書きで出してください。冒頭にナンバリングや記号の類は必要ありません"
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=150
    )
    lines = resp.choices[0].message.content.splitlines()
    variants = [line.strip("• 　") for line in lines if line.strip()]
    return variants


def generate_article_html(prompt: str) -> dict:
    """
    AI に「タイトルとHTML形式本文」をJSONで返してもらい、
    JSON 部分だけを抜き出して返す。
    戻り値: {'title': str, 'content': str(html)}
    """
    system_msg = (
       "あなたはSEO記事における構成と執筆に長けたプロライターです。"
       "以下の入力情報をもとに、検索ユーザーの共感と関心を自然に引き出しながら、参考記事があればそれに近いトーンで「人間らしい」全文を作成してください。"
       "【入力情報】"
       "- 想定読者（ペルソナ）：{{今からAIを使い始める幅広い年代層。置いていかれてるかもしれないという不安のあるひとたち}}"
       "- 検索意図：{{AIってどうやって使うの？AIって何から始めればいいの？お金はかかるの？}}" 
       "- 記事の目的（CV）：{{アフィリエイト広告収入}} "
       "【出力条件】"
       "・コピーアンドペーストでそのまま記事に使える形でまとめてください" 
       "・ 共感：情報提示 ＝ 3:7〜4:6 程度にしてください"
       "・ 読者が「これは自分の状況かも」と思えるよう、行動や状況の具体例を挟んでください"
       "・情報パートでは「この後の記事に何が書かれているか」を自然に提示してください"
       "・出力結果の一番初めから、記事内容を記載してください"
       "・テンプレ的表現（「〜をご存じですか？」「注目されています」など）は避けてください"
       "・参考記事がある場合は、その構成や言い回し、文章リズムを可能な範囲で踏襲してください"
       "・「です」「ます」調を守ってください。"
       "・冒頭文を300字程度、本文を1000字程度で構成してください"
       "・本文は複数の章立てをしてわかりやすくまとめてください"
       "【文体・トーン】"
       "- トーンは「信頼性があるが押し付けがましくない」"
       "- 読者と同じ立場に立つような自然体の語り口でお願いします"
        "必ず以下のJSONだけを返してください：\n"
        '{"title":"ここに記事タイトル","content":"ここに本文のHTML"}'
    )
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=900
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
    # ────────────────────────────────────────────

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
        max_tokens=100
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

