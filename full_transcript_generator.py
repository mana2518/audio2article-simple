#!/usr/bin/env python3
"""
完全文字起こし保持型記事生成ツール
音声 → 完全文字起こし → 整理・清書 → note風記事
"""

import os
import sys
import argparse
from pathlib import Path
import whisper
import re
from datetime import datetime
import pyperclip

class FullTranscriptGenerator:
    def __init__(self):
        self.model = None
        self.model_name = "base"  # 高速処理
        
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

    def transcribe_audio_full(self, audio_path: str) -> str:
        """完全な音声文字起こし"""
        try:
            self.load_whisper_model()
            print("🎵 音声の完全文字起こし処理中...")
            
            # 高品質設定で完全文字起こし
            result = self.model.transcribe(
                audio_path,
                language="ja",
                temperature=0.0,
                beam_size=5,
                best_of=5,
                patience=1.0,
                condition_on_previous_text=True,
                compression_ratio_threshold=2.4,
                logprob_threshold=-1.0,
                no_speech_threshold=0.6,
                initial_prompt="マナミです。3人の子どもを育てながらSNS発信やコンテンツ作成を中心にお仕事をしているママフリーランスです。以下は日本語の音声配信です。正確に文字起こしをしてください。"
            )
            
            transcript = result["text"]
            print(f"✅ 完全文字起こし完了: {len(transcript)}文字")
            return transcript
            
        except Exception as e:
            print(f"❌ 文字起こしエラー: {e}")
            return None

    def clean_transcript_gently(self, text):
        """軽微なクリーニング（内容を削除しない）"""
        text = text.strip()
        
        # 基本的な音声認識エラーの修正のみ
        corrections = {
            'まなみ': 'マナミ', 'マナみ': 'マナミ', '学み': 'マナミ',
            'さにの子ども': '3人の子ども', 'さ人の子ども': '3人の子ども',
            'SNSはしん': 'SNS発信', 'SNSのつう': 'SNS運用',
            'ままフリー': 'ママフリーランス', 'ままプリー': 'ママフリーランス',
            'コンテンツペーサク': 'コンテンツ作成', 'コンテンツ製作': 'コンテンツ作成',
            '子どもたち': '子ども', '子供': '子ども',
            'インスタ': 'Instagram', 'ユーチューブ': 'YouTube'
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text

    def organize_into_paragraphs(self, text):
        """自然な段落に整理"""
        # 文を句読点で分割
        sentences = re.split(r'[。！？]', text)
        
        paragraphs = []
        current_paragraph = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
                
            # 軽微なフィラー語のみ除去（内容は保持）
            sentence = re.sub(r'えー+、?', '', sentence)
            sentence = re.sub(r'あの+、?', '', sentence)
            sentence = re.sub(r'えっと+、?', '', sentence)
            sentence = re.sub(r'うーん+、?', '', sentence)
            sentence = re.sub(r'まぁ+、?', '', sentence)
            sentence = re.sub(r'そう+、?', '', sentence)
            
            # 冗長な表現を少し簡潔に
            sentence = re.sub(r'だと思うんですけど、?', 'と思います', sentence)
            sentence = re.sub(r'なんですけど、?', 'です', sentence)
            sentence = re.sub(r'っていう風に、?', 'という形で', sentence)
            
            sentence = re.sub(r'\s+', ' ', sentence).strip()
            
            if sentence:
                current_paragraph.append(sentence + '。')
                
                # 段落区切りの判定（話題転換の兆候）
                topic_change_indicators = [
                    'それで', 'そして', 'それから', 'でも', 'ただ', '実は',
                    'ところで', 'さて', '次に', 'また', 'そういえば', 'あと'
                ]
                
                # 段落が3-5文になったら区切る、または話題転換があったら区切る
                if (len(current_paragraph) >= 3 and 
                    any(indicator in sentence for indicator in topic_change_indicators)) or \
                   len(current_paragraph) >= 5:
                    
                    paragraphs.append(''.join(current_paragraph))
                    current_paragraph = []
        
        # 最後の段落を追加
        if current_paragraph:
            paragraphs.append(''.join(current_paragraph))
        
        return paragraphs

    def create_note_style_article_full(self, transcript):
        """完全な文字起こしからnote風記事を生成"""
        print("📝 完全文字起こしをnote風記事に整理中...")
        
        # 軽微なクリーニング
        cleaned_text = self.clean_transcript_gently(transcript)
        
        # 段落整理
        paragraphs = self.organize_into_paragraphs(cleaned_text)
        
        # 記事構成
        article_parts = []
        
        # 導入部
        article_parts.append("マナミです。\n")
        
        # 最初の段落から導入のヒントを得る
        if paragraphs:
            first_para = paragraphs[0]
            if 'ママフリーランス' in first_para or '働き方' in first_para:
                article_parts.append("ママフリーランスとしての働き方について、最近考えていることをお話しします。\n")
            elif 'SNS' in first_para or 'Instagram' in first_para:
                article_parts.append("SNS発信について、最近感じていることをお話しします。\n")
            elif 'コンテンツ' in first_para:
                article_parts.append("コンテンツ作成について、日々感じていることをお話しします。\n")
            else:
                article_parts.append("最近考えていることを、皆さんと共有したいと思います。\n")
        
        # メインコンテンツ（全段落を使用）
        for i, paragraph in enumerate(paragraphs):
            if i > 0:  # 最初の段落は導入で使用済み
                article_parts.append(paragraph + "\n")
                
                # 長い記事の場合は適度に区切り線を挿入
                if i % 4 == 0 and i > 0:
                    article_parts.append("\n---------------\n\n")
        
        # 結論部
        article_parts.append("\n何か皆さんの参考になれば嬉しいです。皆さんも日常の中で感じたことや工夫していることがあれば、大切にしてみてください。そうした積み重ねが、より良い生活や働き方につながっていくのではないかと思います。")
        
        final_article = "".join(article_parts)
        
        print(f"📊 最終記事文字数: {len(final_article)}文字")
        
        return final_article

    def copy_to_clipboard(self, text):
        """クリップボードにコピー"""
        try:
            pyperclip.copy(text)
            print("📋 記事をクリップボードにコピーしました！")
        except Exception as e:
            print(f"⚠️ クリップボードコピー失敗: {e}")

    def save_article(self, article):
        """記事保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"full_transcript_article_{timestamp}.md"
        filepath = Path("/Users/manami/audio_to_article_new") / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(article)
            print(f"💾 記事保存完了: {filename}")
            return str(filepath)
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            return None

    def save_full_transcript(self, transcript):
        """完全文字起こしも保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"full_transcript_{timestamp}.txt"
        filepath = Path("/Users/manami/audio_to_article_new") / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"💾 完全文字起こし保存完了: {filename}")
            return str(filepath)
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            return None

    def process_audio_file(self, audio_path):
        """音声ファイルの完全処理"""
        print(f"🔍 処理開始: {Path(audio_path).name}")
        
        # ファイル存在確認
        if not os.path.exists(audio_path):
            print(f"❌ ファイルが見つかりません: {audio_path}")
            return None
        
        # ファイルサイズ確認
        file_size = os.path.getsize(audio_path)
        print(f"📁 ファイルサイズ: {file_size / (1024*1024):.1f}MB")
        
        # 完全文字起こし
        transcript = self.transcribe_audio_full(audio_path)
        if not transcript:
            return None
        
        # 完全文字起こしを保存
        self.save_full_transcript(transcript)
        
        # note風記事生成
        article = self.create_note_style_article_full(transcript)
        
        # 結果表示
        print("\n" + "=" * 80)
        print("📰 生成されたnote風記事:")
        print("=" * 80)
        print(article)
        print("=" * 80)
        
        # クリップボードにコピー
        self.copy_to_clipboard(article)
        
        # 保存
        saved_path = self.save_article(article)
        
        print(f"\n✅ 処理完了")
        if saved_path:
            print(f"💾 保存場所: {saved_path}")
        
        return article

    def interactive_mode(self):
        """インタラクティブモード"""
        print("🎯 音声ファイルをドラッグ&ドロップするか、パスを入力してください")
        print("   📁 対応形式: mp3, wav, m4a, aac, flac, ogg, wma, mp4, mov等")
        print("   📋 完全文字起こし保持: 内容を削除せずに整理します")
        print("   🚪 終了: 'q' を入力")
        
        while True:
            audio_input = input("\n🎙️ ファイル: ").strip()
            
            if audio_input.lower() in ['q', 'quit', 'exit']:
                break
            
            if not audio_input:
                continue
            
            # パスの整理
            audio_path = self.process_file_path(audio_input)
            
            print(f"🔍 解析されたパス: {audio_path}")
            
            if os.path.exists(audio_path):
                self.process_audio_file(audio_path)
            else:
                print("❌ ファイルが見つかりません")
                continue
            
            # 次の処理を確認
            print("\n" + "=" * 50)
            next_action = input("🔄 別の音声ファイルを処理しますか？ (y/N): ").lower().strip()
            if next_action not in ['y', 'yes']:
                break
        
        print("👋 お疲れさまでした！")

    def process_file_path(self, file_input):
        """ファイルパスの処理"""
        audio_path = file_input.strip().strip('\n\r\t ')
        
        # クオート文字を削除
        quote_chars = ['"', "'", '`']
        for quote in quote_chars:
            if audio_path.startswith(quote) and audio_path.endswith(quote) and len(audio_path) > 1:
                audio_path = audio_path[1:-1]
                break
        
        # エスケープ文字処理
        escape_mappings = {
            '\\ ': ' ', '\\&': '&', '\\(': '(', '\\)': ')', '\\[': '[', '\\]': ']',
            '\\{': '{', '\\}': '}', '\\"': '"', "\\'":  "'", '\\\\': '\\'
        }
        for escaped, unescaped in escape_mappings.items():
            audio_path = audio_path.replace(escaped, unescaped)
        
        if audio_path.startswith('file://'):
            audio_path = audio_path[7:]
            
        audio_path = os.path.expanduser(audio_path)
        audio_path = os.path.abspath(audio_path)
        
        return audio_path

def main():
    parser = argparse.ArgumentParser(description='完全文字起こし保持型記事生成ツール')
    parser.add_argument('audio_file', nargs='?', help='音声ファイルのパス')
    
    args = parser.parse_args()
    
    generator = FullTranscriptGenerator()
    
    print("🎙️" + "=" * 50)
    print("   完全文字起こし保持型記事生成ツール v1.0")
    print("   音声 → 完全文字起こし → note風記事")
    print("=" * 52)
    print()
    
    if args.audio_file:
        # コマンドライン引数で音声ファイルが指定されている場合
        audio_path = generator.process_file_path(args.audio_file)
        
        print(f"🔍 解析されたパス: {audio_path}")
        
        if os.path.exists(audio_path):
            generator.process_audio_file(audio_path)
        else:
            print(f"❌ ファイルが見つかりません: {audio_path}")
        return
    
    # インタラクティブモード
    generator.interactive_mode()

if __name__ == "__main__":
    main()