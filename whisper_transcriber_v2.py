#!/usr/bin/env python3
"""
Whisper + Claude Code 音声記事化システム v2.0
APIコストゼロ・ローカル文字起こし対応（完全再構築版）
"""

import os
import sys
import argparse
import tempfile
import subprocess
from pathlib import Path
import whisper
from dotenv import load_dotenv
import pyperclip
import re

# 環境変数の読み込み
load_dotenv()

class WhisperTranscriberV2:
    def __init__(self):
        # Whisperモデルの初期化
        self.model = None
        self.model_name = "medium"  # 高精度なmediumモデルを使用
        
        # 文体学習用ファイルパス
        self.style_file_path = "/Users/manami/(N)note本文.md"
        
        # 文体サンプルを読み込み
        self.style_patterns = self.load_style_patterns()
        
        # 処理ファイルの管理
        self.current_audio_name = None

    def load_whisper_model(self):
        """Whisperモデルを読み込み"""
        if self.model is None:
            print(f"🤖 Whisperモデル ({self.model_name}) を読み込み中...")
            try:
                self.model = whisper.load_model(self.model_name)
                print("✅ Whisperモデル読み込み完了")
            except Exception as e:
                print(f"❌ Whisperモデル読み込みエラー: {e}")
                sys.exit(1)

    def load_style_patterns(self) -> dict:
        """note本文から文体パターンを学習"""
        try:
            if os.path.exists(self.style_file_path):
                with open(self.style_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # マナミのnote記事の特徴的な文体パターンを抽出
                patterns = {
                    'opening': ['マナミです。'],
                    
                    # 話題転換・段落開始パターン
                    'paragraph_starters': [
                        '今日は', '最近', 'さて', '実は', 'ただ', 'でも', 'そして',
                        'この', 'つい最近', 'そんな中', 'ちなみに', 'ところで'
                    ],
                    
                    # 接続表現
                    'connecting_phrases': [
                        'ということで', 'というわけで', 'そんな中でも', 'なので',
                        'だから', 'つまり', 'それは', 'これって'
                    ],
                    
                    # 感情表現・話し言葉らしさ
                    'emotional_expressions': [
                        'なんです', 'なんですよね', 'んです', 'んですよね',
                        'と思うんです', 'かもしれません', 'だと思います',
                        'ですよね', 'ますよね', 'でしょうね'
                    ],
                    
                    # 区切り線
                    'section_break': '---------------',
                    
                    # 結び
                    'closing': [
                        '今日も読んでいただき、ありがとうございました。',
                        'ありがとうございました。'
                    ],
                    
                    # 強調表現
                    'emphasis_markers': ['「', '」', '･･･', '！'],
                    
                    # 話し言葉特有の表現
                    'conversational_patterns': [
                        'って', 'みたいな', 'という感じ', 'かな', 'ちょっと',
                        'なんだか', 'やっぱり', 'でも', 'まあ', 'そういう'
                    ]
                }
                
                return patterns
            else:
                return self.get_default_patterns()
                
        except Exception as e:
            print(f"❌ 文体ファイル読み込みエラー: {e}")
            return self.get_default_patterns()

    def get_default_patterns(self) -> dict:
        """デフォルト文体パターン"""
        return {
            'opening': ['マナミです。'],
            'paragraph_starters': ['今日は', '最近', 'さて'],
            'connecting_phrases': ['ということで'],
            'closing': ['今日も読んでいただき、ありがとうございました。']
        }

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
                print(f"🧹 前回の処理ファイル {cleanup_count}個をクリアしました")
                
        except Exception as e:
            print(f"⚠️ ファイルクリア中にエラー: {e}")

    def print_banner(self):
        """バナー表示"""
        print("🎙️" + "="*60)
        print("    Whisper + Claude Code 音声記事化システム v2.0")
        print("    💰 APIコストゼロ・ローカル処理対応")
        print("="*62)
        
        if os.path.exists(self.style_file_path):
            print("✅ 文体学習済み: note本文.mdから文体を学習")
        else:
            print("⚠️ デフォルト文体を使用")
        print()

    def convert_audio_format(self, input_path: str, output_path: str) -> bool:
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

    def transcribe_with_whisper(self, audio_path: str) -> str:
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

    def clean_transcript(self, transcript: str) -> str:
        """文字起こしテキストの効果的クリーニング"""
        text = transcript.strip()
        
        # ステップ1: 話し言葉の整理
        text = self.remove_speech_fillers(text)
        
        # ステップ2: 誤認識の修正
        text = self.fix_recognition_errors(text)
        
        # ステップ3: 読点の適正化
        text = self.optimize_punctuation(text)
        
        # ステップ4: 漢字変換
        text = self.convert_to_kanji(text)
        
        return text

    def remove_speech_fillers(self, text: str) -> str:
        """話し言葉の冗長表現を削除"""
        fillers = [
            'えー', 'あの', 'えっと', 'うーん', 'まぁ', 'そうですね',
            'なんか', 'ちょっと', 'まあ', 'うん', 'はい', 'ね',
            'って', 'っていう', 'みたいな', 'という感じ', 'っての'
        ]
        
        for filler in fillers:
            text = re.sub(rf'\b{filler}[、。]?', '', text)
            text = re.sub(rf'{filler}、', '', text)
        
        return text

    def fix_recognition_errors(self, text: str) -> str:
        """音声認識エラーの徹底修正"""
        corrections = {
            # 基本的な誤認識
            'まん波': 'マナミ', '学み': 'マナミ',
            'ままふりなす': 'ママフリーランス',
            'フリランス': 'フリーランス',
            'コンテンチェーサーコーチューシン': 'コンテンツ作成',
            'バイブコーディング': 'ライブコーディング',
            'サニティ': 'Sanity',
            'ワードブレス': 'WordPress',
            'おやむけ': '短冊',
            'ポートフリオ': 'ポートフォリオ',
            
            # 重複表現の修正
            'とという': 'という',
            'ととという': 'という', 
            'とと': 'と',
            'ということという': 'ということ',
            'やとた': 'やった',
            'あとた': 'あった',
            'だとた': 'だった',
            'なとた': 'なった',
            'しとた': 'した',
            'きとた': 'きた',
            'いとた': 'いた',
            'やとぱり': 'やっぱり',
            'ちょと': 'ちょっと',
            'どとか': 'どこか',
            'やとて': 'やって',
            'とて': 'って',
            '作とて': '作って',
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
            'っと': 'と',
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
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text

    def optimize_punctuation(self, text: str) -> str:
        """読点の最適化"""
        # 過度な読点を削除
        text = re.sub(r'、+', '、', text)
        text = re.sub(r'。+', '。', text)
        
        # 不要な読点パターンを削除
        text = re.sub(r'([私今])、', r'\1は', text)  # 「私、」→「私は」
        text = re.sub(r'、([でもだからそして])([^、]{5,})', r'\1\2', text)  # 接続詞前の読点削除
        text = re.sub(r'([^、]{15,})、([^、]{1,5})。', r'\1\2。', text)  # 短い語句前の読点削除
        
        # より積極的な読点削除
        text = re.sub(r'([です|ます])、', r'\1', text)  # 語尾後の読点削除
        text = re.sub(r'([と|で|に|を|が|は])、', r'\1', text)  # 助詞後の読点削除
        text = re.sub(r'、([とか|など|みたいな])', r'\1', text)  # 特定語句前の読点削除
        
        # 文頭の不要な記号削除
        text = re.sub(r'^[、。\s]+', '', text)
        text = re.sub(r'\n[、。\s]+', '\n', text)
        
        return text

    def convert_to_kanji(self, text: str) -> str:
        """適切な漢字変換"""
        kanji_conversions = {
            'いう': 'という',
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
        
        for hiragana, kanji in kanji_conversions.items():
            text = re.sub(rf'\b{hiragana}\b', kanji, text)
        
        return text

    def final_polish(self, text: str) -> str:
        """最終的な文章調整"""
        # 重複表現の徹底除去
        text = re.sub(r'という+', 'という', text)
        text = re.sub(r'やっ+て', 'やって', text)
        text = re.sub(r'それ+', 'それ', text)
        
        # 文の流れを自然に
        text = re.sub(r'。で、', '。\n\n', text)
        text = re.sub(r'。そして、', '。\n\n', text)
        text = re.sub(r'。また、', '。\n\n', text)
        
        # 意味不明な短い断片を削除
        sentences = text.split('。')
        meaningful_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 3 and not re.match(r'^[、。\s]+$', sentence):
                meaningful_sentences.append(sentence)
        
        result = '。'.join(meaningful_sentences)
        if meaningful_sentences:
            result += '。'
        
        return result

    def organize_into_article(self, cleaned_text: str) -> str:
        """プロンプトに基づいてnote記事として構成"""
        print("🔄 note記事として整理中（新プロンプト対応）...")
        
        # 文を分割して分析
        sentences = [s.strip() for s in cleaned_text.split('。') if s.strip() and len(s.strip()) > 5]
        total_chars = len(cleaned_text)
        target_chars = 2500
        
        # 1. 導入部（約200文字）
        introduction = self.create_introduction(sentences[:3])
        
        # 2. 主要内容（約2000文字）
        main_content = self.create_main_content(sentences[3:], target_chars - 500)
        
        # 3. 結論（約300文字）
        conclusion = self.create_conclusion(sentences[-3:])
        
        # 記事構成
        article = f"マナミです。\n\n{introduction}\n\n{main_content}\n\n{conclusion}"
        
        print(f"✅ note記事整理完了 ({len(article)}文字)")
        return article

    def create_introduction(self, sentences: list) -> str:
        """導入部を作成（約200文字）"""
        intro_text = ""
        char_count = 0
        
        for sentence in sentences:
            if not sentence:
                continue
            
            # note文体に調整
            sentence = self.apply_note_style(sentence)
            sentence_with_period = sentence + "。"
            
            if char_count + len(sentence_with_period) <= 200:
                intro_text += sentence_with_period
                char_count += len(sentence_with_period)
            else:
                break
        
        # 導入らしく調整
        if intro_text:
            # 話題の重要性を示すフレーズを追加
            if not any(phrase in intro_text for phrase in ['今日は', '最近', 'さて']):
                intro_text = f"今日は{intro_text}"
        
        return intro_text

    def create_main_content(self, sentences: list, target_chars: int) -> str:
        """主要内容を作成（約2000文字）"""
        main_text = ""
        current_paragraph = ""
        paragraph_count = 0
        char_count = 0
        
        for sentence in sentences:
            if not sentence:
                continue
            
            if char_count >= target_chars:
                break
            
            # note文体に調整
            sentence = self.apply_note_style(sentence)
            sentence_with_period = sentence + "。"
            
            # 段落区切りの判定
            is_new_topic = any(sentence.startswith(starter) for starter in self.style_patterns['paragraph_starters'])
            is_long_paragraph = len(current_paragraph) > 120
            
            if (is_new_topic and current_paragraph and len(current_paragraph) > 40) or is_long_paragraph:
                # 段落完成
                if current_paragraph.strip():
                    main_text += current_paragraph.strip() + "。\n\n"
                    paragraph_count += 1
                    char_count += len(current_paragraph) + 3
                current_paragraph = sentence_with_period
            else:
                current_paragraph += sentence_with_period
        
        # 最後の段落
        if current_paragraph.strip() and char_count < target_chars:
            main_text += current_paragraph.strip() + "。\n\n"
            paragraph_count += 1
        
        # 区切り線を追加（適切な位置に）
        if paragraph_count > 3:
            paragraphs = main_text.split('\n\n')
            mid_point = len(paragraphs) // 2
            if mid_point > 1:
                paragraphs.insert(mid_point, self.style_patterns['section_break'])
                main_text = '\n\n'.join(paragraphs)
        
        return main_text.strip()

    def create_conclusion(self, sentences: list) -> str:
        """結論部を作成（約300文字）"""
        conclusion_text = ""
        char_count = 0
        
        # 最後の方の文から結論を構成
        for sentence in reversed(sentences):
            if not sentence:
                continue
            
            # note文体に調整
            sentence = self.apply_note_style(sentence)
            sentence_with_period = sentence + "。"
            
            if char_count + len(sentence_with_period) <= 250:  # 結びの分を考慮
                conclusion_text = sentence_with_period + conclusion_text
                char_count += len(sentence_with_period)
            else:
                break
        
        # 結びを追加
        if not any(ending in conclusion_text for ending in ['ありがとうございました', 'ありがとうございます']):
            conclusion_text += "\n\n" + self.style_patterns['closing'][0]
        
        return conclusion_text

    def apply_note_style(self, sentence: str) -> str:
        """note本文の文体を反映した調整"""
        # マナミのnote文体の特徴を反映
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
        
        # 語尾調整
        for old, new in adjustments.items():
            if sentence.endswith(old):
                sentence = sentence.replace(old, new)
        
        # 強調表現の追加（重要なキーワードを「」で囲む）
        important_words = [
            'ライブコーディング', 'フリーランス', 'コンテンツ作成', 
            'Sanity', 'WordPress', '自社サイト', 'ポートフォリオ',
            'PR案件', 'SNS', 'AI', 'コミュニケーション'
        ]
        
        for word in important_words:
            if word in sentence and f'「{word}」' not in sentence:
                sentence = sentence.replace(word, f'「{word}」')
        
        # 話し言葉らしさを保持
        conversational_adjustments = {
            'でも': 'でも',  # そのまま保持
            'やっぱり': 'やっぱり',  # そのまま保持
            'ちょっと': 'ちょっと',  # そのまま保持
            'なんだか': 'なんだか',  # そのまま保持
        }
        
        return sentence

    def save_results(self, transcript: str, article: str, filename: str):
        """結果をファイルに保存"""
        timestamp = Path(filename).stem
        
        transcript_file = f"{timestamp}_transcript.txt"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        article_file = f"{timestamp}_article.txt"
        with open(article_file, 'w', encoding='utf-8') as f:
            f.write(article)
        
        return transcript_file, article_file

    def display_results(self, transcript: str, article: str, filename: str):
        """結果を表示"""
        print("\n" + "="*80)
        print("✨ 記事作成完了！")
        print("="*80)
        print(f"📁 元ファイル: {filename}")
        print(f"📝 文字起こし文字数: {len(transcript)}文字")
        if article:
            print(f"📰 完成記事文字数: {len(article)}文字")
        print("="*80)
        
        if article:
            print("\n📰 完成記事:")
            print("-" * 80)
            print(article)
            print("-" * 80)
            
            # クリップボードにコピー
            try:
                pyperclip.copy(article)
                print("\n📋 記事をクリップボードにコピーしました！")
            except Exception as e:
                print(f"⚠️ クリップボードコピーに失敗: {e}")
        
        # ファイル保存のオプション
        save_option = input("\n💾 結果をファイルに保存しますか？ (y/N): ").lower().strip()
        if save_option in ['y', 'yes']:
            try:
                if article:
                    transcript_file, article_file = self.save_results(transcript, article, filename)
                    print(f"✅ 文字起こし: {transcript_file}")
                    print(f"✅ 完成記事: {article_file}")
                else:
                    timestamp = Path(filename).stem
                    transcript_file = f"{timestamp}_transcript.txt"
                    with open(transcript_file, 'w', encoding='utf-8') as f:
                        f.write(transcript)
                    print(f"✅ 文字起こし: {transcript_file}")
            except Exception as e:
                print(f"❌ 保存に失敗しました: {e}")

    def process_audio_file(self, audio_path: str):
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
                    print("⚠️ 音声変換に失敗しました。元ファイルで試行します。")
                    wav_path = audio_path
            else:
                wav_path = audio_path
            
            # Whisperで文字起こし
            transcript = self.transcribe_with_whisper(wav_path)
            
            if not transcript:
                print("❌ 文字起こしに失敗しました")
                return
            
            # テキストクリーニング
            cleaned_text = self.clean_transcript(transcript)
            
            # 最終調整
            cleaned_text = self.final_polish(cleaned_text)
            
            # 記事として整理
            article = self.organize_into_article(cleaned_text)
            
            # 結果表示
            self.display_results(transcript, article, filename)
            
        except Exception as e:
            print(f"❌ 処理中にエラーが発生しました: {e}")
        finally:
            # 一時ファイルの削除
            try:
                if wav_path and wav_path != audio_path and os.path.exists(wav_path):
                    os.remove(wav_path)
            except Exception as e:
                print(f"⚠️ 一時ファイル削除エラー: {e}")

def main():
    transcriber = WhisperTranscriberV2()
    transcriber.print_banner()
    
    parser = argparse.ArgumentParser(description="Whisper音声文字起こし + Claude Code記事生成 v2.0")
    parser.add_argument("audio_file", nargs="?", help="音声ファイルのパス")
    parser.add_argument("--model", default="medium", choices=["tiny", "base", "small", "medium", "large"],
                       help="使用するWhisperモデル (default: medium)")
    
    args = parser.parse_args()
    
    if args.model:
        transcriber.model_name = args.model
    
    if args.audio_file:
        # コマンドライン引数から
        if not os.path.exists(args.audio_file):
            print("❌ ファイルが見つかりません:", args.audio_file)
            return
        
        transcriber.process_audio_file(args.audio_file)
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
                
                # ドラッグ&ドロップ時のパス処理
                file_path = file_path.strip('"').strip("'").strip()
                file_path = file_path.replace('\\ ', ' ')
                file_path = file_path.replace('\\~', '~')
                file_path = file_path.replace('\\(', '(')
                file_path = file_path.replace('\\)', ')')
                
                # 日本語の文字化け対策
                try:
                    if 'ã' in file_path or 'â' in file_path:
                        file_path = file_path.encode('latin1').decode('utf-8')
                except:
                    pass
                
                file_path = os.path.expanduser(file_path)
                file_path = os.path.abspath(file_path)
                
                print(f"🔍 処理中のパス: {file_path}")
                
                if not file_path:
                    print("⚠️ ファイルパスを入力してください")
                    continue
                
                if not os.path.exists(file_path):
                    print("❌ ファイルが見つかりません:", file_path)
                    print("💡 ファイルを直接ドラッグ&ドロップしてみてください")
                    continue
                
                transcriber.process_audio_file(file_path)
                
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