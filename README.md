# WordPress自動記事投稿システム

ChatGPTとDALL-E 3を使用したWordPress記事の完全自動生成・投稿システム

## 🔗 GitHubリポジトリ

**メインリポジトリ**: [https://github.com/HirokiMorimoto0713/wp-auto](https://github.com/HirokiMorimoto0713/wp-auto)

## 🚀 プロジェクト概要

このシステムは、AI技術を活用してWordPress記事を完全自動で生成・投稿するシステムです。キーワードベースの記事生成から、複数の参考記事を統合したスタイルガイド機能まで、多様な記事生成方法をサポートしています。

## 🆕 新機能：参考記事ベース記事生成

参考記事（HTMLまたはマークダウン）を読み取り、その構造に沿った記事を生成できるようになりました！

### 📝 従来機能
- CSVキーワードベース記事生成
- SEO最適化（メタ記述、タグ、スラッグ）
- DALL-E 3による画像生成・自動挿入
- WordPress REST API連携

### 🆕 参考記事機能
- **URLから記事構造抽出**：Webページの見出し・内容を解析
- **マークダウンファイル対応**：ローカルの.mdファイルから構造抽出
- **構造を活用した記事生成**：参考記事の見出し構成を参考に独自記事を生成
- **SEO要素も参考記事に最適化**：メタ記述・タグ・スラッグも参考記事を考慮

## 🆕 新機能：複数参考記事統合記事生成

**🎯 複数の参考記事を組み合わせて、より多角的で包括的な記事を自動生成！**

### 📝 従来機能
- CSVキーワードベース記事生成
- SEO最適化（メタ記述、タグ、スラッグ）
- DALL-E 3による画像生成・自動挿入
- WordPress REST API連携

### 🆕 参考記事機能
- **単一URLから記事構造抽出**：Webページの見出し・内容を解析
- **単一マークダウンファイル対応**：ローカルの.mdファイルから構造抽出
- **🔥 複数ソース統合**：複数URL・ファイルを組み合わせて統合
- **構造最適化**：類似セクションを自動クラスター化・統合
- **多角的記事生成**：複数視点を融合した包括的コンテンツ
- **SEO要素も統合最適化**：複数ソースを考慮したメタ情報生成

### **🔥 NEW! スタイルガイド機能**
**🎨 複数記事のスタイル特徴を自動抽出・統合して、まったく新しい最適化された文体で記事生成！**

#### **🚀 スタイルガイドのメリット**
1. **📊 自動スタイル分析**: 見出し頻度・絵文字使用率・箇条書き密度を定量化
2. **🎯 文体統合**: 複数記事の語調（です・ます調 vs カジュアル調）を最適ブレンド
3. **⚡ 構造最適化**: 参考記事の構造スタイル（リスト重視 vs 段落重視）を統合
4. **🔍 YAMLガイド生成**: AI可読な形式でスタイル指示を自動生成
5. **💪 一貫性保証**: 複数ソースから一貫した文体ルールを抽出

#### **📈 抽出されるスタイル特徴**
- **見出し頻度**: H2見出しの密度（per 1000語）
- **絵文字使用率**: 見出しでの絵文字使用パターン
- **箇条書き密度**: リスト形式の使用頻度
- **文体判定**: です・ます調 vs カジュアル調の比率
- **文長分析**: 平均センテンス長
- **構造スタイル**: リスト重視 vs 段落重視の判定
- **専門用語率**: 英語・技術用語の使用頻度

### **🚀 複数参考記事のメリット**
1. **📊 多角的な視点**: 異なる記事構造・アプローチを統合
2. **🎯 内容の豊富さ**: 複数ソースから最良の要素を抽出
3. **⚡ 独創性の向上**: 複数要素の融合で独自性アップ
4. **🔍 包括性**: より深い洞察と網羅的な情報

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

### 1. リポジトリのクローン
```bash
git clone https://github.com/HirokiMorimoto0713/wp-auto.git
cd wp-auto
```

### 2. 環境設定

```bash
# 仮想環境作成
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 依存関係インストール
pip install -r requirements.txt
```

### 3. 環境変数設定

`.env`ファイルを作成：

```env
OPENAI_API_KEY=your_openai_api_key
WP_URL=https://your-wordpress-site.com
WP_USER=your_wp_username
WP_APP_PASS=your_wp_app_password
```

### 4. キーワードリスト準備

`keywords.csv`ファイルを作成：

```csv
キーワード
ChatGPT 使い方
AI 画像生成
プログラミング 入門
```

### 5. WordPress設定

- REST API有効化
- アプリケーションパスワード生成
- 適切なユーザー権限設定

## 使用方法

### 1. 従来のキーワードベース生成
```bash
# .envで設定
REFERENCE_MODE=keywords

# 実行
python post_article.py
```

### 2. 参考記事URL指定
```bash
# .envで設定
REFERENCE_MODE=url
REFERENCE_URL=https://example.com/reference-article
ARTICLE_THEME=AI活用術

# 実行
python post_article.py
```

### 3. ローカルファイル指定
```bash
# .envで設定
REFERENCE_MODE=file
REFERENCE_FILE=./reference/sample.md
ARTICLE_THEME=ChatGPT活用法

# 実行
python post_article.py
```

### 4. 🔥 複数参考記事統合生成
```bash
# .envで設定
REFERENCE_MODE=multiple

# 複数URLを指定
REFERENCE_URLS=https://site1.com/article1,https://site2.com/article2,https://site3.com/article3

# または複数ファイルを指定
REFERENCE_FILES=./reference/guide1.md,./reference/guide2.md,./reference/manual.html

# または混合（URL + ファイル）
REFERENCE_URLS=https://example.com/article
REFERENCE_FILES=./reference/local-guide.md

ARTICLE_THEME=AI活用完全ガイド

# 実行
python post_article.py
```

### 5. 🎨 **NEW! スタイルガイド統合生成**
```bash
# .envで設定
REFERENCE_MODE=multiple
USE_STYLE_GUIDE=true

# 複数ソースを指定（URL + ファイル混合可能）
REFERENCE_URLS=https://tech-blog1.com/ai-guide,https://expert-site.com/tutorial
REFERENCE_FILES=./reference/style-sample1.md,./reference/style-sample2.md

ARTICLE_THEME=最新AI活用術

# デバッグ用：生成されたYAMLを表示
DEBUG_STYLE=true

# 実行
python post_article.py
```

**💡 スタイルガイド実行例：**
```
🎨 スタイルガイド機能を使用します
🎨 スタイル分析 1/4: https://tech-blog.com/ai-guide
✅ スタイル特徴抽出完了
🎨 スタイル分析 2/4: ./reference/sample1.md
✅ スタイル特徴抽出完了
...
✨ スタイル特徴統合完了
📈 見出し絵文字率: 75%
📝 文体: polite
🎨 スタイルガイド付き記事生成完了！
📊 統合スタイル特徴数: 4
✅ スタイルガイド統合記事投稿完了！（4ソース統合）
```

## ⚙️ 環境変数設定

```env
# 基本設定
WP_URL=https://your-site.com
WP_USER=your_username
WP_APP_PASS=your_app_password
OPENAI_API_KEY=your_openai_api_key

# 参考記事設定
REFERENCE_MODE=keywords  # keywords | url | file | multiple

# 単一記事設定
REFERENCE_URL=https://example.com/article
REFERENCE_FILE=./reference/sample.md

# 複数記事設定（カンマ区切り）
REFERENCE_URLS=https://site1.com/a1,https://site2.com/a2
REFERENCE_FILES=./ref/guide1.md,./ref/guide2.md

# 記事テーマ
ARTICLE_THEME=AI活用完全ガイド

# 🆕 スタイルガイド設定
USE_STYLE_GUIDE=true     # スタイル統合機能の有効/無効
DEBUG_STYLE=false        # YAMLガイド表示（デバッグ用）
```

## 🧪 テスト機能

```bash
# 参考記事機能の全テスト（スタイルガイド含む）
python test_reference.py
```

**🎨 テスト結果例：**
```
=== スタイル特徴抽出テスト ===
🎨 2つのソースからスタイル抽出:
  - reference/sample.md
  - reference/sample2.md
✅ スタイル特徴統合完了!
📊 見出し頻度: 4.2/1000語
📊 絵文字率: 60%
📊 箇条書き密度: 12.5%
📊 文体: polite
📊 見出しスタイル: moderate_emoji
📊 構造スタイル: moderate_lists
```

## 📁 ファイル構成

```
wp-autp/
├── generate_article.py      # 記事生成（スタイルガイド機能含む）
├── post_article.py         # WordPress投稿
├── test_reference.py       # テストスクリプト（スタイルテスト含む）
├── reference/              # 参考記事フォルダ
│   ├── sample.md          # サンプル参考記事1
│   └── sample2.md         # サンプル参考記事2
├── keywords.csv           # キーワードリスト
├── last_index.txt         # 進行状況
└── env_example.txt        # 環境変数例
```

## 🔧 スタイルガイドの技術詳細

### YAML生成例
```yaml
document_style:
  heading_frequency: "4.2 H2見出し per 1000語"
  emoji_usage:
    in_headings: "60%の見出しに絵文字"
    overall_density: "2.1 絵文字 per 1000文字"
    style: "moderate_emoji"
  structure:
    bullet_density: "12.5%の行が箇条書き"
    style: "moderate_lists"
    code_blocks: true
    tables: false
  writing_style:
    tone: "polite"
    avg_sentence_length: "28文字"
    formality: 0.8
    english_ratio: "15.2%"

generation_rules:
  見出し: "H2見出しに絵文字を適度に使用"
  箇条書き: "• を使用し、適度な密度で配置"
  語調: "です・ます調"
  文長: "読みやすい長さに調整"
  構成: "視覚的にわかりやすく整理"
```

### スタイル分析アルゴリズム
1. **正規表現分析**: 見出し・箇条書き・絵文字パターンを抽出
2. **統計計算**: 密度・比率・平均値を算出
3. **カテゴリ判定**: スタイルタイプを自動分類
4. **YAML生成**: AI可読形式でガイドを構造化
5. **プロンプト統合**: システムプロンプトに組み込み

## 🎯 活用例

### 競合記事リサーチ & スタイル統合
```bash
REFERENCE_MODE=multiple
USE_STYLE_GUIDE=true
REFERENCE_URLS=https://competitor1.com/guide,https://competitor2.com/tutorial,https://expert-blog.com/tips
ARTICLE_THEME=競合を参考にした独自ガイド
```

### 社内資料の統合ブログ化
```bash
REFERENCE_MODE=multiple
USE_STYLE_GUIDE=true
REFERENCE_FILES=./docs/manual1.md,./docs/guide2.md,./docs/faq.html
ARTICLE_THEME=統一された社内ナレッジ
```

### 多様なソースからの最適化記事
```bash
REFERENCE_URLS=https://official-docs.com/api-guide
REFERENCE_FILES=./internal/best-practices.md,./examples/use-cases.md
USE_STYLE_GUIDE=true
ARTICLE_THEME=最適化されたAPI実践ガイド
```

## 📊 スタイルガイド生成結果例

```
=== 複数参考記事モード: multiple ===
🎨 スタイルガイド機能を使用します
📚 複数参考記事モード: 4つのソース
  1. https://example1.com/chatgpt-guide
  2. https://example2.com/ai-tutorial  
  3. ./reference/ai-basics.md
  4. ./reference/practical-tips.md

🎨 スタイル分析 1/4 を処理中: https://example1.com/chatgpt-guide
✅ スタイル特徴抽出完了
📖 参考記事 2/4 を処理中: https://example2.com/ai-tutorial
✅ スタイル特徴抽出完了
🎨 スタイル分析 3/4 を処理中: ./reference/ai-basics.md
✅ スタイル特徴抽出完了
🎨 スタイル分析 4/4 を処理中: ./reference/practical-tips.md
✅ スタイル特徴抽出完了

✨ スタイル特徴統合完了
📈 見出し絵文字率: 70%
📝 文体: polite
📊 統合セクション数: 5

🎨 スタイルガイド付き記事生成完了！
📊 統合スタイル特徴数: 4
✅ スタイルガイド統合記事投稿完了！（4ソース統合）
URL: https://ai-blog.com/?p=456
```

## 📋 システム要件

- Python 3.8+
- 必要ライブラリ：
  - `openai` - GPT-4o & DALL-E 3
  - `requests` - API通信
  - `beautifulsoup4` - HTML解析
  - `Pillow` - 画像処理
  - `python-dotenv` - 環境変数
  - `pyyaml` - スタイルガイドYAML生成

## 🔄 cron設定例

```bash
# スタイルガイド統合を1日3回自動実行
0 8 * * * cd /path/to/wp-autp && python post_article.py
0 12 * * * cd /path/to/wp-autp && python post_article.py  
0 18 * * * cd /path/to/wp-autp && python post_article.py
```

---

**🎉 これで複数の競合記事・資料を統合した最高品質の記事を、参考記事のスタイルを忠実に再現して自動生成できます！**

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