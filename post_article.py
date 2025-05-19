# 1. モジュールと関数読み込み
import os, requests, random, re, json
from dotenv import load_dotenv
from io import BytesIO
from bs4 import BeautifulSoup
from generate_article import (
    generate_article_html,          # ← ★ 関数名を合わせる
    generate_title_variants,
    generate_image_prompt,
    generate_image_url
)

# 2. 環境変数
load_dotenv()
WP_URL      = os.getenv("WP_URL").rstrip("/")
WP_USER     = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")

# 3. 画像アップロード関数（URLも返す）
def upload_image_to_wp(image_url: str) -> tuple[int, str]:
    img_data = requests.get(image_url).content
    filename = os.path.basename(image_url.split("?")[0]) or "img.jpg"
    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/media",
        auth=(WP_USER, WP_APP_PASS),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        files={"file": (filename, img_data, "image/jpeg")}
    )
    resp.raise_for_status()
    j = resp.json()
    return j["id"], j["source_url"]

# 4. h2直下に画像を挿入
def insert_images_to_html(html: str, max_imgs: int = 6) -> tuple[str, list[int]]:
    soup = BeautifulSoup(html, "html.parser")
    media_ids = []

    for h2_tag, _ in zip(soup.find_all("h2"), range(max_imgs)):
        heading_text = h2_tag.get_text()

        # 1) 見出しから画像プロンプト
        img_prompt = generate_image_prompt(
            f"Illustration or photograph representing: {heading_text}"
        )

        # 2) 画像URL生成
        img_url = generate_image_url(img_prompt)

        # 3) WPにアップロード
        m_id, wp_src = upload_image_to_wp(img_url)
        media_ids.append(m_id)

        # 4) <img> を h2 直後に挿入
        img_tag = soup.new_tag("img", src=wp_src, loading="lazy")
        h2_tag.insert_after(img_tag)

    return str(soup), media_ids

# 5. 投稿関数
def post_to_wp(title: str, content: str, featured_id: int | None) -> dict:
    data = {
        "title": title,
        "content": content,
        "status": "draft",
        "featured_media": featured_id or 0
    }
    r = requests.post(
        f"{WP_URL}/wp-json/wp/v2/posts",
        auth=(WP_USER, WP_APP_PASS),
        json=data
    )
    r.raise_for_status()
    return r.json()

# 6. 実行(main)
if __name__ == "__main__":
    prompt = "AI初心者に生成AIを紹介する記事を書いてください"

    # (a) 記事本文＋タイトル生成
    article = generate_article_html(prompt)

    # (b) 本文に画像6枚を埋め込み
    updated_html, media_ids = insert_images_to_html(article["content"], max_imgs=6)
    article["content"] = updated_html
    featured_id = media_ids[0] if media_ids else None

    # (c) 投稿
    res = post_to_wp(article["title"], article["content"], featured_id)
    print("✅ 投稿完了！URL:", res["link"])

