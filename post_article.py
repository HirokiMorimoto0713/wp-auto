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
    get_next_keyword_group,
    generate_integrated_article_from_keywords,
    generate_meta_description,
    generate_seo_tags,
    generate_seo_slug,
    extract_article_structure,
    generate_article_from_reference,
    extract_multiple_article_structures,
    generate_article_from_multiple_references,
    extract_style_features_from_sources,
    generate_article_with_style_guide,
    generate_keyword_article_with_style
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

        try:
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
            print(f"✅ 見出し「{heading_text}」に画像を挿入しました")

        except Exception as e:
            print(f"⚠️ 見出し「{heading_text}」の画像生成/アップロードに失敗: {e}")
            print("📝 画像なしで記事作成を続行します")
            continue

    return str(soup), media_ids

# WordPressカテゴリ作成・取得関数
def get_or_create_categories(main_category: str, sub_category: str = "") -> list[int]:
    """
    メインカテゴリとサブカテゴリからWordPressカテゴリIDのリストを取得
    階層構造（親子関係）で作成・管理
    """
    category_ids = []
    
    if not main_category:
        return category_ids
    
    # メインカテゴリ（親カテゴリ）の処理
    main_category_id = get_or_create_single_category(main_category)
    if main_category_id:
        category_ids.append(main_category_id)
        print(f"メインカテゴリ設定: {main_category} (ID: {main_category_id})")
    
    # サブカテゴリ（子カテゴリ）の処理
    if sub_category and main_category_id:
        sub_category_id = get_or_create_single_category(sub_category, parent_id=main_category_id)
        if sub_category_id:
            category_ids.append(sub_category_id)
            print(f"サブカテゴリ設定: {sub_category} (ID: {sub_category_id}, 親: {main_category})")
    
    return category_ids

def get_or_create_single_category(category_name: str, parent_id: int = 0) -> int:
    """
    単一カテゴリを取得または作成
    """
    try:
        # 既存カテゴリを検索
        search_resp = requests.get(
            f"{WP_URL}/wp-json/wp/v2/categories",
            auth=(WP_USER, WP_APP_PASS),
            params={
                "search": category_name,
                "parent": parent_id  # 親カテゴリ指定
            }
        )
        
        if search_resp.status_code == 200:
            existing_categories = search_resp.json()
            # 完全一致するカテゴリがあるかチェック
            found_category = next(
                (cat for cat in existing_categories 
                 if cat["name"] == category_name and cat["parent"] == parent_id), 
                None
            )
            
            if found_category:
                return found_category["id"]
            else:
                # カテゴリを新規作成
                create_data = {
                    "name": category_name,
                    "parent": parent_id
                }
                create_resp = requests.post(
                    f"{WP_URL}/wp-json/wp/v2/categories",
                    auth=(WP_USER, WP_APP_PASS),
                    json=create_data
                )
                if create_resp.status_code == 201:
                    new_category = create_resp.json()
                    parent_text = f" (親: {parent_id})" if parent_id > 0 else ""
                    print(f"新規カテゴリ作成: {category_name}{parent_text} (ID: {new_category['id']})")
                    return new_category["id"]
                else:
                    print(f"カテゴリ作成失敗: {category_name} - {create_resp.text}")
                    return 0
        else:
            print(f"カテゴリ検索失敗: {category_name}")
            return 0
            
    except Exception as e:
        print(f"カテゴリ処理エラー: {category_name} - {e}")
        return 0

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
def post_to_wp(title: str, content: str, meta_description: str, slug: str, tag_ids: list[int], category_ids: list[int], featured_id: int | None) -> dict:
    data = {
        "title": title,
        "content": content,
        "slug": slug,  # SEOスラッグ
        "status": "draft",
        "featured_media": featured_id or 0,
        "tags": tag_ids,
        "categories": category_ids,  # カテゴリIDリスト
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

def main():
    """
    メイン処理
    記事生成から投稿まで実行
    """
    try:
        print("=== デバッグ: main開始 ===")
        
        # 参考記事設定を確認
        reference_mode = os.getenv('REFERENCE_MODE', 'integrated_keywords')  # integrated_keywords, keywords, url, file, multiple, style_with_keywords
        print(f"参考記事モード: {reference_mode}")
        
        if reference_mode == 'integrated_keywords':
            # 🆕 新しいCSVファイルを使用した統合キーワードモード
            print("🎯 統合キーワードモード: 新しいCSVファイルを使用")
            
            # キーワードグループを取得
            keyword_group = get_next_keyword_group()
            
            print(f"📝 取得したキーワードグループ:")
            print(f"   グループID: {keyword_group['group_id']}")
            print(f"   キーワード: {', '.join(keyword_group['keywords'])}")
            print(f"   メインカテゴリ: {keyword_group['main_category']}")
            print(f"   サブカテゴリ: {keyword_group['sub_category']}")
            
            # スタイル特徴抽出の設定確認
            reference_urls = os.getenv('REFERENCE_URLS', '').split(',') if os.getenv('REFERENCE_URLS') else []
            reference_files = os.getenv('REFERENCE_FILES', '').split(',') if os.getenv('REFERENCE_FILES') else []
            
            # URLとファイルを統合
            all_sources = []
            if reference_urls and reference_urls != ['']:
                all_sources.extend([url.strip() for url in reference_urls if url.strip()])
            if reference_files and reference_files != ['']:
                all_sources.extend([file.strip() for file in reference_files if file.strip() and os.path.exists(file.strip())])
            
            style_features = None
            if all_sources:
                print(f"🎨 スタイル参考ソース: {len(all_sources)}つ")
                # スタイル特徴を抽出
                style_features = extract_style_features_from_sources(all_sources)
                if "error" not in style_features:
                    print(f"✨ スタイル特徴抽出完了")
                    print(f"📈 見出し絵文字率: {style_features.get('emoji_in_headings_ratio', 0)*100:.0f}%")
                    print(f"📝 文体: {style_features.get('tone', 'polite')}")
                else:
                    print(f"⚠️ スタイル抽出エラー: {style_features['error']}")
                    style_features = None
            
            # 統合記事生成
            article = generate_integrated_article_from_keywords(keyword_group, style_features)
            
            prompt = f"{keyword_group['primary_keyword']}関連記事"  # SEO関連の生成用
            
        elif reference_mode == 'style_with_keywords':
            # 🆕 スタイル参考 + キーワードベース モード
            reference_urls = os.getenv('REFERENCE_URLS', '').split(',') if os.getenv('REFERENCE_URLS') else []
            reference_files = os.getenv('REFERENCE_FILES', '').split(',') if os.getenv('REFERENCE_FILES') else []
            
            # URLとファイルを統合
            all_sources = []
            if reference_urls and reference_urls != ['']:
                all_sources.extend([url.strip() for url in reference_urls if url.strip()])
            if reference_files and reference_files != ['']:
                all_sources.extend([file.strip() for file in reference_files if file.strip() and os.path.exists(file.strip())])
            
            if not all_sources:
                print("エラー: REFERENCE_URLsまたはREFERENCE_FILESが設定されていません")
                exit(1)
            
            print(f"🎨 スタイル参考 + キーワードベース モード: {len(all_sources)}つのスタイル参考ソース")
            for i, source in enumerate(all_sources, 1):
                print(f"  {i}. {source}")
            
            # キーワードを取得
            keyword = get_next_keyword(col=0)
            print(f"📝 取得したキーワード: {keyword}")
            prompt = f"{keyword}についての記事を書いてください。SEOを意識して、検索ユーザーのニーズに応える内容にしてください。"
            print(f"★今回のプロンプト: {prompt}")
            
            # スタイル特徴を抽出
            print("🎨 参考記事からスタイル特徴を抽出中...")
            style_features = extract_style_features_from_sources(all_sources)
            
            if "error" in style_features:
                print(f"⚠️ スタイル抽出エラー、通常キーワードモードで継続: {style_features['error']}")
                article = generate_article_html(prompt)
            else:
                print(f"✨ スタイル特徴統合完了")
                print(f"📈 見出し絵文字率: {style_features.get('emoji_in_headings_ratio', 0)*100:.0f}%")
                print(f"📝 文体: {style_features.get('tone', 'polite')}")
                
                # キーワードベース + スタイルガイド記事生成
                article = generate_keyword_article_with_style(keyword, style_features)
                
        elif reference_mode == 'multiple':
            # 複数参考記事モード
            reference_urls = os.getenv('REFERENCE_URLS', '').split(',') if os.getenv('REFERENCE_URLS') else []
            reference_files = os.getenv('REFERENCE_FILES', '').split(',') if os.getenv('REFERENCE_FILES') else []
            
            # URLとファイルを統合
            all_sources = []
            if reference_urls and reference_urls != ['']:
                all_sources.extend([url.strip() for url in reference_urls if url.strip()])
            if reference_files and reference_files != ['']:
                all_sources.extend([file.strip() for file in reference_files if file.strip() and os.path.exists(file.strip())])
            
            if not all_sources:
                print("エラー: REFERENCE_URLsまたはREFERENCE_FILESが設定されていません")
                exit(1)
                
            print(f"📚 複数参考記事モード: {len(all_sources)}つのソース")
            for i, source in enumerate(all_sources, 1):
                print(f"  {i}. {source}")
            
            # 複数記事から構造抽出・統合
            integrated_structure = extract_multiple_article_structures(all_sources)
            
            if "error" in integrated_structure:
                print(f"参考記事統合エラー: {integrated_structure['error']}")
                exit(1)
                
            print(f"✅ {integrated_structure['source_count']}つのソースから統合完了")
            print(f"📊 統合セクション数: {integrated_structure['total_sections']}")
            
            # 記事テーマを環境変数から取得
            article_theme = os.getenv('ARTICLE_THEME', 'AI活用術')
            print(f"記事テーマ: {article_theme}")
            
            # スタイルガイド使用フラグをチェック
            use_style_guide = os.getenv('USE_STYLE_GUIDE', 'true').lower() == 'true'
            
            if use_style_guide:
                print("🎨 スタイルガイド機能を使用します")
                # スタイル特徴を抽出
                style_features = extract_style_features_from_sources(all_sources)
                
                if "error" in style_features:
                    print(f"⚠️ スタイル抽出エラー、通常モードで継続: {style_features['error']}")
                    article = generate_article_from_multiple_references(article_theme, integrated_structure)
                else:
                    print(f"✨ スタイル特徴統合完了")
                    print(f"📈 見出し絵文字率: {style_features.get('emoji_in_headings_ratio', 0)*100:.0f}%")
                    print(f"📝 文体: {style_features.get('tone', 'polite')}")
                    
                    # スタイルガイド付き記事生成
                    article = generate_article_with_style_guide(article_theme, integrated_structure, style_features)
            else:
                print("📝 通常の複数参考記事統合モードを使用します")
                # 複数参考記事を基に記事生成
                article = generate_article_from_multiple_references(article_theme, integrated_structure)
            
            prompt = article_theme  # SEO関連の生成用
            
        elif reference_mode == 'url':
            # 単一URL参考記事モード
            reference_url = os.getenv('REFERENCE_URL')
            if not reference_url:
                print("エラー: REFERENCE_URLが設定されていません")
                exit(1)
                
            print(f"参考記事URL: {reference_url}")
            reference_structure = extract_article_structure(reference_url, "url")
            
            if "error" in reference_structure:
                print(f"参考記事取得エラー: {reference_structure['error']}")
                exit(1)
                
            # 記事テーマを環境変数から取得
            article_theme = os.getenv('ARTICLE_THEME', 'AI活用術')
            print(f"記事テーマ: {article_theme}")
            
            # 参考記事を基に記事生成
            article = generate_article_from_reference(article_theme, reference_structure)
            prompt = article_theme  # SEO関連の生成用
            
        elif reference_mode == 'file':
            # 単一ファイル参考記事モード
            reference_file = os.getenv('REFERENCE_FILE')
            if not reference_file or not os.path.exists(reference_file):
                print("エラー: REFERENCE_FILEが設定されていないか、ファイルが存在しません")
                exit(1)
                
            print(f"参考記事ファイル: {reference_file}")
            
            # ファイル拡張子で判定
            if reference_file.endswith('.md'):
                with open(reference_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                reference_structure = extract_article_structure(content, "markdown")
            else:
                with open(reference_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                reference_structure = extract_article_structure(content, "html")
                
            if "error" in reference_structure:
                print(f"参考記事解析エラー: {reference_structure['error']}")
                exit(1)
                
            # 記事テーマを環境変数から取得
            article_theme = os.getenv('ARTICLE_THEME', 'AI活用術')
            print(f"記事テーマ: {article_theme}")
            
            # 参考記事を基に記事生成
            article = generate_article_from_reference(article_theme, reference_structure)
            prompt = article_theme  # SEO関連の生成用
            
        else:
            # 従来のキーワードベース記事生成
            keyword = get_next_keyword(col=0)
            print("取得したキーワード:", keyword)
            prompt = f"{keyword}についての記事を書いてください。SEOを意識して、検索ユーザーのニーズに応える内容にしてください。"
            print("★今回のプロンプト:", prompt)
            
            # (a) 記事本文＋タイトル生成
            article = generate_article_html(prompt)
            
        if "error" in article:
            print(f"記事生成エラー: {article['error']}")
            exit(1)

        print("生成されたタイトル:", article.get("title"))
        print("生成された記事冒頭:", article.get("content", "")[:100])

        # 複数参考記事の場合の特別なメタ情報表示
        if article.get('keyword_based') and article.get('style_guided'):
            print(f"🎨 キーワード×スタイルガイド記事生成完了！")
            print(f"📝 キーワード: {article.get('keyword')}")
            print(f"🎯 スタイル参考数: {len(article.get('style_features', {}).get('sources', []))}")
        elif article.get('style_guided'):
            print(f"�� スタイルガイド付き記事生成完了！")
            print(f"📊 統合スタイル特徴数: {len(article.get('style_features', {}).get('sources', []))}")
        elif article.get('multiple_references'):
            print(f"🔗 複数参考記事使用: {article.get('source_count')}つのソースから統合")

        # (a-2) meta description生成
        if article.get('keyword_based') and article.get('style_guided'):
            # キーワード×スタイルガイド使用時は専用プロンプト
            meta_desc = generate_meta_description(f"{article['title']} - {article.get('keyword')}の最適化ガイド（スタイル統合）", article["content"])
        elif article.get('style_guided'):
            # スタイルガイド使用時は専用プロンプト
            meta_desc = generate_meta_description(f"{article['title']} - {article.get('source_count')}つの記事のスタイルを統合した最適化ガイド", article["content"])
        elif article.get('multiple_references'):
            # 複数参考記事使用時は専用プロンプト
            meta_desc = generate_meta_description(f"{article['title']} - {article.get('source_count')}つの記事を統合した包括的ガイド", article["content"])
        elif article.get('reference_used'):
            # 単一参考記事使用時は専用プロンプト
            meta_desc = generate_meta_description(f"{article['title']} - 参考記事を基にした詳細解説", article["content"])
        else:
            meta_desc = generate_meta_description(prompt, article["content"])
        print("生成されたmeta description:", meta_desc)

        # (a-3) SEOタグ生成
        if article.get('keyword_based') and article.get('style_guided'):
            # キーワード×スタイルガイド使用時は専用プロンプト
            seo_tags = generate_seo_tags(f"{article['title']} - {article.get('keyword')} スタイル最適化記事", article["content"])
        elif article.get('style_guided'):
            # スタイルガイド使用時は専用プロンプト
            seo_tags = generate_seo_tags(f"{article['title']} - スタイル統合による最適化記事", article["content"])
        elif article.get('multiple_references'):
            # 複数参考記事使用時は専用プロンプト
            seo_tags = generate_seo_tags(f"{article['title']} - 複数ソースを統合した包括的解説", article["content"])
        else:
            seo_tags = generate_seo_tags(prompt, article["content"])
        print("生成されたSEOタグ:", seo_tags)
        tag_ids = get_or_create_tags(seo_tags)
        print("WordPressタグID:", tag_ids)

        # (a-4) カテゴリ設定（統合キーワードモードの場合）
        category_ids = []
        if reference_mode == 'integrated_keywords' and 'main_category' in article:
            category_ids = get_or_create_categories(
                article.get('main_category', ''),
                article.get('sub_category', '')
            )
            print("WordPressカテゴリID:", category_ids)

        # (a-5) SEOスラッグ生成
        seo_slug = generate_seo_slug(prompt, article["title"])
        print("生成されたSEOスラッグ:", seo_slug)

        # (b) 本文に画像6枚を埋め込み（リサイズ機能付き）
        # 画像生成設定を確認
        enable_images = os.getenv('ENABLE_IMAGE_GENERATION', 'true').lower() == 'true'
        
        if enable_images:
            # 参考記事使用時は異なる画像プロンプト
            if article.get('multiple_references'):
                print("📸 複数参考記事ベースの画像生成を実行中...")
            elif article.get('reference_used'):
                print("📸 参考記事ベースの画像生成を実行中...")
            else:
                print("📸 画像生成を実行中...")
            
            updated_html, media_ids = insert_images_to_html(article["content"], max_imgs=6)
            article["content"] = updated_html
            featured_id = media_ids[0] if media_ids else None
        else:
            print("📝 画像生成を無効化しています（ENABLE_IMAGE_GENERATION=false）")
            media_ids = []
            featured_id = None

        # (c) 投稿
        res = post_to_wp(article["title"], article["content"], meta_desc, seo_slug, tag_ids, category_ids, featured_id)
        
        # 投稿完了メッセージ
        if article.get('keyword_based') and article.get('style_guided'):
            print(f"✅ キーワード×スタイルガイド記事投稿完了！")
            print(f"📝 キーワード: {article.get('keyword')}")
        elif article.get('style_guided'):
            print(f"✅ スタイルガイド統合記事投稿完了！（{article.get('source_count')}ソース統合）")
        elif article.get('multiple_references'):
            print(f"✅ 複数参考記事統合投稿完了！（{article.get('source_count')}ソース統合）")
        else:
            print("✅ 投稿完了！")
        print(f"URL: {res['link']}")

        # デバッグ情報を出力
        if article.get('style_guided') and os.getenv('DEBUG_STYLE', 'false').lower() == 'true':
            print("\n--- 生成されたスタイルガイド ---")
            print(article.get('style_yaml', ''))

    except Exception as e:
        print("記事生成で例外:", e)
        import traceback
        traceback.print_exc()
        exit(1)

# 6. 実行(main)
if __name__ == "__main__":
    import sys
    
    # コマンドライン引数で参考記事ファイルが指定された場合
    if len(sys.argv) > 1:
        reference_files = [arg for arg in sys.argv[1:] if os.path.exists(arg)]
        
        if reference_files:
            print(f"🎯 コマンドライン引数で参考記事が指定されました: {len(reference_files)}個")
            
            # 環境変数を動的に設定
            if len(reference_files) == 1:
                # 単一ファイル＋キーワードモード
                os.environ['REFERENCE_MODE'] = 'style_with_keywords'  
                os.environ['REFERENCE_FILES'] = reference_files[0]
                print(f"📝 キーワード×スタイルガイドモード: {reference_files[0]}")
            else:
                # 複数ファイル＋キーワードモード
                os.environ['REFERENCE_MODE'] = 'style_with_keywords'
                os.environ['REFERENCE_FILES'] = ','.join(reference_files)
                print(f"📚 キーワード×複数スタイルガイドモード: {len(reference_files)}個のファイル使用")
                
            # 画像生成を一時的に無効化
            os.environ['ENABLE_IMAGE_GENERATION'] = 'false'
            print("⚠️ 参考記事モードのため画像生成を無効化しました")
        else:
            print("⚠️ 指定されたファイルが存在しません")
    
    main()

