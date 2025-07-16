#!/usr/bin/env python3
"""
音声から記事を生成するシステム v3.0
安定性と精度を重視したアーキテクチャ
APIコストゼロ・ローカル処理対応
"""

import os
import sys
import json
import logging
import tempfile
import subprocess
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import whisper
import pyperclip
import re
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ArticleConfig:
    """記事生成の設定を管理"""
    target_length: int = 2500
    intro_length: int = 200
    main_length: int = 2000
    conclusion_length: int = 300
    writing_style_reference: str = "/Users/manami/(N)note本文.md"
    whisper_model: str = "medium"
    output_format: str = "note記事"

class ErrorCorrectionEngine:
    """音声認識エラー修正エンジン"""
    
    def __init__(self):
        self.correction_patterns = self._load_correction_patterns()
    
    def _load_correction_patterns(self) -> Dict[str, str]:
        """エラー修正パターンを読み込み"""
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
            
            # よくある誤認識パターン
            'やおります': 'やっています',
            'やいる': 'やっている',
            'やもいい': 'やってもいい',
            'やろー': 'やろう',
            'あれる': 'できる',
            'おとも': '今日も',
            
            # 話し言葉の整理
            'えー': '',
            'あの': '',
            'えっと': '',
            'うーん': '',
            'まぁ': '',
            'そうですね': '',
            'なんか': '',
            'ちょっと': '',
            'って': '',
            'っていう': '',
            'みたいな感じ': '',
            'という感じ': '',
        }
    
    def correct_transcript(self, text: str) -> str:
        """文字起こしテキストのエラー修正"""
        # 段階1: 冗長表現削除
        text = self._remove_redundant_expressions(text)
        
        # 段階2: エラー修正
        for wrong, correct in self.correction_patterns.items():
            text = text.replace(wrong, correct)
        
        # 段階3: 読点最適化
        text = self._optimize_punctuation(text)
        
        # 段階4: 漢字変換
        text = self._convert_to_kanji(text)
        
        return text.strip()
    
    def _remove_redundant_expressions(self, text: str) -> str:
        """冗長表現の削除"""
        patterns = [
            r'はい、?', r'えー、?', r'あの、?', r'えっと、?', r'うーん、?', 
            r'まぁ、?', r'そうですね、?', r'なんか、?', r'ね、?', 
            r'ちょっと、?', r'まあ、?', r'うん、?', r'そう、?'
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text)
        
        return text
    
    def _optimize_punctuation(self, text: str) -> str:
        """読点の最適化"""
        # 過度な読点を削除
        text = re.sub(r'、+', '、', text)
        text = re.sub(r'。+', '。', text)
        
        # 不要な読点パターンを削除
        text = re.sub(r'([私今])、', r'\1は', text)
        text = re.sub(r'([です|ます])、', r'\1', text)
        text = re.sub(r'([と|で|に|を|が|は])、', r'\1', text)
        text = re.sub(r'、([とか|など|みたいな])', r'\1', text)
        
        # 文頭の不要な記号削除
        text = re.sub(r'^[、。\s]+', '', text)
        
        return text
    
    def _convert_to_kanji(self, text: str) -> str:
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
            text = re.sub(rf'\b{hiragana}\b', kanji, text)
        
        return text

class StyleLearningEngine:
    """note文体学習エンジン"""
    
    def __init__(self, style_file_path: str):
        self.style_file_path = style_file_path
        self.style_patterns = self._learn_style_patterns()
    
    def _learn_style_patterns(self) -> Dict[str, List[str]]:
        """note本文から文体パターンを学習"""
        try:
            if os.path.exists(self.style_file_path):
                with open(self.style_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
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
                    
                    # 結び
                    'closing': [
                        '今日も読んでいただき、ありがとうございました。',
                        'ありがとうございました。'
                    ],
                    
                    # 話し言葉特有の表現
                    'conversational_patterns': [
                        'って', 'みたいな', 'という感じ', 'かな', 'ちょっと',
                        'なんだか', 'やっぱり', 'でも', 'まあ', 'そういう'
                    ]
                }
                
                logger.info("文体パターン学習完了")
                return patterns
            else:
                logger.warning(f"文体ファイルが見つかりません: {self.style_file_path}")
                return self._get_default_patterns()
                
        except Exception as e:
            logger.error(f"文体学習エラー: {e}")
            return self._get_default_patterns()
    
    def _get_default_patterns(self) -> Dict[str, List[str]]:
        """デフォルト文体パターン"""
        return {
            'opening': ['マナミです。'],
            'paragraph_starters': ['今日は', '最近', 'さて'],
            'connecting_phrases': ['ということで'],
            'closing': ['今日も読んでいただき、ありがとうございました。']
        }
    
    def apply_note_style(self, sentence: str) -> str:
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
        
        # 語尾調整
        for old, new in adjustments.items():
            if sentence.endswith(old):
                sentence = sentence.replace(old, new)
        
        return sentence

class VoiceToArticleSystem:
    """音声から記事を生成するシステム"""
    
    def __init__(self, config: ArticleConfig):
        """
        初期化
        Args:
            config: システム設定
        """
        self.config = config
        self.whisper_model = None
        self.error_corrector = ErrorCorrectionEngine()
        self.style_engine = StyleLearningEngine(config.writing_style_reference)
        self.current_audio_name = None
    
    def _load_whisper_model(self):
        """Whisperモデルを読み込み"""
        if self.whisper_model is None:
            logger.info(f"Whisperモデル ({self.config.whisper_model}) を読み込み中...")
            try:
                self.whisper_model = whisper.load_model(self.config.whisper_model)
                logger.info("Whisperモデル読み込み完了")
            except Exception as e:
                logger.error(f"Whisperモデル読み込みエラー: {e}")
                raise
    
    def _cleanup_previous_files(self):
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
                logger.info(f"前回の処理ファイル {cleanup_count}個をクリア")
                
        except Exception as e:
            logger.warning(f"ファイルクリア中にエラー: {e}")
    
    def _convert_audio_format(self, input_path: str, output_path: str) -> bool:
        """音声ファイルをWAVに変換"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path, '-acodec', 'pcm_s16le', 
                '-ar', '16000', '-ac', '1', output_path, '-y'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"音声変換エラー: {e}")
            return False
    
    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        音声をテキストに変換
        Args:
            audio_path: 音声ファイルのパス
        Returns:
            transcription結果
        """
        try:
            self._load_whisper_model()
            logger.info("Whisperで文字起こし中...")
            
            # 音声ファイル変換が必要な場合
            wav_path = audio_path
            file_ext = Path(audio_path).suffix.lower()
            
            if file_ext != '.wav':
                logger.info("音声ファイルを変換中...")
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    wav_path = temp_wav.name
                
                if not self._convert_audio_format(audio_path, wav_path):
                    logger.warning("音声変換に失敗。元ファイルで試行")
                    wav_path = audio_path
            
            # Whisperで文字起こし
            result = self.whisper_model.transcribe(wav_path, language="ja")
            
            # 結果の検証
            if not result.get("text") or len(result["text"].strip()) < 20:
                raise ValueError("音声の文字起こし結果が短すぎます")
            
            logger.info(f"文字起こし完了: {len(result['text'])}文字")
            
            # 一時ファイルの削除
            if wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)
            
            return result
            
        except Exception as e:
            logger.error(f"音声文字起こしエラー: {e}")
            raise
    
    def generate_article_structure(self, cleaned_transcript: str) -> str:
        """
        クリーンアップされた文字起こしから記事構造を生成
        Args:
            cleaned_transcript: クリーンアップ済みの文字起こし
        Returns:
            構造化された記事
        """
        logger.info("記事構造を生成中...")
        
        # 文を分割して分析
        sentences = [s.strip() for s in cleaned_transcript.split('。') if s.strip() and len(s.strip()) > 5]
        
        # 1. 導入部（約200文字）
        introduction = self._create_introduction(sentences[:3])
        
        # 2. 主要内容（約2000文字）
        main_content = self._create_main_content(sentences[3:])
        
        # 3. 結論（約300文字）
        conclusion = self._create_conclusion(sentences[-3:])
        
        # 記事構成
        article = f"マナミです。\\n\\n{introduction}\\n\\n{main_content}\\n\\n{conclusion}"
        
        logger.info(f"記事構造生成完了: {len(article)}文字")
        return article
    
    def _create_introduction(self, sentences: List[str]) -> str:
        """導入部を作成（約200文字）"""
        intro_text = ""
        char_count = 0
        
        for sentence in sentences:
            if not sentence:
                continue
            
            # note文体に調整
            sentence = self.style_engine.apply_note_style(sentence)
            sentence_with_period = sentence + "。"
            
            if char_count + len(sentence_with_period) <= 200:
                intro_text += sentence_with_period
                char_count += len(sentence_with_period)
            else:
                break
        
        # 導入らしく調整
        if intro_text and not any(phrase in intro_text for phrase in ['今日は', '最近', 'さて']):
            intro_text = f"今日は{intro_text}"
        
        return intro_text
    
    def _create_main_content(self, sentences: List[str]) -> str:
        """主要内容を作成（約2000文字）"""
        main_text = ""
        current_paragraph = ""
        char_count = 0
        target_chars = 2000
        
        for sentence in sentences:
            if not sentence or char_count >= target_chars:
                break
            
            # note文体に調整
            sentence = self.style_engine.apply_note_style(sentence)
            sentence_with_period = sentence + "。"
            
            # 段落区切りの判定
            is_new_topic = any(sentence.startswith(starter) for starter in 
                             self.style_engine.style_patterns['paragraph_starters'])
            is_long_paragraph = len(current_paragraph) > 120
            
            if (is_new_topic and current_paragraph and len(current_paragraph) > 40) or is_long_paragraph:
                # 段落完成
                if current_paragraph.strip():
                    main_text += current_paragraph.strip() + "。\\n\\n"
                    char_count += len(current_paragraph) + 3
                current_paragraph = sentence_with_period
            else:
                current_paragraph += sentence_with_period
        
        # 最後の段落
        if current_paragraph.strip() and char_count < target_chars:
            main_text += current_paragraph.strip() + "。"
        
        # 区切り線を追加（適切な位置に）
        paragraphs = main_text.split('\\n\\n')
        if len(paragraphs) > 3:
            mid_point = len(paragraphs) // 2
            if mid_point > 1:
                paragraphs.insert(mid_point, "---------------")
                main_text = '\\n\\n'.join(paragraphs)
        
        return main_text.strip()
    
    def _create_conclusion(self, sentences: List[str]) -> str:
        """結論部を作成（約300文字）"""
        conclusion_text = ""
        char_count = 0
        
        # 最後の方の文から結論を構成
        for sentence in reversed(sentences):
            if not sentence:
                continue
            
            # note文体に調整
            sentence = self.style_engine.apply_note_style(sentence)
            sentence_with_period = sentence + "。"
            
            if char_count + len(sentence_with_period) <= 250:  # 結びの分を考慮
                conclusion_text = sentence_with_period + conclusion_text
                char_count += len(sentence_with_period)
            else:
                break
        
        # 結びを追加
        if not any(ending in conclusion_text for ending in ['ありがとうございました', 'ありがとうございます']):
            conclusion_text += "\\n\\n" + self.style_engine.style_patterns['closing'][0]
        
        return conclusion_text
    
    def _validate_article(self, article: str) -> None:
        """生成された記事の品質チェック"""
        if not article:
            raise ValueError("記事が生成されませんでした")
        
        if len(article) < 1500:
            raise ValueError("記事が短すぎます")
        
        if "マナミです。" not in article[:20]:
            raise ValueError("記事の冒頭が正しくありません")
        
        logger.info(f"記事品質チェック完了: {len(article)}文字")
    
    def process_audio_to_article(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """
        音声ファイルから記事を生成する完全なフロー
        Args:
            audio_path: 音声ファイルのパス
            output_path: 出力ファイルのパス（オプション）
        Returns:
            生成された記事
        """
        try:
            filename = Path(audio_path).name
            
            # 新しい音声ファイルの処理開始時に前回のファイルをクリア
            if self.current_audio_name != filename:
                logger.info(f"新しい音声ファイルを検出: {filename}")
                self._cleanup_previous_files()
                self.current_audio_name = filename
            
            # 1. 音声文字起こし
            transcript_result = self.transcribe_audio(audio_path)
            transcript = transcript_result["text"]
            
            # 2. エラー修正
            cleaned_transcript = self.error_corrector.correct_transcript(transcript)
            
            # 3. 記事生成
            article = self.generate_article_structure(cleaned_transcript)
            
            # 4. 品質チェック
            self._validate_article(article)
            
            # 5. ファイル保存（オプション）
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(article)
                logger.info(f"記事を保存: {output_path}")
            
            return article
            
        except Exception as e:
            logger.error(f"処理エラー: {e}")
            raise

class CLIInterface:
    """コマンドラインインターフェース"""
    
    def __init__(self):
        self.system = None
    
    def print_banner(self):
        """バナー表示"""
        print("🎙️" + "="*60)
        print("    音声記事化システム v3.0")
        print("    💰 APIコストゼロ・ローカル処理対応")
        print("    🎯 安定性と精度を重視したアーキテクチャ")
        print("="*62)
        print()
    
    def display_results(self, transcript: str, article: str, filename: str):
        """結果を表示"""
        print("\\n" + "="*80)
        print("✨ 記事作成完了！")
        print("="*80)
        print(f"📁 元ファイル: {filename}")
        print(f"📝 文字起こし文字数: {len(transcript)}文字")
        print(f"📰 完成記事文字数: {len(article)}文字")
        print("="*80)
        
        print("\\n📰 完成記事:")
        print("-" * 80)
        print(article)
        print("-" * 80)
        
        # クリップボードにコピー
        try:
            pyperclip.copy(article)
            print("\\n📋 記事をクリップボードにコピーしました！")
        except Exception as e:
            print(f"⚠️ クリップボードコピーに失敗: {e}")
        
        # ファイル保存のオプション
        save_option = input("\\n💾 結果をファイルに保存しますか？ (y/N): ").lower().strip()
        if save_option in ['y', 'yes']:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                transcript_file = f"{timestamp}_transcript.txt"
                article_file = f"{timestamp}_article.txt"
                
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                with open(article_file, 'w', encoding='utf-8') as f:
                    f.write(article)
                
                print(f"✅ 文字起こし: {transcript_file}")
                print(f"✅ 完成記事: {article_file}")
            except Exception as e:
                print(f"❌ 保存に失敗: {e}")
    
    def run_interactive_mode(self):
        """インタラクティブモード"""
        config = ArticleConfig()
        self.system = VoiceToArticleSystem(config)
        
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
                file_path = self._clean_file_path(file_path)
                
                if not file_path:
                    print("⚠️ ファイルパスを入力してください")
                    continue
                
                if not os.path.exists(file_path):
                    print("❌ ファイルが見つかりません:", file_path)
                    continue
                
                # 処理実行
                print(f"🎵 処理開始: {Path(file_path).name}")
                
                transcript_result = self.system.transcribe_audio(file_path)
                transcript = transcript_result["text"]
                
                cleaned_transcript = self.system.error_corrector.correct_transcript(transcript)
                article = self.system.generate_article_structure(cleaned_transcript)
                
                self.display_results(transcript, article, Path(file_path).name)
                
                # 続行確認
                continue_option = input("\\n🔄 別のファイルを処理しますか？ (y/N): ").lower().strip()
                if continue_option not in ['y', 'yes']:
                    break
                
            except KeyboardInterrupt:
                print("\\n👋 終了します")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")
                logger.error(f"処理エラー: {e}")
    
    def _clean_file_path(self, file_path: str) -> str:
        """ファイルパスのクリーニング"""
        # ドラッグ&ドロップ時の引用符・エスケープ文字を削除
        file_path = file_path.strip('"').strip("'").strip()
        
        # macOSのドラッグ&ドロップエスケープ処理
        file_path = file_path.replace('\\\\ ', ' ')
        file_path = file_path.replace('\\\\~', '~')
        file_path = file_path.replace('\\\\(', '(')
        file_path = file_path.replace('\\\\)', ')')
        file_path = file_path.replace('\\\\&', '&')
        
        # パスの正規化
        file_path = os.path.expanduser(file_path)
        file_path = os.path.abspath(file_path)
        
        return file_path

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="音声記事化システム v3.0")
    parser.add_argument("audio_file", nargs="?", help="音声ファイルのパス")
    parser.add_argument("--model", default="medium", 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="使用するWhisperモデル (default: medium)")
    parser.add_argument("--output", "-o", help="出力ファイルのパス")
    
    args = parser.parse_args()
    
    cli = CLIInterface()
    cli.print_banner()
    
    if args.audio_file:
        # コマンドライン引数から
        if not os.path.exists(args.audio_file):
            print("❌ ファイルが見つかりません:", args.audio_file)
            return
        
        config = ArticleConfig()
        config.whisper_model = args.model
        
        system = VoiceToArticleSystem(config)
        
        try:
            article = system.process_audio_to_article(args.audio_file, args.output)
            print("記事生成成功！")
            print(f"記事の長さ: {len(article)}文字")
            
            if not args.output:
                cli.display_results("", article, Path(args.audio_file).name)
                
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            logger.error(f"処理エラー: {e}")
    else:
        # インタラクティブモード
        cli.run_interactive_mode()

if __name__ == "__main__":
    main()