# 🎙️ Whisper + Claude Code 音声記事化システム

**💰 APIコストゼロ・ローカル処理対応**

音声ファイルをWhisperでローカル文字起こし → Claude Codeで記事生成する、APIコスト不要のシステムです。

## ✨ 新システムの特徴

- 🆓 **完全無料**: APIコスト一切なし
- 🏠 **ローカル処理**: Whisperによる高精度文字起こし
- 📚 **文体学習継続**: note本文.mdから文体学習
- 🤖 **Claude Code連携**: 自動でプロンプト生成
- 🎨 **既存プロンプト維持**: 従来の記事生成品質を保持

## 🚀 セットアップ

### 1. 新しい依存関係のインストール

```bash
cd /Users/manami/audio_to_article_new
source venv/bin/activate
pip install -r requirements-whisper.txt
```

### 2. ffmpegの確認（既存）

音声変換用のffmpegが必要です：

```bash
# macOS
brew install ffmpeg

# 確認
ffmpeg -version
```

## 🎯 使用方法

### 🖥️ 新しいWhisperシステム

```bash
cd /Users/manami/audio_to_article_new
./audio2article-whisper
```

**または音声ファイルを直接指定:**
```bash
./audio2article-whisper audio_file.mp3
```

### 📝 ワークフロー

1. **音声アップロード** → Whisperで文字起こし
2. **Claude Codeプロンプト自動生成** → コピー&ペースト用
3. **Claude Codeに貼り付け** → 高品質記事生成

## 🔧 Whisperモデル選択

精度と速度のバランスで選択可能：

```bash
# 高速・軽量（推奨）
./audio2article-whisper --model base

# 高精度・重い
./audio2article-whisper --model large
```

**モデル比較:**
- `tiny`: 超高速、精度普通
- `base`: 高速、精度良好（推奨）
- `small`: 中速、精度高
- `medium`: 低速、精度高
- `large`: 最低速、最高精度

## 📊 出力結果

### 1. 文字起こし結果
```
📄 文字起こし結果:
----------------------------------------
マナミです。今日はAIを使った新しいサービスについて話します...
```

### 2. Claude Code用プロンプト
```
🤖 Claude Code用プロンプト生成完了
以下のプロンプトをClaude Codeにコピー&ペーストしてください：
----------------------------------------
# 目的
あなたは優秀なライターです。noteに掲載する記事を作成します...
```

## 💡 使用例

```bash
# 基本使用
./audio2article-whisper my_audio.mp3

# 高精度モード
./audio2article-whisper --model large my_audio.wav

# インタラクティブモード
./audio2article-whisper
```

## 📁 プロジェクト構成（更新版）

```
audio_to_article_new/
├── whisper_transcriber.py    # 新メインシステム
├── audio2article-whisper     # 新起動スクリプト
├── requirements-whisper.txt  # 新依存関係
├── README-WHISPER.md         # このファイル
├── (N)note本文.md           # 文体学習用（外部）
└── 旧システム/
    ├── terminal_simple.py    # 旧Gemini版
    ├── audio2article-simple  # 旧起動スクリプト
    └── requirements.txt      # 旧依存関係
```

## 🎨 文体学習機能

従来通り `/Users/manami/(N)note本文.md` から文体を学習：

- 話し言葉的な表現パターン
- 感情表現や接続詞の使い方
- 段落構成や改行パターン
- 強調表現（「」）の適切な使用

## 💰 コスト比較

| システム | 文字起こし | 記事生成 | 月間コスト |
|----------|------------|----------|------------|
| 旧Gemini版 | $0.50/回 | $0.50/回 | $30-50 |
| **新Whisper版** | **無料** | **無料** | **$0** |

## 🚨 注意事項

- 初回起動時にWhisperモデルをダウンロード（数分）
- 大きなファイルは処理に時間がかかる場合があります
- ローカル処理のため、インターネット接続不要

## 🤝 サポート

問題が発生した場合：

1. ffmpegがインストールされているか確認
2. 仮想環境が正しく設定されているか確認
3. 音声ファイルが対応形式か確認（MP3, WAV, M4A等）

---

**🎉 これで完全無料の音声記事化システムが完成しました！**