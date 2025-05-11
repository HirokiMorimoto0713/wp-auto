import os
import openai
import json
from dotenv import load_dotenv

# .env から APIキーを読み込む
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_article_html(prompt: str) -> dict:
    """
    AI に「タイトルとHTML形式本文」をJSONで返してもらう。
    戻り値: {'title': str, 'content': str(html)}
    """
    system_msg = (
        "あなたはブログ記事作成のプロフェッショナルです。"
        "SEOを意識した記事の**タイトル**と、<h2>見出し</h2>, <h3>小見出し</h3>,"
        "<p>段落</p> のHTML形式で**本文**を生成してください。"
        "必ず以下のJSONだけを返してください：\n"
        '{"title":"ここに記事タイトル","content":"ここに本文のHTML"}'
    )
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system", "content":system_msg},
            {"role":"user",   "content":prompt}
        ],
        temperature=0.7,
        max_tokens=900
    )
    text = resp.choices[0].message.content.strip()
    data = json.loads(text)
    return {"title": data["title"], "content": data["content"]}

def generate_image_prompt(article_body: str) -> str:
    """
    記事本文HTMLから英語の画像生成プロンプトを作成
    """
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role":"system",
                "content":(
                    "あなたは画像プロンプト作成のエキスパートです。"
                    "以下のHTML形式の記事に合った画像を生成するには"
                    "どんな英語プロンプトが良いか1文だけで答えてください。"
                )
            },
            {"role":"user", "content":article_body}
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

