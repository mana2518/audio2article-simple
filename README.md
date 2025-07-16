# 🎙️ 音声から記事化ツール

音声ファイルを自動でnote記事に変換するツールです。Web版とターミナル版の2つのバージョンがあります。

## ✨ 機能

- 🎵 **多形式対応**: MP3、WAV、M4A、などの音声ファイルに対応
- 🤖 **AI文字起こし**: Google Gemini APIによる高精度な音声認識
- 📝 **記事自動生成**: AIが自然な文章に変換
- 🎨 **美しいUI**: モダンなデザインとドラッグ&ドロップ対応
- 📊 **リアルタイム進捗**: プログレスバーで処理状況を可視化
- 📋 **簡単コピー**: ワンクリックでテキストをコピー可能

## 🚀 セットアップ

### 1. 必要な環境

- Python 3.8以上
- ffmpeg（音声変換用）

### 2. インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd audio_to_article_new

# 仮想環境の作成
python3 -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. APIキーの設定

`.env` ファイルを編集して、Google AI（Gemini）APIキーを設定してください：

```bash
# Google AI (Gemini) APIキー
GOOGLE_API_KEY=your_gemini_api_key_here
```

APIキーは [Google AI Studio](https://aistudio.google.com/) で取得できます。

### 4. ffmpegのインストール

音声ファイル変換のため、ffmpegが必要です：

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
[公式サイト](https://ffmpeg.org/download.html)からダウンロードして、PATHに追加してください。

## 🎯 使用方法

### 🌐 Web版

```bash
# サーバー起動
source venv/bin/activate
python app.py

# ブラウザで http://127.0.0.1:8000 にアクセス
```

**特徴:**
- ブラウザでの美しいGUI
- ドラッグ&ドロップアップロード
- リアルタイムプログレス表示
- Markdown/プレビュー切り替え

### 🖥️ ターミナル版

```bash
# 音声ファイルを直接指定
./audio2article-simple audio_file.mp3

# または簡単起動スクリプト
./audio2article-simple
```

**特徴:**
- ターミナルに音声ファイルをドラッグ&ドロップ
- 結果を自動でクリップボードにコピー
- ファイル保存オプション
- GUI依存なし

## 📁 プロジェクト構成

```
audio_to_article_new/
├── app.py              # メインアプリケーション
├── simple_server.py    # シンプル版（依存関係最小）
├── requirements.txt    # Python依存関係
├── .env               # 環境変数
├── static/
│   └── index.html     # フロントエンドUI
└── README.md          # このファイル
```

## 🔧 技術スタック

- **バックエンド**: FastAPI, Python
- **AI**: Google Gemini API, Google Cloud Speech-to-Text
- **フロントエンド**: HTML5, CSS3, JavaScript
- **音声処理**: ffmpeg
- **文体解析**: MeCab

## 🎨 特徴

### 高度な音声処理
- 複数の音声形式に自動対応
- ffmpegによる音声変換
- フォールバック機能付きの文字起こし

### 直感的なUI
- ドラッグ&ドロップ対応
- リアルタイム進捗表示
- レスポンシブデザイン
- タブ切り替え（Markdown/プレビュー）

### 信頼性
- エラーハンドリング
- 一時ファイルの自動削除
- 非同期処理

## 🚨 注意事項

- Gemini APIには利用制限があります
- 大きなファイル（数十MB以上）は処理に時間がかかる場合があります
- インターネット接続が必要です

## 📝 ライセンス

MIT License

## 🤝 貢献

プルリクエストやイシューの報告をお待ちしています！

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. APIキーが正しく設定されているか
2. ffmpegがインストールされているか
3. インターネット接続が安定しているか
4. 音声ファイルが対応形式か

それでも解決しない場合は、イシューを作成してください。