import os
import requests
import random
from dotenv import load_dotenv
from io import BytesIO
from generate_article import (
    generate_title_variants,
    generate_article_html,
    generate_image_prompt,
    generate_image_url
)

# .env から WP の情報を読み込む
load_dotenv()
WP_URL      = os.getenv("WP_URL").rstrip("/")    # 例: https://your-site.com
WP_USER     = os.getenv("WP_USER")               # WPログインユーザー名
WP_APP_PASS = os.getenv("WP_APP_PASS")           # アプリケーションパスワード

def upload_image_to_wp(image_url: str) -> int:
    """
    画像URLをダウンロードし、WPメディアにアップロードしてIDを返す
    """
    img_data = requests.get(image_url).content
    filename = "featured.jpg"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/media",
        auth=(WP_USER, WP_APP_PASS),
        headers=headers,
        files={"file": (filename, BytesIO(img_data), "image/jpeg")}
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
    prompt = "今からAIを使い始める人に向けて、生成AIとは何か、何が便利なのか、無料で使えるのか、をわかりやすく解説してください"

    # 1) タイトル案生成＆ログ出力
    variants = generate_title_variants(prompt, n=8)
    print("🔍 タイトル候補一覧:")
    for idx, t in enumerate(variants, start=1):
        print(f"  {idx}. {t}")
    print("───────────────────────────\n")

    # 2) ランダムに1つ選択
    chosen_title = random.choice(variants)
    print(f"🔖 選ばれたタイトル: {chosen_title}")

    # 3) 本文（HTML）を生成
    article = generate_article_html(prompt)
    article["title"] = chosen_title

    # 4) 画像プロンプト＆URL取得
    img_prompt = generate_image_prompt(article["content"])
    img_url    = generate_image_url(img_prompt)

    # 5) 画像アップロード→ID取得
    img_id = upload_image_to_wp(img_url)

    # 6) 記事投稿
    res = post_to_wp(article["title"], article["content"], img_id)
    print("✅ 投稿完了！記事URL:", res.get("link"))

