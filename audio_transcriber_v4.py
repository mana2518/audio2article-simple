#!/usr/bin/env python3
"""
音声記事化システム v4.0 - 完全改良版
Whisperの依存関係問題を解決し、より安定した音声記事化を実現
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
import re
from datetime import datetime

# Whisperのインストール確認と自動インストール
def check_and_install_whisper():
    """Whisperの確認と自動インストール"""
    try:
        import whisper
        print("✅ Whisperは既にインストールされています")
        return True
    except ImportError:
        print("⚠️ Whisperがインストールされていません")
        print("🔄 自動インストールを開始します...")
        
        try:
            # pipでwhisperをインストール
            subprocess.check_call([sys.executable, "-m", "pip", "install", "openai-whisper", "--upgrade"])
            print("✅ Whisperのインストールが完了しました")
            import whisper
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Whisperのインストールに失敗: {e}")
            return False
        except ImportError:
            print("❌ インストール後もWhisperが見つかりません")
            return False

# 最初にWhisperをチェック
WHISPER_AVAILABLE = check_and_install_whisper()

if WHISPER_AVAILABLE:
    import whisper

# pyperclipのインストール確認
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("💡 pyperclipをインストールするとクリップボードコピーが可能になります: pip install pyperclip")

class TextCleaner:
    """音声認識テキストのクリーニングエンジン"""
    
    def __init__(self):
        self.patterns = {
            # 基本的な誤認識修正
            'まん波': 'マナミ',
            '日山波': 'マナミ',
            'ままふりなす': 'ママフリーランス',
            'フリランス': 'フリーランス',
            'コンテンチェーサーコーチューシン': 'コンテンツ作成',
            'バイブコーディング': 'ライブコーディング',
            'ワードブレス': 'WordPress',
            'ポートフリオ': 'ポートフォリオ',
            'サニーの子ども': '3人の子ども',
            'サニー': '3人',
            '一斉にス発進': 'SNS発信',
            'コンテンセサコ': 'コンテンツ作成',
            
            # 重複表現の修正
            'とという': 'という',
            'ととという': 'という',
            'とと': 'と',
            'やとぱり': 'やっぱり',
            'やとて': 'やって',
            'とて': 'って',
            'やとている': 'やっている',
            'やとています': 'やっています',
            
            # 語尾の修正
            '思今す': '思います',
            '思今した': '思いました',
            '今す': 'います',
            '今した': 'ました',
            
            # 話し言葉の整理
            'えー': '',
            'あの': '',
            'えっと': '',
            'うーん': '',
            'そうですね': '',
            'なんか': '',
            'みたいな感じ': '',
            'という感じ': '',
        }
    
    def clean_text(self, text):
        """テキストのクリーニング"""
        # 基本的な誤認識修正
        for wrong, correct in self.patterns.items():
            text = text.replace(wrong, correct)
        
        # 重複表現の削除
        text = re.sub(r'という+', 'という', text)
        text = re.sub(r'やっ+て', 'やって', text)
        text = re.sub(r'それ+', 'それ', text)
        
        # 読点の最適化
        text = re.sub(r'、+', '、', text)
        text = re.sub(r'。+', '。', text)
        
        # 文の整理
        text = re.sub(r'([です|ます])、', r'\1', text)
        text = re.sub(r'([と|で|に|を|が|は])、', r'\1', text)
        
        # 不要な記号の削除
        text = re.sub(r'^[、。\s]+', '', text)
        text = re.sub(r'[、。\s]+$', '', text)
        
        return text.strip()

class ArticleFormatter:
    """記事フォーマッター"""
    
    def __init__(self):
        self.max_intro_chars = 200
        self.max_main_chars = 2000
        self.max_conclusion_chars = 300
    
    def format_as_article(self, text):
        """テキストを記事形式に整形"""
        # 文章を分割
        sentences = [s.strip() for s in text.split('。') if s.strip() and len(s.strip()) > 5]
        
        if not sentences:
            return "記事の生成に失敗しました。"
        
        # 各セクションを作成
        intro = self._create_intro(sentences[:3])
        main = self._create_main(sentences[3:-2] if len(sentences) > 5 else sentences[1:-1])
        conclusion = self._create_conclusion(sentences[-2:])
        
        # 記事の構成
        article = f"マナミです。\n\n{intro}\n\n{main}\n\n{conclusion}"
        
        return article
    
    def _create_intro(self, sentences):
        """導入部の作成"""
        intro = ""
        char_count = 0
        
        for sentence in sentences:
            if char_count + len(sentence) + 1 <= self.max_intro_chars:
                intro += sentence + "。"
                char_count += len(sentence) + 1
            else:
                break
        
        if not intro.startswith(('今日は', '最近', 'さて')):
            intro = f"今日は{intro}"
        
        return intro
    
    def _create_main(self, sentences):
        """メイン部分の作成"""
        main = ""
        char_count = 0
        
        for sentence in sentences:
            if char_count + len(sentence) + 1 <= self.max_main_chars:
                main += sentence + "。"
                char_count += len(sentence) + 1
            else:
                break
        
        # 段落分けを追加
        if len(main) > 400:
            mid_point = len(main) // 2
            main = main[:mid_point] + "\n\n" + main[mid_point:]
        
        return main
    
    def _create_conclusion(self, sentences):
        """結論部の作成"""
        conclusion = ""
        char_count = 0
        
        for sentence in sentences:
            if char_count + len(sentence) + 1 <= self.max_conclusion_chars:
                conclusion += sentence + "。"
                char_count += len(sentence) + 1
        
        if not any(ending in conclusion for ending in ['ありがとう', 'ました']):
            conclusion += "\n\n今日も読んでいただき、ありがとうございました。"
        
        return conclusion

class AudioTranscriber:
    """音声文字起こしシステム"""
    
    def __init__(self, model_name="medium"):
        self.model_name = model_name
        self.model = None
        self.text_cleaner = TextCleaner()
        self.article_formatter = ArticleFormatter()
    
    def load_model(self):
        """Whisperモデルの読み込み"""
        if not WHISPER_AVAILABLE:
            raise ImportError("Whisperが利用できません")
        
        if self.model is None:
            print(f"🤖 Whisperモデル ({self.model_name}) を読み込み中...")
            try:
                self.model = whisper.load_model(self.model_name)
                print("✅ モデルの読み込み完了")
            except Exception as e:
                print(f"❌ モデル読み込みエラー: {e}")
                raise
    
    def convert_to_wav(self, input_path):
        """音声ファイルをWAVに変換"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                output_path = temp_file.name
            
            cmd = [
                'ffmpeg', '-i', input_path, 
                '-acodec', 'pcm_s16le', 
                '-ar', '16000', 
                '-ac', '1', 
                output_path, '-y'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 音声変換完了")
                return output_path
            else:
                print(f"⚠️ 音声変換に失敗: {result.stderr}")
                return input_path
                
        except Exception as e:
            print(f"❌ 音声変換エラー: {e}")
            return input_path
    
    def transcribe_audio(self, audio_path):
        """音声の文字起こし"""
        try:
            self.load_model()
            print("🗣️ 音声を文字起こし中...")
            
            # 音声ファイルの変換
            file_ext = Path(audio_path).suffix.lower()
            if file_ext not in ['.wav', '.mp3', '.m4a']:
                print("⚠️ サポートされていない音声形式です")
                return None
            
            if file_ext != '.wav':
                audio_path = self.convert_to_wav(audio_path)
            
            # Whisperで文字起こし
            result = self.model.transcribe(audio_path, language="ja")
            transcript = result["text"]
            
            print(f"✅ 文字起こし完了 ({len(transcript)}文字)")
            return transcript
            
        except Exception as e:
            print(f"❌ 文字起こしエラー: {e}")
            return None
    
    def process_audio_file(self, audio_path):
        """音声ファイルの処理"""
        if not os.path.exists(audio_path):
            print(f"❌ ファイルが見つかりません: {audio_path}")
            return None, None
        
        # 文字起こし
        transcript = self.transcribe_audio(audio_path)
        if not transcript:
            return None, None
        
        # テキストクリーニング
        cleaned_text = self.text_cleaner.clean_text(transcript)
        
        # 記事フォーマット
        article = self.article_formatter.format_as_article(cleaned_text)
        
        return transcript, article

def print_banner():
    """バナー表示"""
    print("🎙️" + "="*60)
    print("    音声記事化システム v4.0 - 完全改良版")
    print("    🚀 Whisper自動インストール対応")
    print("    📝 安定した音声記事化を実現")
    print("="*62)
    print()

def display_results(transcript, article, filename):
    """結果の表示"""
    print("\n" + "="*70)
    print("✨ 処理完了！")
    print("="*70)
    print(f"📁 ファイル: {filename}")
    print(f"📝 文字起こし: {len(transcript)}文字")
    print(f"📰 記事: {len(article)}文字")
    print("="*70)
    
    print("\n📰 完成記事:")
    print("-" * 70)
    print(article)
    print("-" * 70)
    
    # クリップボードにコピー
    if PYPERCLIP_AVAILABLE:
        try:
            pyperclip.copy(article)
            print("\n📋 記事をクリップボードにコピーしました！")
        except Exception as e:
            print(f"⚠️ クリップボードコピーエラー: {e}")
    
    # ファイル保存
    save_option = input("\n💾 結果をファイルに保存しますか？ (y/N): ").lower().strip()
    if save_option in ['y', 'yes']:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 文字起こしファイル
            transcript_file = f"{timestamp}_transcript.txt"
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"✅ 文字起こし保存: {transcript_file}")
            
            # 記事ファイル
            article_file = f"{timestamp}_article.txt"
            with open(article_file, 'w', encoding='utf-8') as f:
                f.write(article)
            print(f"✅ 記事保存: {article_file}")
            
        except Exception as e:
            print(f"❌ ファイル保存エラー: {e}")

def clean_file_path(file_path):
    """ファイルパスのクリーニング"""
    file_path = file_path.strip('"').strip("'").strip()
    file_path = file_path.replace('\\ ', ' ')
    file_path = file_path.replace('\\~', '~')
    file_path = file_path.replace('\\(', '(')
    file_path = file_path.replace('\\)', ')')
    file_path = file_path.replace('\\&', '&')
    
    file_path = os.path.expanduser(file_path)
    file_path = os.path.abspath(file_path)
    
    return file_path

def main():
    """メイン関数"""
    print_banner()
    
    if not WHISPER_AVAILABLE:
        print("❌ Whisperが利用できません")
        print("💡 手動インストール: pip install openai-whisper")
        return
    
    transcriber = AudioTranscriber()
    
    print("💡 使用方法:")
    print("   📁 音声ファイルをドラッグ&ドロップ")
    print("   📝 ファイルパスを直接入力")
    print("   🔄 'q'で終了")
    print()
    
    while True:
        try:
            file_path = input("🎙️ 音声ファイル: ").strip()
            
            if file_path.lower() in ['q', 'quit', 'exit']:
                print("👋 終了します")
                break
            
            file_path = clean_file_path(file_path)
            
            if not file_path:
                print("⚠️ ファイルパスを入力してください")
                continue
            
            if not os.path.exists(file_path):
                print(f"❌ ファイルが見つかりません: {file_path}")
                continue
            
            transcript, article = transcriber.process_audio_file(file_path)
            
            if transcript and article:
                display_results(transcript, article, Path(file_path).name)
            
            # 続行確認
            continue_option = input("\n🔄 別のファイルを処理しますか？ (y/N): ").lower().strip()
            if continue_option not in ['y', 'yes']:
                break
                
        except KeyboardInterrupt:
            print("\n👋 終了します")
            break
        except Exception as e:
            print(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()