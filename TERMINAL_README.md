# 🖥️ ターミナル版 - 音声から記事化ツール

ターミナルに音声ファイルをドラッグ&ドロップするだけで記事を生成し、結果をGUIダイアログボックスで表示するツールです。

## 🚀 クイックスタート

### 1. セットアップ（初回のみ）

```bash
# 依存関係のインストール
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 使用方法

#### 方法A: 簡単起動スクリプト

```bash
# 音声ファイルを指定
./audio2article path/to/your/audio.mp3

# または対話モード
./audio2article
```

#### 方法B: 直接実行

```bash
# 音声ファイルを指定
python terminal_tool.py path/to/your/audio.mp3

# または対話モード
python terminal_tool.py
```

#### 方法C: ドラッグ&ドロップ

1. ターミナルで対話モードを起動:
   ```bash
   ./audio2article
   ```

2. 音声ファイルをターミナルにドラッグ&ドロップ

3. Enterキーを押す

## 🎯 特徴

### 📱 GUIダイアログボックス
- **美しい表示**: 生成された記事を見やすいダイアログで表示
- **ワンクリックコピー**: クリップボードに瞬時にコピー
- **ファイル保存**: Markdownファイルとして保存可能
- **フォント最適化**: 日本語に最適化されたフォント

### 🔧 高度な処理機能
- **多形式対応**: MP3, WAV, M4A, etc.
- **自動音声変換**: ffmpegによる最適化
- **AI文字起こし**: Gemini API + フォールバック
- **文体分析**: MeCabによる自然な文章生成

### 💡 使いやすさ
- **ドラッグ&ドロップ対応**
- **進捗表示**: リアルタイムで処理状況を表示
- **エラーハンドリング**: 分かりやすいエラーメッセージ
- **一時ファイル自動削除**

## 📊 処理フロー

```
🎵 音声ファイル
    ↓
🔄 音声形式変換 (ffmpeg)
    ↓
🤖 AI文字起こし (Gemini API)
    ↓
📝 文体分析 (MeCab)
    ↓
✍️ 記事生成 (Gemini API)
    ↓
📱 GUIダイアログ表示
    ↓
📋 クリップボードコピー / 💾 ファイル保存
```

## 🎨 スクリーンショット例

```
🎙️==================================================
    音声から記事化ツール (ターミナル版)
==================================================

🎵 処理開始: my_podcast.mp3
🔄 音声ファイルを変換中...
🤖 Gemini APIで文字起こし中...
✍️ AI記事生成中...
✅ 処理完了！

[GUIダイアログボックスが開きます]
┌─────────────────────────────────────┐
│ 📝 記事生成完了 - my_podcast.mp3    │
├─────────────────────────────────────┤
│ ✨ 記事が生成されました！            │
│ 📁 元ファイル: my_podcast.mp3       │
│                                     │
│ [記事内容がここに表示されます]       │
│                                     │
│ [📋 クリップボードにコピー] [💾 保存] │
│               [✅ 閉じる]            │
└─────────────────────────────────────┘
```

## 💻 システム要件

- **Python**: 3.8以上
- **ffmpeg**: 音声変換用
- **GUI**: tkinter（通常Python標準）
- **OS**: macOS, Linux, Windows

## 🔧 トラブルシューティング

### GUI表示されない場合

**macOS:**
```bash
# X11がインストールされていない場合
brew install --cask xquartz
```

**Linux:**
```bash
# tkinter がインストールされていない場合
sudo apt-get install python3-tk
```

### ファイルアクセス権限エラー

```bash
# 実行権限を付与
chmod +x audio2article
```

### ffmpeg not found エラー

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

## 🎯 高度な使い方

### バッチ処理

```bash
# 複数ファイルを連続処理
for file in *.mp3; do
    ./audio2article "$file"
done
```

### カスタムスクリプト作成

```python
from terminal_tool import AudioToArticleCLI

cli = AudioToArticleCLI()
article = cli.process_audio_file("my_audio.mp3")
```

## 📝 ライセンス

MIT License

## 🆘 サポート

問題が発生した場合：

1. **APIキー確認**: `.env`ファイルのGOOGLE_API_KEY
2. **ffmpeg確認**: `ffmpeg -version`
3. **依存関係確認**: `pip list`
4. **権限確認**: `ls -la audio2article`

それでも解決しない場合は、イシューを作成してください。