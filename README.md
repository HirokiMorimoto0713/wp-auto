# WordPress自動記事投稿システム

ChatGPTとDALL-E 3を使用したWordPress記事の完全自動生成・投稿システム

## 機能

### 🤖 AI記事生成
- ChatGPT 4oによる高品質な記事生成
- SEO最適化されたタイトル自動生成
- 読者に響くリード文（250文字程度）
- 章立て構成（h2タグ5つ）

### 🎨 画像自動生成・挿入
- DALL-E 3による各章のイメージ画像生成
- 自動リサイズ・圧縮機能
- h2タグ直下への画像自動挿入

### 📊 SEO最適化
- meta description自動生成（150文字以内）
- SEOタグ自動生成・設定（3つ）
- 英語スラッグ自動生成
- キーワード最適化

### ⏰ 自動スケジュール実行
- Cronによる定期実行（8時、12時、18時）
- CSVキーワードリストからの順次取得
- 投稿状況のログ記録

## セットアップ

### 1. 環境設定

```bash
# 仮想環境作成
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 依存関係インストール
pip install openai requests python-dotenv beautifulsoup4 Pillow
```

### 2. 環境変数設定

`.env`ファイルを作成：

```env
OPENAI_API_KEY=your_openai_api_key
WP_URL=https://your-wordpress-site.com
WP_USER=your_wp_username
WP_APP_PASS=your_wp_app_password
```

### 3. キーワードリスト準備

`keywords.csv`ファイルを作成：

```csv
キーワード
ChatGPT 使い方
AI 画像生成
プログラミング 入門
```

### 4. WordPress設定

- REST API有効化
- アプリケーションパスワード生成
- 適切なユーザー権限設定

## 使用方法

### 手動実行
```bash
python post_article.py
```

### 自動実行設定
```bash
# cron設定
crontab -e

# 以下を追加
0 8,12,18 * * * cd /path/to/wp-auto && .venv/bin/python post_article.py >> logs/cron.log 2>&1
```

## ファイル構成

```
wp-auto/
├── generate_article.py    # 記事生成メイン関数
├── post_article.py        # 投稿実行スクリプト
├── keywords.csv          # キーワードリスト
├── .env                  # 環境変数（要作成）
├── last_index.txt        # 最後のキーワードインデックス
└── logs/                 # ログディレクトリ
    └── cron.log
```

## 出力例

```
=== デバッグ: main開始 ===
取得したキーワード: ChatGPT 使い方
★今回のプロンプト: ChatGPT 使い方についての記事を...
生成されたタイトル: もう迷わない。初心者でもできるChatGPTの始め方
生成されたmeta description: ChatGPT初心者向けガイド...
生成されたSEOタグ: ['ChatGPT', 'AI活用', '初心者向け']
生成されたSEOスラッグ: chatgpt-beginner-guide
✅ 投稿完了！URL: https://yoursite.com/chatgpt-beginner-guide/
```

## 注意事項

- OpenAI API使用料が発生します
- WordPress REST APIが有効である必要があります
- サーバーのタイムゾーン設定を確認してください

## ライセンス

MIT License

## 開発者

- 記事生成: ChatGPT 4o
- 画像生成: DALL-E 3
- WordPress連携: REST API 
