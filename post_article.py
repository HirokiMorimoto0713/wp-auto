# 1. モジュールと関数読み込み
import os, requests, random, re, json
from dotenv import load_dotenv
from io import BytesIO
from bs4 import BeautifulSoup
from generate_article import (
    generate_article_html,          
    generate_title_variants,
    generate_image_prompt,
    generate_image_url,
    get_next_keyword,
    generate_meta_description,
    generate_seo_tags,
    generate_seo_slug
)

# 2. 環境変数
load_dotenv()
WP_URL      = os.getenv("WP_URL").rstrip("/")
WP_USER     = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")

# 3. 画像アップロード関数（改良版：リサイズ・エラーハンドリング付き）
def upload_image_to_wp(image_url: str) -> tuple[int, str]:
    print("アップロード画像URL:", image_url)
    
    try:
        # 画像を取得
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()
        original_data = img_response.content
        print("元画像サイズ:", len(original_data), "bytes")
        
        # 画像サイズが大きい場合はリサイズ
        if len(original_data) > 500 * 1024:  # 500KB以上の場合
            try:
                from PIL import Image
                import io
                
                # 画像を開く
                img = Image.open(io.BytesIO(original_data))
                print("元画像サイズ:", img.size)
                
                # アスペクト比を保持してリサイズ（最大800x600）
                img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                print("リサイズ後:", img.size)
                
                # JPEG形式で圧縮
                img_buffer = io.BytesIO()
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(img_buffer, format='JPEG', quality=85, optimize=True)
                img_data = img_buffer.getvalue()
                print("圧縮後サイズ:", len(img_data), "bytes")
                
                filename = "resized_image.jpg"
                content_type = "image/jpeg"
                
            except ImportError:
                print("Pillowがインストールされていません。元画像を使用します。")
                img_data = original_data
                filename = os.path.basename(image_url.split("?")[0]) or "img.jpg"
                content_type = "image/jpeg"
        else:
            img_data = original_data
            filename = os.path.basename(image_url.split("?")[0]) or "img.jpg"
            content_type = "image/jpeg"
        
        # WordPress にアップロード
        resp = requests.post(
            f"{WP_URL}/wp-json/wp/v2/media",
            auth=(WP_USER, WP_APP_PASS),
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            files={"file": (filename, img_data, content_type)},
            timeout=60
        )
        
        if resp.status_code == 201:
            j = resp.json()
            print(f"画像アップロード成功: {filename}")
            return j["id"], j["source_url"]
        else:
            print(f"画像アップロードエラー: {resp.status_code} - {resp.text}")
            raise requests.exceptions.HTTPError(f"画像アップロード失敗: {resp.status_code}")
            
    except Exception as e:
        print(f"画像アップロード例外: {e}")
        raise

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

# WordPressタグ作成・取得関数
def get_or_create_tags(tag_names: list[str]) -> list[int]:
    """
    タグ名のリストからWordPressタグIDのリストを取得（存在しない場合は作成）
    """
    tag_ids = []
    
    for tag_name in tag_names:
        # 既存タグを検索
        search_resp = requests.get(
            f"{WP_URL}/wp-json/wp/v2/tags",
            auth=(WP_USER, WP_APP_PASS),
            params={"search": tag_name}
        )
        
        if search_resp.status_code == 200:
            existing_tags = search_resp.json()
            # 完全一致するタグがあるかチェック
            found_tag = next((tag for tag in existing_tags if tag["name"] == tag_name), None)
            
            if found_tag:
                tag_ids.append(found_tag["id"])
                print(f"既存タグ使用: {tag_name} (ID: {found_tag['id']})")
            else:
                # タグを新規作成
                create_resp = requests.post(
                    f"{WP_URL}/wp-json/wp/v2/tags",
                    auth=(WP_USER, WP_APP_PASS),
                    json={"name": tag_name}
                )
                if create_resp.status_code == 201:
                    new_tag = create_resp.json()
                    tag_ids.append(new_tag["id"])
                    print(f"新規タグ作成: {tag_name} (ID: {new_tag['id']})")
                else:
                    print(f"タグ作成失敗: {tag_name}")
        else:
            print(f"タグ検索失敗: {tag_name}")
    
    return tag_ids

# 5. 投稿関数
def post_to_wp(title: str, content: str, meta_description: str, slug: str, tag_ids: list[int], featured_id: int | None) -> dict:
    data = {
        "title": title,
        "content": content,
        "slug": slug,  # SEOスラッグ
        "status": "draft",
        "featured_media": featured_id or 0,
        "tags": tag_ids,
        "meta": {
            "meta_description": meta_description,  # 汎用カスタムフィールド
            "seo_description": meta_description    # SEO用カスタムフィールド
        }
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
    print("=== デバッグ: main開始 ===")
    try:
        keyword = get_next_keyword(col=0)
        print("取得したキーワード:", keyword)
        prompt = f"{keyword}についての記事を書いてください。SEOを意識して、検索ユーザーのニーズに応える内容にしてください。"
        print("★今回のプロンプト:", prompt)
    except Exception as e:
        print("get_next_keywordで例外:", e)
        raise

    # (a) 記事本文＋タイトル生成
    article = generate_article_html(prompt)
    print("生成されたタイトル:", article.get("title"))
    print("生成された記事冒頭:", article.get("content", "")[:100])

    # (a-2) meta description生成
    meta_desc = generate_meta_description(prompt, article["content"])
    print("生成されたmeta description:", meta_desc)

    # (a-3) SEOタグ生成
    seo_tags = generate_seo_tags(prompt, article["content"])
    print("生成されたSEOタグ:", seo_tags)
    tag_ids = get_or_create_tags(seo_tags)
    print("WordPressタグID:", tag_ids)

    # (a-4) SEOスラッグ生成
    seo_slug = generate_seo_slug(prompt, article["title"])
    print("生成されたSEOスラッグ:", seo_slug)

    # (b) 本文に画像6枚を埋め込み（リサイズ機能付き）
    updated_html, media_ids = insert_images_to_html(article["content"], max_imgs=6)
    article["content"] = updated_html
    featured_id = media_ids[0] if media_ids else None

    # (c) 投稿
    res = post_to_wp(article["title"], article["content"], meta_desc, seo_slug, tag_ids, featured_id)
    print("✅ 投稿完了！URL:", res["link"])

