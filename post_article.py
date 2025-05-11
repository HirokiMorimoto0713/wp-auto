import os
import requests
from dotenv import load_dotenv
from generate_article import (
    generate_article_html,
    generate_image_prompt,
    generate_image_url
)
from io import BytesIO

# .env から WP の情報を読み込む
load_dotenv()
WP_URL      = os.getenv("WP_URL").rstrip("/")
WP_USER     = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")

def upload_image_to_wp(image_url: str) -> int:
    """
    画像URLをダウンロードし、WPメディアにアップロードしてIDを返す
    """
    img = requests.get(image_url).content
    filename = "featured.jpg"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/media",
        auth=(WP_USER, WP_APP_PASS),
        headers=headers,
        files={"file": (filename, BytesIO(img), "image/jpeg")}
    )
    resp.raise_for_status()
    return resp.json()["id"]

def post_to_wp(title: str, html_content: str, image_id: int) -> dict:
    """
    タイトル／HTML本文／アイキャッチ画像IDを使ってWPに投稿
    """
    data = {
        "title":          title,
        "content":        html_content,
        "status":         "publish",       # draftなら"draft"
        "featured_media": image_id
    }
    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/posts",
        auth=(WP_USER, WP_APP_PASS),
        json=data
    )
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    # 投稿したいテーマをここで記述
    prompt = "夏に東京近郊で楽しめる日帰り温泉スポットを5つ紹介する記事を書いてください"

    # 1) タイトル＆HTML生成
    article = generate_article_html(prompt)

    # 2) 画像プロンプト＆URL取得
    img_prompt = generate_image_prompt(article["content"])
    img_url    = generate_image_url(img_prompt)

    # 3) WP に画像アップロード→ID取得
    img_id = upload_image_to_wp(img_url)

    # 4) 記事投稿（自動生成タイトルをそのまま使う）
    res = post_to_wp(article["title"], article["content"], img_id)
    print("✅ 完了！記事URL:", res.get("link"))

