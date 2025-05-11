import os
import requests
from dotenv import load_dotenv
# 新：HTML付き記事生成関数をインポート
from generate_article import (
    generate_article_html,
    generate_image_prompt,
    generate_image_url
)
from io import BytesIO

# .env から読み込む
load_dotenv()
WP_URL      = os.getenv("WP_URL").rstrip("/")
WP_USER     = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")

# 画像アップロード
def upload_image_to_wp(image_url: str) -> int:
    img_data = requests.get(image_url).content
    filename = "featured.jpg"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/media",
        auth=(WP_USER, WP_APP_PASS),
        headers=headers,
        files={"file": (filename, BytesIO(img_data), "image/jpeg")}
    )
    resp.raise_for_status()
    return resp.json()["id"]

# 記事投稿（画像IDを受け取る）
def post_to_wp(title: str, content: str, image_id: int) -> dict:
    data = {
        "title": title,
        "content": content,
        "status": "draft",           # 下書き → 確認後に "publish" へ
        "featured_media": image_id   # ここでアイキャッチ設定
    }
    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/posts",
        auth=(WP_USER, WP_APP_PASS),
        json=data
    )
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    prompt = "春におすすめの東京のカフェを5つ紹介する記事を書いてください"

    # 1. HTML付き本文生成
    article = generate_article_html(prompt)

    # 2. 画像生成プロンプト作成
    image_prompt = generate_image_prompt(article["content"])

    # 3. 画像URL取得
    image_url = generate_image_url(image_prompt)

    # 4. WPに画像アップロード → ID取得
    image_id = upload_image_to_wp(image_url)

    # 5. WPに記事投稿（画像IDを渡す）
    res = post_to_wp(article["title"], article["content"], image_id)
    print("✅ 投稿完了！記事URL:", res.get("link"))

