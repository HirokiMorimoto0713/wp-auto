import os
import openai
from dotenv import load_dotenv

# .env から読み込む
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_article_html(prompt: str) -> dict:
    """
    ChatGPT に HTML付きのタイトル＋本文を生成させる。
    戻り値: {'title': str, 'content': str(html)}
    """
    system_msg = (
        "あなたはブログ記事生成アシスタントです。"
        "SEOを意識した記事をHTML形式で出力してください。"
        "<h1>タグは使わず、タイトルはプレーンテキストだけ返してください。"
        "本文は<h2>見出し</h2>、<h3>小見出し</h3>、<p>本文</p>の形式で約800字以内で生成してください。"
    )
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.7,
        max_tokens=900
    )
    html = resp.choices[0].message.content.strip()

    # タイトルはプロンプトの冒頭とするか、システムに任せてもOK
    # ここではプロンプトの1行目をそのままタイトルに抜き出します
    title_line = prompt.split("\n")[0]
    return {"title": title_line, "content": html}

def generate_image_prompt(article_body: str) -> str:
    """
    記事本文HTMLから、DALL·E用の英語プロンプトを生成する
    """
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたは画像生成プロンプトの専門家です。"
                    "以下のHTML形式の記事本文に合った画像を1枚生成するとしたら、"
                    "DALL·Eで使えるシンプルかつ具体的な英語プロンプトを1文だけ出力してください。"
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
    DALL·E 3 を使って画像を生成し、そのURLを返す
    """
    response = openai.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        size="1024x1024",
        n=1
    )
    return response.data[0].url

if __name__ == "__main__":
    test_prompt = "春におすすめの東京のカフェを5つ紹介する記事を書いてください"
    article = generate_article_html(test_prompt)
    print("=== Title ===")
    print(article["title"])

