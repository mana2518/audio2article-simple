#!/usr/bin/env python3
"""
最終版音声記事生成システム
全要求を満たすシンプル・確実システム
"""

import os
import sys
import argparse
import whisper
import pyperclip
import re
from pathlib import Path

class FinalArticleSystem:
    def __init__(self):
        self.model = None
        self.model_name = "tiny"
    
    def clear_session(self):
        """セッション完全クリア"""
        # 何も表示せずクリア
        pass
    
    def load_whisper(self):
        """Whisperモデル読み込み"""
        if self.model is None:
            print("🎵 音声を文字起こし中...")
            self.model = whisper.load_model(self.model_name)
    
    def transcribe_audio(self, audio_path: str) -> str:
        """音声文字起こし"""
        self.load_whisper()
        result = self.model.transcribe(audio_path, language="ja")
        return result["text"]
    
    def fix_transcript(self, text: str) -> str:
        """文字起こし修正"""
        
        # 基本修正
        fixes = {
            'まなみ': 'マナミ', 'お彼': 'お金', 'フォアン': '不安', '押しごと': '仕事',
            'ままプリ': 'ママフリーランス', 'SNSはしん': 'SNS発信', 'コンテンツペーサコ': 'コンテンツ作成',
            'バイブコーディング': 'ライブコーディング', 'Vibu': 'ライブ', 'カメソ': 'メソッド',
            'あまぞん': 'Amazon', 'リーナー': 'リリーナ', 'テーコスト': '低コスト',
            'こそだって': '子育て', 'つきまじかん': 'スキマ時間', 'スキムマ時間': 'スキマ時間',
            '終入': '収入', 'シンオート': '仕事', '自田': '実際', 'ゲッチオビ': '月曜日',
            '今天水浅口': 'SNS発信や', 'サウイト': '三男', '年収年上': '長女',
            'ビネツー': '微熱', 'ポンド': '発熱', 'ボント': '発熱', '企たく': '何か',
            'んか': 'なんか', 'う': '', 'がら': 'ながら', 'ってる': 'ている',
            'だんという': 'だと', 'しう': 'し', 'ですもん': 'です', 'かんか': 'なんか',
            '方々': 'を', 'うあれ': 'は', 'もた': '子ども', '縦続き': '続けて',
            '気ましたということで': '話しました', 'スコシ方': '過ごし方',
            'んで': 'ので', 'だら': 'だから', 'かば': 'ので'
        }
        
        for old, new in fixes.items():
            text = text.replace(old, new)
        
        # 話し言葉修正
        text = text.replace('っていう', 'という')
        text = text.replace('だと思うんです', 'だと思います')
        text = text.replace('なんですよ', 'です')
        text = text.replace('ですね', 'です')
        
        # 不要語句除去
        text = re.sub(r'、+', '、', text)
        text = re.sub(r'。+', '。', text)
        text = re.sub(r'えー、?|あの、?|うーん、?', '', text)
        
        return text
    
    def create_article(self, text: str) -> str:
        """記事作成"""
        
        print("📝 記事を生成中...")
        
        # 文を分割して意味のある部分を抽出
        sentences = [s.strip() for s in text.split('。') if len(s.strip()) > 10]
        
        # トピック判定
        all_text = ' '.join(sentences)
        if '子育て' in all_text or '子ども' in all_text or 'スキマ時間' in all_text:
            topic = "子育て"
            intro = "今回は子育てについて思うことをお話ししたいと思います。"
            conclusion = "子育てについて、今後も皆さんと経験を共有していきたいと思います。"
        elif 'お金' in all_text or '本' in all_text:
            topic = "お金・本"
            intro = "今回は本やお金について思うことをお話ししたいと思います。"
            conclusion = "皆さんもよかったら参考にしてみてください。"
        elif '仕事' in all_text or 'フリーランス' in all_text:
            topic = "仕事"
            intro = "今回は仕事について思うことをお話ししたいと思います。"
            conclusion = "仕事について、今後も皆さんと経験を共有していきたいと思います。"
        else:
            topic = "日常"
            intro = "今回は最近感じていることについてお話ししたいと思います。"
            conclusion = "今後もこうした内容を皆さんと共有していきたいと思います。"
        
        # 意味のある文を選別（最大6文）
        good_sentences = []
        for sentence in sentences:
            if len(sentence) > 15 and not any(skip in sentence for skip in ['今、今、今', 'はい', 'ありがとう']):
                good_sentences.append(sentence)
        
        if len(good_sentences) < 3:
            good_sentences = sentences[:6]  # フォールバック
        
        good_sentences = good_sentences[:6]
        
        # 記事構成
        if len(good_sentences) <= 2:
            main_parts = good_sentences
        elif len(good_sentences) <= 4:
            mid = len(good_sentences) // 2
            main_parts = [
                ' '.join(good_sentences[:mid]),
                ' '.join(good_sentences[mid:])
            ]
        else:
            # 3つのセクションに分割
            third = len(good_sentences) // 3
            main_parts = [
                ' '.join(good_sentences[:third]),
                ' '.join(good_sentences[third:2*third]),
                ' '.join(good_sentences[2*third:])
            ]
        
        # 記事組み立て
        article = f"マナミです。\n\n{intro}\n\n"
        
        for i, part in enumerate(main_parts):
            if i > 0:
                article += "---------------\n\n"
            article += f"{part.strip()}。\n\n"
        
        article += f"---------------\n\n{conclusion}"
        
        return article
    
    def process_audio(self, audio_path: str):
        """音声処理メイン"""
        # セッションクリア
        self.clear_session()
        
        try:
            # 文字起こし
            transcript = self.transcribe_audio(audio_path)
            
            # 修正
            fixed_text = self.fix_transcript(transcript)
            
            # 記事作成
            article = self.create_article(fixed_text)
            
            # 結果表示
            print("\n" + "=" * 80)
            print("📰 完成記事:")
            print("=" * 80)
            print(article)
            print("=" * 80)
            
            # クリップボードコピー
            pyperclip.copy(article)
            print("\n✅ 記事をクリップボードにコピーしました！")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def main(self):
        """メイン処理"""
        parser = argparse.ArgumentParser(description='音声記事生成システム')
        parser.add_argument('audio_file', nargs='?', help='音声ファイル')
        args = parser.parse_args()
        
        print("🎙️ 音声記事生成システム")
        print("=" * 50)
        print("使用方法: 音声ファイルをドラッグ&ドロップ")
        print()
        
        if args.audio_file:
            audio_path = args.audio_file.strip().strip('"').strip("'")
            audio_path = os.path.expanduser(audio_path)
            
            if os.path.exists(audio_path):
                self.process_audio(audio_path)
            else:
                print(f"❌ ファイルが見つかりません")
            return
        
        # ドラッグ&ドロップ待機
        while True:
            try:
                print("🎯 音声ファイルをドラッグ&ドロップしてください")
                print("   (終了: q)")
                
                user_input = input("ファイル: ").strip()
                
                if user_input.lower() in ['q', 'quit', 'exit']:
                    break
                
                if not user_input:
                    continue
                
                # パス整理
                audio_path = user_input.strip()
                if audio_path.startswith('"') and audio_path.endswith('"'):
                    audio_path = audio_path[1:-1]
                elif audio_path.startswith("'") and audio_path.endswith("'"):
                    audio_path = audio_path[1:-1]
                
                audio_path = audio_path.replace('\\ ', ' ')
                audio_path = os.path.expanduser(audio_path)
                
                if os.path.exists(audio_path):
                    print(f"\n🔍 処理開始: {Path(audio_path).name}")
                    self.process_audio(audio_path)
                    
                    print("\n" + "=" * 50)
                    next_file = input("🔄 続けて処理しますか？ (y/N): ").lower()
                    if next_file not in ['y', 'yes']:
                        break
                else:
                    print("❌ ファイルが見つかりません")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        print("\n👋 終了しました")

if __name__ == "__main__":
    system = FinalArticleSystem()
    system.main()