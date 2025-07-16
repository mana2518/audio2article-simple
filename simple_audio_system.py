#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプル音声記事化システム v1.0
確実に動作することを重視した最小構成版

使用方法:
python3 simple_audio_system.py

対応音声形式: mp3, wav, m4a, flac など
"""

import os
import json
import logging
from pathlib import Path
import subprocess
import sys

# Claude APIをオプション化
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("💡 anthropicがインストールされていません。手動プロンプト生成モードで動作します。")
    print("   Claude自動生成を使用したい場合: pip3 install --user anthropic")

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleAudioToArticle:
    """シンプルな音声記事化システム"""
    
    def __init__(self):
        self.setup_directories()
        self.load_reference_text()
        self.setup_claude()
        
    def setup_directories(self):
        """必要なディレクトリを作成"""
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
    def load_reference_text(self):
        """文体参考テキストを読み込み"""
        reference_file = Path("(N)note本文.md")
        if reference_file.exists():
            with open(reference_file, 'r', encoding='utf-8') as f:
                self.reference_text = f.read()[:4000]  # 最初の4000文字のみ
        else:
            # デフォルトの参考文体
            self.reference_text = """マナミです。

今日は、私が最近感じていることについてお話ししたいと思います。

フリーランスとして働いていると、日々色々な発見があります。特に最近は、効率的な働き方について考えることが多くなりました。

子どもたちとの時間も大切にしたいですし、仕事も充実させたい。そのバランスを取るのは簡単ではありませんが、少しずつ自分なりの方法を見つけています。

皆さんも、きっと同じような悩みを抱えているのではないでしょうか。

今後も、こうした日常の気づきや学びを、皆さんと共有していきたいと思っています。"""
    
    def setup_claude(self):
        """Claude APIの設定"""
        if not ANTHROPIC_AVAILABLE:
            self.claude_client = None
            return
            
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("⚠️  Claude APIキーが設定されていません")
            print("環境変数 ANTHROPIC_API_KEY を設定してください")
            print("例: export ANTHROPIC_API_KEY='your-api-key-here'")
            self.claude_client = None
        else:
            self.claude_client = anthropic.Anthropic(api_key=api_key)
            logger.info("✅ Claude APIが設定されました")
    
    def check_whisper_installation(self):
        """Whisperのインストール状況をチェック"""
        try:
            import whisper
            logger.info("✅ Whisperが正常にインストールされています")
            return True
        except ImportError:
            logger.error("❌ Whisperがインストールされていません")
            self.install_whisper()
            return False
    
    def install_whisper(self):
        """Whisperをインストール"""
        print("\n🔧 Whisperをインストールしています...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "openai-whisper", "--quiet"
            ])
            print("✅ Whisperのインストールが完了しました")
        except subprocess.CalledProcessError as e:
            print(f"❌ Whisperのインストールに失敗しました: {e}")
            print("手動でインストールしてください: pip install openai-whisper")
            return False
        return True
    
    def get_audio_duration(self, audio_path):
        """音声ファイルの長さを取得"""
        try:
            import librosa
            duration = librosa.get_duration(path=str(audio_path))
            return duration
        except ImportError:
            # librosaがない場合は推定値を返す
            file_size = Path(audio_path).stat().st_size / (1024 * 1024)  # MB
            estimated_duration = file_size * 8  # 大まかな推定（1MB = 約8分）
            return estimated_duration
        except:
            return None
    
    def show_progress_bar(self, current, total, bar_length=30):
        """プログレスバーを表示"""
        if total == 0:
            progress = 1.0
        else:
            progress = min(current / total, 1.0)
        
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        percent = progress * 100
        
        print(f"\r⏳ 処理中: [{bar}] {percent:.1f}% ({current:.0f}s/{total:.0f}s)", end='', flush=True)
    
    def transcribe_audio(self, audio_path):
        """音声をテキストに変換"""
        try:
            import whisper
            import time
            
            # 音声ファイルの確認
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"音声ファイルが見つかりません: {audio_path}")
            
            # 音声の長さを取得
            duration = self.get_audio_duration(audio_path)
            if duration:
                print(f"🎵 音声ファイル長さ: {duration/60:.1f}分")
                print(f"⏱️  推定処理時間: {duration/4:.1f}分（音声の約1/4の時間）")
            
            # Whisperモデルを読み込み（高速化のためtinyモデルを使用）
            print("📥 Whisperモデルを読み込んでいます（高速処理用）...")
            model = whisper.load_model("tiny")
            
            print("🎙️ 音声を文字起こししています...")
            
            # 進行状況を表示するためのカスタム関数
            start_time = time.time()
            
            # 文字起こし実行（高速化のため軽量モデルを使用）
            result = model.transcribe(
                str(audio_path), 
                language="ja",
                verbose=True,  # 進行状況を表示
                word_timestamps=False,  # 高速化
                fp16=False  # CPU使用時はFP32を使用
            )
            
            print()  # 改行
            
            transcript = result["text"].strip()
            
            if len(transcript) < 50:
                raise ValueError("音声の文字起こし結果が短すぎます（50文字未満）")
            
            elapsed_time = time.time() - start_time
            print(f"✅ 文字起こし完了: {len(transcript)}文字 (処理時間: {elapsed_time/60:.1f}分)")
            return transcript
            
        except Exception as e:
            print()  # 改行
            logger.error(f"❌ 文字起こしエラー: {e}")
            raise
    
    def create_prompt(self, transcript):
        """記事生成用のプロンプトを作成"""
        prompt = f"""#目的

あなたは優秀なライターです。noteに掲載する記事を作成します。　

#最重要

文体や口調は主に「知識」の中にある「編集済み　note本文」を参考にしてください。なるべく話しているような雰囲気を残してほしいです。

## 知識（編集済み　note本文）
```
{self.reference_text}
```

要求: 添付するテキストは、音声配信の内容の文字起こしデータ（日本語）です。全体を通して2500文字程度に収めるように構成してください。以下の構成に従って要約を行ってください。

## 入力データ
以下は音声配信の文字起こしデータです：
```
{transcript}
```

## 出力構成
1. 導入部（約200文字）:
   - 音声配信の主題を結論、その重要性を簡潔に紹介します。

2. 主要内容の要約（約2000文字）:
   - 主要な議論やポイントを、明確かつ簡潔に要約します。

3. 結論（約300文字）:

このプロセスを通じて、リスナーが元の音声配信から得ることができる主要な知見と情報を効果的に伝えることが目的です。各セクションは情報を適切に要約し、読者にとって理解しやすく、かつ情報量が豊富であることを心掛けてください。

## その他の制約
・最初の自己紹介文「3人の子供達を育てながらSNS発信をしているママフリーランスです」は削除し、「マナミです。」→すぐ本文へ続けてください。

・「ですます調」にしてください。

・内容から段落わけ、改行を適切に行ってください

・強調するところは「」で区切ってください

・子供は「子ども」と表記してください

・見出しをつけないでください

それでは記事を作成してください："""
        
        return prompt
    
    def generate_article_with_claude(self, transcript):
        """Claudeで記事を自動生成"""
        if not self.claude_client:
            print("❌ Claude APIが設定されていないため、自動生成できません")
            return None
        
        try:
            print("🤖 Claudeで記事を生成しています...")
            
            prompt = self.create_prompt(transcript)
            
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            article = response.content[0].text
            
            # 記事をファイルに保存
            base_name = Path(transcript).stem if isinstance(transcript, (str, Path)) else "generated"
            article_file = self.output_dir / f"{base_name}_article.txt"
            
            with open(article_file, 'w', encoding='utf-8') as f:
                f.write(article)
            
            # クリップボードにコピー
            try:
                import pyperclip
                pyperclip.copy(article)
                print("📋 記事をクリップボードにコピーしました！")
            except ImportError:
                print("💡 pyperclipをインストールするとクリップボードにコピーできます")
                print("   インストール: pip install pyperclip")
            except Exception as e:
                print(f"⚠️  クリップボードへのコピーに失敗: {e}")
            
            logger.info(f"✅ 記事生成完了: {article_file}")
            return article
            
        except Exception as e:
            logger.error(f"❌ Claude記事生成エラー: {e}")
            return None
    
    def generate_article_manual(self, transcript):
        """手動でChatGPTを使用するためのプロンプトを出力"""
        prompt = self.create_prompt(transcript)
        
        # プロンプトをファイルに保存
        prompt_file = self.output_dir / "prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        print(f"\n📝 プロンプトを保存しました: {prompt_file}")
        print("\n" + "="*60)
        print("🤖 以下のプロンプトをChatGPTにコピー&ペーストしてください：")
        print("="*60)
        print(prompt)
        print("="*60)
        
        # プロンプトをクリップボードにコピー（オプション）
        try:
            import pyperclip
            pyperclip.copy(prompt)
            print("📋 プロンプトをクリップボードにコピーしました！")
        except ImportError:
            print("💡 pyperclipをインストールするとプロンプトを自動でクリップボードにコピーできます")
            print("   インストール: pip install pyperclip")
        except Exception as e:
            print(f"⚠️  クリップボードへのコピーに失敗: {e}")
        
        return prompt
    
    def save_transcript(self, transcript, audio_filename):
        """文字起こし結果を保存"""
        base_name = Path(audio_filename).stem
        transcript_file = self.output_dir / f"{base_name}_transcript.txt"
        
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        logger.info(f"📄 文字起こし結果を保存: {transcript_file}")
        return transcript_file
    
    def process_audio(self, audio_path):
        """音声ファイルを処理する完全なフロー"""
        try:
            print(f"\n🎵 音声ファイルを処理します: {audio_path}")
            
            # Whisperのインストール確認
            if not self.check_whisper_installation():
                print("Whisperのインストール後、再度実行してください。")
                return None
            
            # 文字起こし
            transcript = self.transcribe_audio(audio_path)
            
            # 文字起こし結果を保存
            transcript_file = self.save_transcript(transcript, audio_path)
            
            # 記事生成
            article = None
            if self.claude_client:
                # Claudeで自動生成
                article = self.generate_article_with_claude(transcript)
                if article:
                    print(f"\n✅ Claude記事生成完了！")
                    print(f"📄 文字起こし: {transcript_file}")
                    print(f"📝 生成記事: {self.output_dir}/{Path(audio_path).stem}_article.txt")
                    print(f"📋 記事はクリップボードにコピー済みです")
                    
                    # 記事内容を表示
                    print("\n" + "="*60)
                    print("📖 生成された記事:")
                    print("="*60)
                    print(article)
                    print("="*60)
                else:
                    print("❌ Claude記事生成に失敗しました。手動プロンプトを表示します。")
                    prompt = self.generate_article_manual(transcript)
            else:
                # 手動プロンプト生成
                prompt = self.generate_article_manual(transcript)
                print(f"\n✅ 処理完了！")
                print(f"📄 文字起こし: {transcript_file}")
                print(f"📝 プロンプト: {self.output_dir}/prompt.txt")
                print(f"\n💡 生成されたプロンプトをChatGPTにペーストして記事を生成してください。")
            
            return {
                'transcript': transcript,
                'transcript_file': transcript_file,
                'article': article if self.claude_client else None
            }
            
        except Exception as e:
            logger.error(f"❌ 処理エラー: {e}")
            return None

def main():
    """メイン関数"""
    print("🎙️" + "="*50)
    print("   シンプル音声記事化システム v1.0")
    print("   確実動作を重視した最小構成版")
    print("="*50)
    
    # システム初期化
    system = SimpleAudioToArticle()
    
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
        
        # ドラッグ&ドロップ時のパス処理
        # 前後のクォートを削除
        user_input = user_input.strip('"').strip("'")
        
        # エスケープ文字を処理
        user_input = user_input.replace('\\ ', ' ')
        user_input = user_input.replace('\\~', '~')
        user_input = user_input.replace('\\【', '【')
        user_input = user_input.replace('\\】', '】')
        user_input = user_input.replace('\\。', '。')
        
        # パスを展開
        user_input = os.path.expanduser(user_input)
        
        audio_path = Path(user_input)
        
        if not audio_path.exists():
            print(f"❌ ファイルが見つかりません: {audio_path}")
            print(f"🔍 確認したパス: {user_input}")
            continue
        
        # 音声ファイルを処理
        result = system.process_audio(audio_path)
        
        if result:
            # 別のファイルを処理するか確認
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