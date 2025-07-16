# Audio2Article Whisper移行ガイド

## 概要
Gemini APIからWhisperベースの無料システムに移行しました。

## 変更点

### 🔄 移行前 (有料版)
- **音声認識**: Gemini API (月額$30-50)
- **記事生成**: Gemini API (自動)
- **コスト**: 従量課金

### ✅ 移行後 (無料版)
- **音声認識**: Whisper (ローカル・無料)
- **記事生成**: Claude Code (手動・無料)
- **コスト**: 完全無料

## セットアップ

```bash
cd /Users/manami/audio_to_article_new
pip install -r requirements-whisper.txt
```

## 使用方法

### 1. Whisper版の実行
```bash
./audio2article-simple [音声ファイル]
```

### 2. 生成されるもの
- 文字起こしテキスト
- Claude Code用プロンプト

### 3. 記事生成手順
1. Whisperで音声を文字起こし
2. 生成されたプロンプトをClaude Codeにコピー
3. Claude Codeで記事を生成

## ファイル構成

- `audio2article-simple` - メインランチャー (Whisper版に更新済み)
- `audio2article-whisper` - Whisper専用ランチャー 
- `whisper_transcriber.py` - Whisperベース処理システム
- `terminal_simple.py` - 旧Geminiベースシステム (非推奨)
- `requirements-whisper.txt` - Whisper版依存関係

## 利点

✅ **完全無料** - APIコストゼロ  
✅ **プライバシー** - ローカル処理  
✅ **高精度** - Whisper音声認識  
✅ **柔軟性** - 手動記事調整可能  

## 注意点

- 記事生成は手動でClaude Codeに依頼する必要があります
- 初回実行時にWhisperモデルのダウンロードが発生します
- ローカル処理のため、処理時間が若干長くなる場合があります