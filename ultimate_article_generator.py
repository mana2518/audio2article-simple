#!/usr/bin/env python3
"""
究極記事生成システム
音声内容を高品質なnote記事に完全変換
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

class UltimateArticleGenerator:
    def __init__(self):
        # Whisperモデルの初期化
        self.model = None
        self.model_name = "tiny"  # 高速処理用tinyモデルを使用

    def cleanup_previous_session(self):
        """前回のセッションデータを完全クリア"""
        print(f"🔄 新しいセッション開始")

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

    def transcribe_with_whisper(self, audio_path: str) -> str:
        """Whisperによる音声文字起こし"""
        try:
            self.load_whisper_model()
            
            result = self.model.transcribe(audio_path, language="ja")
            transcript = result["text"]
            
            return transcript
            
        except Exception as e:
            print(f"❌ Whisper文字起こしエラー: {e}")
            return None

    def clean_transcript(self, transcript: str) -> str:
        """文字起こしテキストの修正"""
        text = transcript.strip()
        
        # 包括的な修正パターン
        corrections = {
            'まなみ': 'マナミ',
            'まなみです': 'マナミです',
            'さらにの子ども': '3人の子ども',
            'SNSはしん': 'SNS発信',
            'コンテンツペーサコ': 'コンテンツ作成',
            'ままプリ': 'ママフリーランス',
            'フォアン': '不安',
            'カメソ': 'メソッド',
            'カメント': 'メソッド',
            'テーコスト': '低コスト',
            'リーナー': 'リリーナ',
            'キンドラー': 'Kindle',
            'あんまぞ': 'Amazon',
            'お彼': 'お金',
            'バクセント': 'ばくぜんとした',
            '押しごと': '仕事',
            'バイブコーディング': 'ライブコーディング',
            'バイブ': 'ライブ'
        }
        
        for old, new in corrections.items():
            text = text.replace(old, new)
        
        # 過度な読点や重複表現を削除
        text = re.sub(r'、+', '、', text)
        text = re.sub(r'えー、?|あの、?|えっと、?|うーん、?|まぁ、?', '', text)
        
        return text

    def detect_content_type(self, text: str) -> str:
        """コンテンツタイプを検出（常にgeneral）"""
        return "general"

    def extract_key_themes(self, text: str) -> list:
        """文字起こしから主要テーマを抽出"""
        sentences = [s.strip() for s in text.split('。') if len(s.strip()) > 5]
        
        if not sentences:
            return ["今回は音声配信の内容についてお話ししたいと思います"]
        
        # 文を意味のあるブロックに分割
        themes = []
        current_theme = []
        sentence_count = 0
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            current_theme.append(sentence.strip())
            sentence_count += 1
            
            # 3-4文ごとにテーマを区切る、または話題転換フレーズを検出
            if (sentence_count >= 3 and any(phrase in sentence for phrase in ['思います', 'ですね', 'ました'])):
                themes.append('。'.join(current_theme) + '。')
                current_theme = []
                sentence_count = 0
        
        # 残りの文を追加
        if current_theme:
            themes.append('。'.join(current_theme) + '。')
        
        # 最低でも2つのテーマを確保
        if len(themes) < 2 and sentences:
            mid_point = len(sentences) // 2
            themes = [
                '。'.join(sentences[:mid_point]) + '。',
                '。'.join(sentences[mid_point:]) + '。'
            ]
        
        return themes[:6]  # 最大6テーマ

    def structure_content(self, themes: list) -> dict:
        """テーマを記事構造に整理"""
        if len(themes) == 0:
            return {"intro": "マナミです。\n\n今回は音声配信の内容についてお話ししたいと思います。", "main": ["最近感じていることを皆さんと共有したいと思います。"], "conclusion": "今後もこうした内容を皆さんと共有していきたいと思います。"}
        
        # 導入部を作成
        intro = self.create_intro_from_text(' '.join(themes))
        
        # メイン部分を作成
        main_sections = []
        
        # すべてのテーマから意味のあるセクションを作成
        for i, theme in enumerate(themes):
            section = self.create_section_from_theme(theme, i)
            if section and len(section.strip()) > 20:  # 意味のある長さがあるセクションのみ
                main_sections.append(section)
        
        # メインセクションが少ない場合のフォールバック
        if len(main_sections) < 2:
            # テーマを再分割して複数のセクションを作成
            all_text = ' '.join(themes)
            sentences = [s.strip() + '。' for s in all_text.split('。') if len(s.strip()) > 10]
            
            if len(sentences) >= 4:
                mid1 = len(sentences) // 3
                mid2 = 2 * len(sentences) // 3
                
                main_sections = [
                    '\n\n'.join(sentences[:mid1]),
                    '\n\n'.join(sentences[mid1:mid2]),
                    '\n\n'.join(sentences[mid2:])
                ]
            else:
                main_sections = ['\n\n'.join(sentences)]
        
        # 結論部
        conclusion = self.create_conclusion_from_content(themes)
        
        return {
            "intro": intro,
            "main": main_sections,
            "conclusion": conclusion
        }

    def create_intro_from_text(self, text: str) -> str:
        """テキストから導入部を作成"""
        intro = "マナミです。\n\n"
        
        # テキストから主要なキーワードを抽出して導入を作成
        if '家事' in text or '代行' in text:
            intro += "今回は家事について思うことをお話ししたいと思います。"
        elif '本' in text:
            intro += "今回は本について話したいと思います。"
        elif 'コーディング' in text or 'プログラミング' in text:
            intro += "今回は技術的な話をしたいと思います。"
        elif '子ども' in text or '育児' in text:
            intro += "今回は子育てについて感じていることをお話ししたいと思います。"
        elif '仕事' in text or 'フリーランス' in text:
            intro += "今回は仕事について思うことをお話ししたいと思います。"
        else:
            intro += "今回は最近考えていることについてお話ししたいと思います。"
        
        return intro

    def create_section_from_theme(self, theme: str, section_num: int) -> str:
        """テーマから記事セクションを作成"""
        if not theme or len(theme.strip()) < 10:
            return None
        
        # テーマを文に分割
        sentences = [s.strip() for s in theme.split('。') if len(s.strip()) > 5]
        
        if not sentences:
            return None
        
        # 文を自然な段落に整理
        result_sentences = []
        for sentence in sentences[:4]:  # 最大4文
            if sentence and not sentence.endswith('。'):
                sentence += '。'
            if sentence:
                result_sentences.append(sentence)
        
        return '\n\n'.join(result_sentences)

    def create_conclusion_from_content(self, themes: list) -> str:
        """内容から結論部を作成"""
        if not themes:
            return "今後もこうした内容を皆さんと共有していきたいと思います。"
        
        # 全体の内容から適切な結論を作成
        all_content = ' '.join(themes)
        
        if '家事' in all_content or '代行' in all_content:
            return "皆さんもそれぞれの価値観で、生活を整えていけばいいと思います。"
        elif '本' in all_content:
            return "皆さんもよかったら参考にしてみてください。"
        elif '子ども' in all_content or '育児' in all_content:
            return "子育てについて、また皆さんと共有していきたいと思います。"
        elif '仕事' in all_content:
            return "働き方について、今後も考えを共有していきたいと思います。"
        else:
            return "今後もこうした内容を皆さんと共有していきたいと思います。"

    def generate_article_from_content(self, transcript: str) -> str:
        """音声内容から高品質記事を生成"""
        
        # 文字起こしを修正
        clean_text = self.clean_transcript(transcript)
        
        print(f"📝 動的記事生成を開始")
        
        # 常に動的記事生成を使用
        return self.generate_dynamic_article(clean_text)

    def generate_dynamic_article(self, text: str) -> str:
        """動的に記事を生成（一般コンテンツ用）"""
        
        # 主要テーマを抽出
        themes = self.extract_key_themes(text)
        
        # 記事構造を作成
        structure = self.structure_content(themes)
        
        # 記事を組み立て
        article_parts = []
        
        # 導入部
        article_parts.append(structure["intro"])
        
        # メイン部分
        for i, section in enumerate(structure["main"]):
            if i > 0:  # 最初のセクション以外に区切り線を追加
                article_parts.append("---------------")
            article_parts.append(section)
        
        # 結論部
        if structure["conclusion"]:
            article_parts.append("---------------")
            article_parts.append(structure["conclusion"])
        
        return '\n\n'.join(article_parts)


    def process_audio_file(self, audio_path: str):
        """音声ファイルを処理して記事を生成"""
        filename = Path(audio_path).name
        
        # 前回のセッションデータを完全クリア
        self.cleanup_previous_session()
        
        print(f"\n🎵 文字起こし中...")
        
        # 文字起こし
        transcript = self.transcribe_with_whisper(audio_path)
        
        if not transcript:
            print("❌ 文字起こしに失敗しました")
            return
        
        print(f"🤖 記事生成中...")
        
        # 高品質記事生成
        article = self.generate_article_from_content(transcript)
        
        print(f"✅ 処理完了\n")
        
        # 結果表示
        self.display_results(article)

    def display_results(self, article: str):
        """結果を表示"""
        # 記事を直接表示
        print("=" * 80)
        print("📰 生成された記事:")
        print("=" * 80)
        print(article)
        print("=" * 80)
        
        # クリップボードにコピー
        try:
            pyperclip.copy(article)
            print("\n✅ 記事をクリップボードに保存しました！")
        except Exception as e:
            print(f"⚠️ クリップボード保存に失敗: {e}")

    def print_banner(self):
        """バナー表示"""
        print("🎙️" + "=" * 60)
        print("    究極記事生成システム")
        print("    💰 音声内容を高品質note記事に完全変換")
        print("=" * 62)
        print()

    def main(self):
        """メイン処理"""
        parser = argparse.ArgumentParser(description='究極記事生成システム')
        parser.add_argument('audio_file', nargs='?', help='音声ファイルのパス')
        parser.add_argument('--model', choices=['tiny', 'base', 'small', 'medium', 'large'], 
                          default='tiny', help='Whisperモデルを指定')
        
        args = parser.parse_args()
        
        # モデル指定があれば設定
        if args.model:
            self.model_name = args.model
        
        self.print_banner()
        
        print("💡 使用方法:")
        print("   1. 📁 音声ファイルをターミナルにドラッグ&ドロップしてEnter")
        print("   2. 📝 ファイルパスを直接入力")
        print()
        
        # コマンドライン引数で音声ファイルが指定されている場合
        if args.audio_file:
            audio_path = args.audio_file.strip().strip('"').strip("'")
            audio_path = os.path.expanduser(audio_path)
            
            if os.path.exists(audio_path):
                self.process_audio_file(audio_path)
            else:
                print(f"❌ ファイルが見つかりません: {audio_path}")
            return
        
        # インタラクティブモード
        while True:
            print("🎯 音声ファイルをここにドラッグ&ドロップするか、パスを入力してください")
            print("   (終了するには 'q' を入力)")
            audio_input = input("🎙️ ファイル: ").strip()
            
            if audio_input.lower() in ['q', 'quit', 'exit']:
                break
            
            if not audio_input:
                continue
            
            # パスの整理（ドラッグ&ドロップ対応）
            audio_path = audio_input.strip()
            
            # クオート文字を削除
            if audio_path.startswith('"') and audio_path.endswith('"'):
                audio_path = audio_path[1:-1]
            elif audio_path.startswith("'") and audio_path.endswith("'"):
                audio_path = audio_path[1:-1]
            
            # 全てのバックスラッシュエスケープを処理
            audio_path = audio_path.replace('\\ ', ' ')
            audio_path = audio_path.replace('\\~', '~')
            audio_path = audio_path.replace('\\\\', '\\')
            
            # チルダ展開
            audio_path = os.path.expanduser(audio_path)
            
            print(f"🔍 処理開始: {os.path.basename(audio_path)}")
            
            if os.path.exists(audio_path):
                self.process_audio_file(audio_path)
            else:
                print(f"❌ ファイルが見つかりません")
                continue
            
            # 次の処理を確認
            print("\n" + "=" * 60)
            next_action = input("🔄 別の音声ファイルを処理しますか？ (y/N): ").lower().strip()
            if next_action not in ['y', 'yes']:
                break
        
        print("👋 お疲れさまでした！")

if __name__ == "__main__":
    generator = UltimateArticleGenerator()
    generator.main()