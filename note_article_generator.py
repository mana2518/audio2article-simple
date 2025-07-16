#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Note記事生成システム
音声→Whisper文字起こし→note記事生成→クリップボードコピー

要件:
- 音声ファイルをドラッグ&ドロップで処理
- Whisperで文字起こし
- (N)note本文.mdを参考にしてnote記事生成
- 生成した記事をクリップボードにコピー
- 音声データ入れ替え時は前の文字起こしデータをリセット
"""

import os
import sys
import shutil
import logging
from pathlib import Path
import time
import json

# 必要なライブラリのインポート
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NoteArticleGenerator:
    """Note記事生成システム"""
    
    def __init__(self):
        self.setup_directories()
        self.load_reference_text()
        self.setup_claude()
        self.previous_transcript = None
        self.current_audio_path = None
        
    def setup_directories(self):
        """必要なディレクトリを作成"""
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # 一時ディレクトリをクリア
        self.temp_dir = Path("temp_audio")
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
    def load_reference_text(self):
        """参考文体テキストを読み込み"""
        reference_file = Path("/Users/manami/(N)note本文.md")
        if reference_file.exists():
            with open(reference_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 最初の3000文字を参考文体として使用
                self.reference_text = content[:3000]
                logger.info("✅ 参考文体を読み込みました")
        else:
            # デフォルトの参考文体
            self.reference_text = """マナミです。

今日は、私が最近感じていることについてお話ししたいと思います。

フリーランスとして働いていると、日々色々な発見があります。特に最近は、効率的な働き方について考えることが多くなりました。

子どもたちとの時間も大切にしたいですし、仕事も充実させたい。そのバランスを取るのは簡単ではありませんが、少しずつ自分なりの方法を見つけています。

皆さんも、きっと同じような悩みを抱えているのではないでしょうか。

今後も、こうした日常の気づきや学びを、皆さんと共有していきたいと思っています。"""
            logger.info("⚠️  参考文体ファイルが見つかりません。デフォルトを使用します")
    
    def setup_claude(self):
        """Claude APIの設定"""
        if not ANTHROPIC_AVAILABLE:
            logger.error("❌ anthropicがインストールされていません")
            sys.exit(1)
        
        # 環境変数またはファイルからAPIキーを取得
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            # .envファイルを確認
            env_file = Path('.env')
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('ANTHROPIC_API_KEY='):
                            api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                            break
        
        if not api_key:
            logger.error("❌ ANTHROPIC_API_KEYが設定されていません")
            print("環境変数またはファイルでANTHROPIC_API_KEYを設定してください")
            sys.exit(1)
        
        try:
            self.claude_client = anthropic.Anthropic(api_key=api_key)
            logger.info("✅ Claude APIが設定されました")
        except Exception as e:
            logger.error(f"❌ Claude API設定エラー: {e}")
            sys.exit(1)
    
    def check_dependencies(self):
        """依存関係をチェック"""
        missing = []
        
        if not WHISPER_AVAILABLE:
            missing.append("openai-whisper")
        if not ANTHROPIC_AVAILABLE:
            missing.append("anthropic")
        if not CLIPBOARD_AVAILABLE:
            missing.append("pyperclip")
        
        if missing:
            print("❌ 必要なライブラリがインストールされていません:")
            for lib in missing:
                print(f"   pip install {lib}")
            return False
        
        return True
    
    def reset_transcription_data(self):
        """文字起こしデータをリセット"""
        self.previous_transcript = None
        logger.info("🗑️ 文字起こしデータをリセットしました")
    
    def get_audio_duration(self, audio_path):
        """音声ファイルの長さを取得"""
        try:
            import librosa
            duration = librosa.get_duration(path=str(audio_path))
            return duration
        except ImportError:
            # librosaがない場合はファイルサイズから推定
            file_size = Path(audio_path).stat().st_size / (1024 * 1024)  # MB
            estimated_duration = file_size * 8  # 大まかな推定
            return estimated_duration
        except Exception:
            return None
    
    def transcribe_audio(self, audio_path):
        """音声をテキストに変換"""
        try:
            # 音声ファイルの確認
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"音声ファイルが見つかりません: {audio_path}")
            
            # 新しい音声ファイルの場合はデータをリセット
            if self.current_audio_path != audio_path:
                self.reset_transcription_data()
                self.current_audio_path = audio_path
            
            # 音声の長さを取得
            duration = self.get_audio_duration(audio_path)
            if duration:
                print(f"🎵 音声ファイル長さ: {duration/60:.1f}分")
                print(f"⏱️  推定処理時間: {duration/4:.1f}分")
            
            # Whisperモデルを読み込み
            print("📥 Whisperモデルを読み込んでいます...")
            model = whisper.load_model("base")  # baseモデルで精度と速度のバランスを取る
            
            print("🎙️ 音声を文字起こししています...")
            start_time = time.time()
            
            # 文字起こし実行（タイムスタンプなし、進捗表示なし）
            result = model.transcribe(
                str(audio_path), 
                language="ja",
                verbose=False,
                word_timestamps=False,
                fp16=False,
                no_speech_threshold=0.6,
                logprob_threshold=-1.0,
                compression_ratio_threshold=2.4
            )
            
            # テキストのみを取得（タイムスタンプを除去）
            transcript = result["text"].strip()
            
            if len(transcript) < 50:
                raise ValueError("音声の文字起こし結果が短すぎます")
            
            elapsed_time = time.time() - start_time
            print(f"✅ 文字起こし完了: {len(transcript)}文字 (処理時間: {elapsed_time/60:.1f}分)")
            
            # 文字起こし結果を保存
            self.previous_transcript = transcript
            self.save_transcript(transcript, audio_path)
            
            return transcript
            
        except Exception as e:
            logger.error(f"❌ 文字起こしエラー: {e}")
            raise
    
    def save_transcript(self, transcript, audio_path):
        """文字起こし結果を保存"""
        base_name = Path(audio_path).stem
        transcript_file = self.output_dir / f"{base_name}_transcript.txt"
        
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        logger.info(f"📄 文字起こし結果を保存: {transcript_file}")
    
    def generate_article(self, transcript):
        """記事を生成"""
        try:
            print("🤖 記事を生成しています...")
            
            prompt = f"""あなたは優秀なライターです。noteに掲載する記事を作成します。

文体や口調は主に「知識」の中にある「編集済み　note本文」を参考にしてください。なるべく話しているような雰囲気を残してほしいです。

## 知識（編集済み　note本文）
```
{self.reference_text}
```

## 入力データ
以下は音声配信の文字起こしデータです：
```
{transcript}
```

## 制約
・最初の自己紹介文「3人の子供達を育てながらSNS発信をしているママフリーランスです」は削除し、「マナミです。」→すぐ本文へ続けてください。
・「ですます調」にしてください。
・内容から段落わけ、改行を適切に行ってください
・強調するところは「」で区切ってください
・子供は「子ども」と表記してください
・見出しをつけないでください

それでは記事を作成してください："""
            
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            article = response.content[0].text.strip()
            
            print("✅ 記事生成完了")
            return article
            
        except Exception as e:
            logger.error(f"❌ 記事生成エラー: {e}")
            raise
    
    def save_article(self, article, audio_path):
        """記事を保存"""
        base_name = Path(audio_path).stem
        article_file = self.output_dir / f"{base_name}_article.txt"
        
        with open(article_file, 'w', encoding='utf-8') as f:
            f.write(article)
        
        logger.info(f"📝 記事を保存: {article_file}")
    
    def copy_to_clipboard(self, text):
        """クリップボードにコピー"""
        if not CLIPBOARD_AVAILABLE:
            logger.warning("⚠️  pyperclipがインストールされていません")
            return False
        
        try:
            pyperclip.copy(text)
            logger.info("📋 クリップボードにコピーしました")
            return True
        except Exception as e:
            logger.error(f"❌ クリップボードコピーエラー: {e}")
            return False
    
    def process_audio(self, audio_path):
        """音声ファイルを処理する完全なフロー"""
        try:
            print(f"\n🎵 音声ファイルを処理します: {audio_path}")
            
            # 文字起こし
            transcript = self.transcribe_audio(audio_path)
            
            # 記事生成
            article = self.generate_article(transcript)
            
            # 記事保存
            self.save_article(article, audio_path)
            
            # クリップボードコピー
            self.copy_to_clipboard(article)
            
            print("\n" + "="*60)
            print("📖 生成された記事:")
            print("="*60)
            print(article)
            print("="*60)
            
            return article
            
        except Exception as e:
            logger.error(f"❌ 処理エラー: {e}")
            return None

def main():
    """メイン関数"""
    print("🎙️" + "="*50)
    print("   Note記事生成システム")
    print("   音声→Whisper→記事生成→クリップボード")
    print("="*50)
    
    # システム初期化
    generator = NoteArticleGenerator()
    
    # 依存関係チェック
    if not generator.check_dependencies():
        return
    
    while True:
        print("\n📁 音声ファイルのパスを入力してください:")
        print("（例: ./audio.mp3, /path/to/audio.wav）")
        print("💡 ドラッグ&ドロップも可能です！")
        print("終了する場合は 'q' を入力")
        
        user_input = input("\n➤ ").strip()
        
        if user_input.lower() == 'q':
            print("👋 お疲れさまでした！")
            break
        
        if not user_input:
            print("❌ ファイルパスを入力してください")
            continue
        
        # パス処理
        user_input = user_input.strip('"').strip("'")
        user_input = user_input.replace('\\ ', ' ')
        user_input = user_input.replace('\\~', '~')
        user_input = user_input.replace('\\【', '【')
        user_input = user_input.replace('\\】', '】')
        user_input = user_input.replace('\\。', '。')
        user_input = os.path.expanduser(user_input)
        
        audio_path = Path(user_input)
        
        if not audio_path.exists():
            print(f"❌ ファイルが見つかりません: {audio_path}")
            continue
        
        # 音声ファイルを処理
        article = generator.process_audio(audio_path)
        
        if article:
            print(f"\n✅ 処理完了！")
            print(f"📋 記事はクリップボードにコピー済みです")
            
            # 継続するか確認
            while True:
                continue_input = input("\n🔄 別のファイルを処理しますか？ (y/N): ").strip().lower()
                if continue_input in ['', 'n', 'no']:
                    print("👋 お疲れさまでした！")
                    return
                elif continue_input in ['y', 'yes']:
                    break
                else:
                    print("❌ 'y' または 'n' を入力してください")

if __name__ == "__main__":
    main()