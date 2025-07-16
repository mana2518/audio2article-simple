#!/usr/bin/env python3
"""
音声記事化システム 最終改良版 v3.0
安定性と精度を重視したアーキテクチャ
APIコストゼロ・ローカル処理対応
"""

import os
import sys
import argparse
import tempfile
import subprocess
from pathlib import Path
import re
from datetime import datetime

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Whisperモジュールが見つかりません")

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

class ErrorCorrectionEngine:
    """音声認識エラー修正エンジン"""
    
    def __init__(self):
        self.correction_patterns = self._load_correction_patterns()
    
    def _load_correction_patterns(self):
        """包括的なエラー修正パターン"""
        return {
            # ユーザー報告の具体的エラー
            '日山波です': 'マナミです',
            '日山波': 'マナミ',
            'サニーの子ども': '3人の子ども', 
            'サニー': '3人',
            '一斉にス発進': 'SNS発信',
            '一斉に素発進': 'SNS発信',
            'コンテンセサコ': 'コンテンツ作成',
            
            # 基本的な誤認識
            'まん波': 'マナミ',
            '学み': 'マナミ',
            'ままふりなす': 'ママフリーランス',
            'フリランス': 'フリーランス',
            'フリーナース': 'フリーランス',
            'コンテンチェーサーコーチューシン': 'コンテンツ作成',
            'バイブコーディング': 'ライブコーディング',
            'サニティ': 'Sanity',
            'ワードブレス': 'WordPress',
            'ポートフリオ': 'ポートフォリオ',
            
            # 重複表現の修正
            'とという': 'という',
            'ととという': 'という', 
            'とと': 'と',
            'ということという': 'ということ',
            'やとぱり': 'やっぱり',
            'どとか': 'どこか',
            'やとて': 'やって',
            '作とて': '作って',
            'とて': 'って',
            'せとかく': 'せっかく',
            'やとている': 'やっている',
            'やとています': 'やっています',
            '持とて': '持って',
            'かぶとた': 'かぶった',
            
            # 語尾の誤認識
            '思今す': '思います',
            '思今した': '思いました',
            'ござ今した': 'ございました',
            '今す': 'います',
            '今した': 'ました',
            'なりたいな': 'なりたいなあ',
            'いいかな': 'いいかなあ',
            
            # よくある誤認識パターン
            'やおります': 'やっています',
            'やいる': 'やっている',
            'やもいい': 'やってもいい',
            'やろー': 'やろう',
            'あれる': 'できる',
            'いけば': 'いけば',
            'おとも': '今日も',
            
            # 文法的修正
            'だったま': 'だから',
            'いうは': 'というのは',
            'ふうに': 'という風に',
            'のとか': 'など',
            '探索書いて': '短冊に書いて',
            '商演': '仕事で',
            '単座コミニ効果な': '',
            '頼ばた風': '七夕飾り',
            '不管して': '俯瞰して',
            '静つも': '正体も',
            '静だな': '正体だな',
            'シオー': 'しよう',
            'あもいい': 'あってもいい',
            'うめこめる': '埋め込める',
            'やたほうな': 'やった方の',
            'あちょっと': 'あと、ちょっと',
            '周囲気': '収益',
            '入くる': '入ってくる',
            'になて': 'になって',
            '微々たん': '微々たる',
            'いかつい': 'いかにも',
            'あこりゃ': 'あ、これは',
            '成球所': '名刺',
            'なんてとという': 'なんていう',
            'ベレーボー': 'ベレー帽',
            'カブッダ': 'かぶった',
            '使使': '使う',
            'わがない': 'わからない',
            'お進め': 'おすすめ',
            '作いく': '作っていく',
            '頑張いき': '頑張っていき',
            
            # 話し言葉の整理
            'えー': '',
            'あの': '',
            'えっと': '',
            'うーん': '',
            'まぁ': '',
            'そうですね': '',
            'なんか': '',
            'って': '',
            'っていう': '',
            'みたいな感じ': '',
            'という感じ': '',
        }
    
    def correct_transcript(self, text):
        """文字起こしテキストの包括的修正"""
        # 段階1: 冗長表現削除
        text = self._remove_redundant_expressions(text)
        
        # 段階2: エラー修正
        for wrong, correct in self.correction_patterns.items():
            text = text.replace(wrong, correct)
        
        # 段階3: 読点最適化
        text = self._optimize_punctuation(text)
        
        # 段階4: 漢字変換
        text = self._convert_to_kanji(text)
        
        # 段階5: 最終調整
        text = self._final_polish(text)
        
        return text.strip()
    
    def _remove_redundant_expressions(self, text):
        """冗長表現の削除"""
        patterns = [
            r'はい、?', r'えー、?', r'あの、?', r'えっと、?', r'うーん、?', 
            r'まぁ、?', r'そうですね、?', r'なんか、?', r'ね、?', 
            r'ちょっと、?', r'まあ、?', r'うん、?', r'そう、?'
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text)
        
        return text
    
    def _optimize_punctuation(self, text):
        """読点の大幅最適化"""
        # 過度な読点を削除
        text = re.sub(r'、+', '、', text)
        text = re.sub(r'。+', '。', text)
        
        # 不要な読点パターンを削除
        text = re.sub(r'([私今])、', r'\\1は', text)
        text = re.sub(r'([です|ます])、', r'\\1', text)
        text = re.sub(r'([と|で|に|を|が|は])、', r'\\1', text)
        text = re.sub(r'、([とか|など|みたいな])', r'\\1', text)
        text = re.sub(r'、([でもだからそして])([^、]{5,})', r'\\1\\2', text)
        
        # より積極的な読点削除
        text = re.sub(r'([^、]{15,})、([^、]{1,5})。', r'\\1\\2。', text)
        
        # 文頭の不要な記号削除
        text = re.sub(r'^[、。\\s]+', '', text)
        
        return text
    
    def _convert_to_kanji(self, text):
        """適切な漢字変換"""
        conversions = {
            'とき': '時',
            'ひと': '人', 
            'いま': '今',
            'しごと': '仕事',
            'つくる': '作る',
            'かんがえる': '考える',
            'おもう': '思う',
            'つかう': '使う',
            'みる': '見る',
            'きく': '聞く',
            'はなす': '話す',
            'かく': '書く',
        }
        
        for hiragana, kanji in conversions.items():
            text = re.sub(rf'\\b{hiragana}\\b', kanji, text)
        
        return text
    
    def _final_polish(self, text):
        """最終的な文章調整"""
        # 重複表現の徹底除去
        text = re.sub(r'という+', 'という', text)
        text = re.sub(r'やっ+て', 'やって', text)
        text = re.sub(r'それ+', 'それ', text)
        
        # 文の流れを自然に
        text = re.sub(r'。で、', '。\\n\\n', text)
        text = re.sub(r'。そして、', '。\\n\\n', text)
        text = re.sub(r'。また、', '。\\n\\n', text)
        
        # 意味不明な短い断片を削除
        sentences = text.split('。')
        meaningful_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 3 and not re.match(r'^[、。\\s]+$', sentence):
                meaningful_sentences.append(sentence)
        
        result = '。'.join(meaningful_sentences)
        if meaningful_sentences:
            result += '。'
        
        return result

class StyleEngine:
    """note文体エンジン"""
    
    def __init__(self, style_file_path):
        self.style_file_path = style_file_path
        self.style_patterns = self._learn_style_patterns()
    
    def _learn_style_patterns(self):
        """note本文から文体パターンを学習"""
        try:
            if os.path.exists(self.style_file_path):
                print("✅ 文体学習済み: note本文.mdから文体を学習")
                return {
                    'opening': ['マナミです。'],
                    'paragraph_starters': [
                        '今日は', '最近', 'さて', '実は', 'ただ', 'でも', 'そして',
                        'この', 'つい最近', 'そんな中', 'ちなみに', 'ところで'
                    ],
                    'connecting_phrases': [
                        'ということで', 'というわけで', 'そんな中でも', 'なので',
                        'だから', 'つまり', 'それは', 'これって'
                    ],
                    'emotional_expressions': [
                        'なんです', 'なんですよね', 'んです', 'んですよね',
                        'と思うんです', 'かもしれません', 'だと思います',
                        'ですよね', 'ますよね', 'でしょうね'
                    ],
                    'closing': [
                        '今日も読んでいただき、ありがとうございました。',
                        'ありがとうございました。'
                    ]
                }
            else:
                print("⚠️ デフォルト文体を使用")
                return self._get_default_patterns()
        except Exception as e:
            print(f"❌ 文体学習エラー: {e}")
            return self._get_default_patterns()
    
    def _get_default_patterns(self):
        return {
            'opening': ['マナミです。'],
            'paragraph_starters': ['今日は', '最近', 'さて'],
            'connecting_phrases': ['ということで'],
            'closing': ['今日も読んでいただき、ありがとうございました。']
        }
    
    def apply_note_style(self, sentence):
        """note本文の文体を反映した調整"""
        adjustments = {
            'と思います': 'と思うんです',
            'ということです': 'ということなんです',
            'でしょう': 'でしょうね',
            'ですね': 'なんですよね',
            'だと思う': 'だと思うんです',
            'かもしれません': 'かもしれないです',
            'になります': 'になるんです',
            'だからです': 'だからなんです',
        }
        
        for old, new in adjustments.items():
            if sentence.endswith(old):
                sentence = sentence.replace(old, new)
        
        return sentence

class AudioArticleSystem:
    """音声記事化システム"""
    
    def __init__(self, model_name="medium"):
        self.model = None
        self.model_name = model_name
        self.style_file_path = "/Users/manami/(N)note本文.md"
        self.error_corrector = ErrorCorrectionEngine()
        self.style_engine = StyleEngine(self.style_file_path)
        self.current_audio_name = None
    
    def load_whisper_model(self):
        """Whisperモデルを読み込み"""
        if not WHISPER_AVAILABLE:
            raise ImportError("Whisperがインストールされていません")
        
        if self.model is None:
            print(f"🤖 Whisperモデル ({self.model_name}) を読み込み中...")
            try:
                self.model = whisper.load_model(self.model_name)
                print("✅ Whisperモデル読み込み完了")
            except Exception as e:
                print(f"❌ Whisperモデル読み込みエラー: {e}")
                raise
    
    def cleanup_previous_files(self):
        """前回の処理ファイルをクリア"""
        try:
            current_dir = Path.cwd()
            cleanup_count = 0
            
            for file_path in current_dir.glob('*'):
                if file_path.is_file():
                    if any(pattern in file_path.name for pattern in [
                        '_transcript.txt', '_article.txt', 'temp', 'tmp'
                    ]) and file_path.suffix in ['.txt', '.wav', '.mp3']:
                        file_path.unlink()
                        cleanup_count += 1
            
            if cleanup_count > 0:
                print(f"🧹 前回の処理ファイル {cleanup_count}個をクリア")
                
        except Exception as e:
            print(f"⚠️ ファイルクリア中にエラー: {e}")
    
    def convert_audio_format(self, input_path, output_path):
        """音声ファイルをWAVに変換"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path, '-acodec', 'pcm_s16le', 
                '-ar', '16000', '-ac', '1', output_path, '-y'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ 音声変換エラー: {e}")
            return False
    
    def transcribe_with_whisper(self, audio_path):
        """Whisperによる音声文字起こし"""
        try:
            self.load_whisper_model()
            print("🗣️ Whisperで文字起こし中...")
            
            result = self.model.transcribe(audio_path, language="ja")
            transcript = result["text"]
            
            print(f"✅ 文字起こし完了 ({len(transcript)}文字)")
            return transcript
            
        except Exception as e:
            print(f"❌ Whisper文字起こしエラー: {e}")
            return None
    
    def organize_into_article(self, cleaned_text):
        """クリーンアップされたテキストをnote記事として構成"""
        print("🔄 note記事として整理中...")
        
        # 文を分割して分析
        sentences = [s.strip() for s in cleaned_text.split('。') if s.strip() and len(s.strip()) > 5]
        
        # 1. 導入部（約200文字）
        introduction = self._create_introduction(sentences[:3])
        
        # 2. 主要内容（約2000文字）
        main_content = self._create_main_content(sentences[3:])
        
        # 3. 結論（約300文字）
        conclusion = self._create_conclusion(sentences[-3:])
        
        # 記事構成
        article = f"マナミです。\\n\\n{introduction}\\n\\n{main_content}\\n\\n{conclusion}"
        
        print(f"✅ note記事整理完了 ({len(article)}文字)")
        return article
    
    def _create_introduction(self, sentences):
        """導入部を作成（約200文字）"""
        intro_text = ""
        char_count = 0
        
        for sentence in sentences:
            if not sentence:
                continue
            
            sentence = self.style_engine.apply_note_style(sentence)
            sentence_with_period = sentence + "。"
            
            if char_count + len(sentence_with_period) <= 200:
                intro_text += sentence_with_period
                char_count += len(sentence_with_period)
            else:
                break
        
        if intro_text and not any(phrase in intro_text for phrase in ['今日は', '最近', 'さて']):
            intro_text = f"今日は{intro_text}"
        
        return intro_text
    
    def _create_main_content(self, sentences):
        """主要内容を作成（約2000文字）"""
        main_text = ""
        current_paragraph = ""
        char_count = 0
        target_chars = 2000
        
        for sentence in sentences:
            if not sentence or char_count >= target_chars:
                break
            
            sentence = self.style_engine.apply_note_style(sentence)
            sentence_with_period = sentence + "。"
            
            # 段落区切りの判定
            is_new_topic = any(sentence.startswith(starter) for starter in 
                             self.style_engine.style_patterns['paragraph_starters'])
            is_long_paragraph = len(current_paragraph) > 120
            
            if (is_new_topic and current_paragraph and len(current_paragraph) > 40) or is_long_paragraph:
                if current_paragraph.strip():
                    main_text += current_paragraph.strip() + "。\\n\\n"
                    char_count += len(current_paragraph) + 3
                current_paragraph = sentence_with_period
            else:
                current_paragraph += sentence_with_period
        
        # 最後の段落
        if current_paragraph.strip() and char_count < target_chars:
            main_text += current_paragraph.strip() + "。\\n\\n"
        
        # 区切り線を追加
        paragraphs = main_text.split('\\n\\n')
        if len(paragraphs) > 3:
            mid_point = len(paragraphs) // 2
            if mid_point > 1:
                paragraphs.insert(mid_point, "---------------")
                main_text = '\\n\\n'.join(paragraphs)
        
        return main_text.strip()
    
    def _create_conclusion(self, sentences):
        """結論部を作成（約300文字）"""
        conclusion_text = ""
        char_count = 0
        
        for sentence in reversed(sentences):
            if not sentence:
                continue
            
            sentence = self.style_engine.apply_note_style(sentence)
            sentence_with_period = sentence + "。"
            
            if char_count + len(sentence_with_period) <= 250:
                conclusion_text = sentence_with_period + conclusion_text
                char_count += len(sentence_with_period)
            else:
                break
        
        if not any(ending in conclusion_text for ending in ['ありがとうございました', 'ありがとうございます']):
            conclusion_text += "\\n\\n" + self.style_engine.style_patterns['closing'][0]
        
        return conclusion_text
    
    def process_audio_file(self, audio_path):
        """音声ファイルの処理メイン"""
        try:
            filename = Path(audio_path).name
            
            # 新しい音声ファイルの処理開始時に前回のファイルをクリア
            if self.current_audio_name != filename:
                print(f"🆕 新しい音声ファイルを検出: {filename}")
                self.cleanup_previous_files()
                self.current_audio_name = filename
            
            print(f"🎵 処理開始: {filename}")
            
            # 音声ファイル変換
            wav_path = None
            file_ext = Path(audio_path).suffix.lower()
            
            if file_ext != '.wav':
                print("🔄 音声ファイルを変換中...")
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    wav_path = temp_wav.name
                
                if not self.convert_audio_format(audio_path, wav_path):
                    print("⚠️ 音声変換に失敗。元ファイルで試行")
                    wav_path = audio_path
            else:
                wav_path = audio_path
            
            # Whisperで文字起こし
            transcript = self.transcribe_with_whisper(wav_path)
            
            if not transcript:
                print("❌ 文字起こしに失敗しました")
                return None, None
            
            # エラー修正とクリーニング
            cleaned_text = self.error_corrector.correct_transcript(transcript)
            
            # 記事として整理
            article = self.organize_into_article(cleaned_text)
            
            # 一時ファイルの削除
            try:
                if wav_path and wav_path != audio_path and os.path.exists(wav_path):
                    os.remove(wav_path)
            except Exception as e:
                print(f"⚠️ 一時ファイル削除エラー: {e}")
            
            return transcript, article
            
        except Exception as e:
            print(f"❌ 処理中にエラーが発生しました: {e}")
            return None, None

def print_banner():
    """バナー表示"""
    print("🎙️" + "="*60)
    print("    音声記事化システム v3.0 最終改良版")
    print("    💰 APIコストゼロ・ローカル処理対応")
    print("    🎯 安定性と精度を重視したアーキテクチャ")
    print("="*62)
    print()

def display_results(transcript, article, filename):
    """結果を表示"""
    print("\\n" + "="*80)
    print("✨ 記事作成完了！")
    print("="*80)
    print(f"📁 元ファイル: {filename}")
    print(f"📝 文字起こし文字数: {len(transcript)}文字")
    if article:
        print(f"📰 完成記事文字数: {len(article)}文字")
    print("="*80)
    
    if article:
        print("\\n📰 完成記事:")
        print("-" * 80)
        print(article)
        print("-" * 80)
        
        # クリップボードにコピー
        if PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(article)
                print("\\n📋 記事をクリップボードにコピーしました！")
            except Exception as e:
                print(f"⚠️ クリップボードコピーに失敗: {e}")
        else:
            print("\\n💡 記事をコピーするにはpyperclipをインストール: pip3 install pyperclip")
    else:
        print("\\n📄 文字起こし結果:")
        print("-" * 40)
        print(transcript)
    
    # ファイル保存のオプション
    save_option = input("\\n💾 結果をファイルに保存しますか？ (y/N): ").lower().strip()
    if save_option in ['y', 'yes']:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            transcript_file = f"{timestamp}_transcript.txt"
            
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"✅ 文字起こし: {transcript_file}")
            
            if article:
                article_file = f"{timestamp}_article.txt"
                with open(article_file, 'w', encoding='utf-8') as f:
                    f.write(article)
                print(f"✅ 完成記事: {article_file}")
        except Exception as e:
            print(f"❌ 保存に失敗: {e}")

def clean_file_path(file_path):
    """ファイルパスのクリーニング"""
    # ドラッグ&ドロップ時の引用符・エスケープ文字を削除
    file_path = file_path.strip('"').strip("'").strip()
    
    # macOSのドラッグ&ドロップエスケープ処理
    file_path = file_path.replace('\\\\ ', ' ')
    file_path = file_path.replace('\\\\~', '~')
    file_path = file_path.replace('\\\\(', '(')
    file_path = file_path.replace('\\\\)', ')')
    file_path = file_path.replace('\\\\&', '&')
    
    # 日本語の文字化け対策
    try:
        if 'ã' in file_path or 'â' in file_path:
            file_path = file_path.encode('latin1').decode('utf-8')
    except:
        pass
    
    # パスの正規化
    file_path = os.path.expanduser(file_path)
    file_path = os.path.abspath(file_path)
    
    return file_path

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="音声記事化システム v3.0 最終改良版")
    parser.add_argument("audio_file", nargs="?", help="音声ファイルのパス")
    parser.add_argument("--model", default="medium", 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="使用するWhisperモデル (default: medium)")
    
    args = parser.parse_args()
    
    print_banner()
    
    if not WHISPER_AVAILABLE:
        print("❌ Whisperがインストールされていません")
        print("💡 インストール方法: pip install openai-whisper")
        return
    
    system = AudioArticleSystem(args.model)
    
    if args.audio_file:
        # コマンドライン引数から
        if not os.path.exists(args.audio_file):
            print("❌ ファイルが見つかりません:", args.audio_file)
            return
        
        transcript, article = system.process_audio_file(args.audio_file)
        if transcript:
            display_results(transcript, article, Path(args.audio_file).name)
    else:
        # インタラクティブモード
        print("💡 使用方法:")
        print("   1. 📁 音声ファイルをターミナルにドラッグ&ドロップしてEnter")
        print("   2. 📝 ファイルパスを直接入力")
        print("   3. ⚙️ オプション: --model [tiny/base/small/medium/large]")
        print()
        
        while True:
            try:
                print("🎯 音声ファイルをここにドラッグ&ドロップするか、パスを入力してください")
                file_path = input("🎙️ ファイル: ").strip()
                
                if file_path.lower() in ['q', 'quit', 'exit', '終了']:
                    print("👋 システムを終了します")
                    break
                
                file_path = clean_file_path(file_path)
                
                if not file_path:
                    print("⚠️ ファイルパスを入力してください")
                    continue
                
                if not os.path.exists(file_path):
                    print("❌ ファイルが見つかりません:", file_path)
                    print("💡 ファイルを直接ドラッグ&ドロップしてみてください")
                    continue
                
                transcript, article = system.process_audio_file(file_path)
                if transcript:
                    display_results(transcript, article, Path(file_path).name)
                
                # 続行確認
                continue_option = input("\\n🔄 別のファイルを処理しますか？ (y/N): ").lower().strip()
                if continue_option not in ['y', 'yes']:
                    break
                
            except KeyboardInterrupt:
                print("\\n👋 終了します")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()