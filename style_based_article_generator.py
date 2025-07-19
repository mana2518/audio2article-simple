#!/usr/bin/env python3
"""
ユーザー文体学習型記事生成ツール
音声ファイル → 文字起こし → ユーザーの文体に基づいた記事生成
"""

import os
import sys
import argparse
from pathlib import Path
import whisper
import re
from datetime import datetime
import pyperclip

class StyleBasedArticleGenerator:
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

    def transcribe_audio(self, audio_path: str) -> str:
        """音声文字起こし"""
        try:
            self.load_whisper_model()
            print("🎵 音声を文字起こし中...")
            
            # 高品質設定で文字起こし
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
            
            print(f"✅ 文字起こし完了: {len(transcript)}文字")
            return transcript
            
        except Exception as e:
            print(f"❌ 文字起こしエラー: {e}")
            return None

    def clean_transcript(self, text):
        """文字起こしのクリーニング"""
        text = text.strip()
        
        # 音声認識エラーの修正
        corrections = {
            'まなみ': 'マナミ', 'マナみ': 'マナミ', '学み': 'マナミ',
            'さにの子ども': '3人の子ども', 'さ人の子ども': '3人の子ども', 'サニーの子ども': '3人の子ども',
            'SNSはしん': 'SNS発信', 'SNSのつう': 'SNS運用', 'SNS4サポート': 'SNS運用サポート',
            'ままフリー': 'ママフリーランス', 'ままプリー': 'ママフリーランス', 'ままプリランス': 'ママフリーランス',
            'コンテンツペーサク': 'コンテンツ作成', 'コンテンツ製作': 'コンテンツ作成',
            'メンバーシーピ': 'メンバーシップ', 'メンバーしップ': 'メンバーシップ',
            '伴奏型': '伴走型', 'バンソー型': '伴走型',
            '子どもたち': '子ども', '子供': '子ども'
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text

    def extract_main_topic_and_content(self, text):
        """主要テーマと重要内容を抽出"""
        # 文を句読点で分割
        sentences = re.split(r'[。！？]', text)
        
        # 重要なキーワードとテーマの対応
        topic_patterns = [
            (r'値段をつける|価格設定|お金.*取る|有料.*サービス|メンバーシップ|8000円|15000円', '自分のサービスに値段をつけること'),
            (r'働き方|フリーランス|仕事.*育児|ママフリーランス|コミュニティ', 'ママフリーランスとしての働き方'),
            (r'コミュニケーション|やり取り|相手.*立場|伝え方|コミュニケーションコスト', 'コミュニケーションの重要性'),
            (r'AI.*活用|AI.*相談|AIと.*壁打ち|ChatGPT|Gemini', 'AIの活用について'),
            (r'SNS.*発信|コンテンツ.*作成|情報.*発信|Instagram|YouTube|note', '情報発信について'),
            (r'子ども.*育て|家事.*育児|ワンオペ|保育園|体調.*崩', '子育てと仕事の両立'),
            (r'生活|日常|ライフスタイル|時間.*使い方', '日々の生活について')
        ]
        
        main_topic = '最近考えていること'
        for pattern, topic in topic_patterns:
            if re.search(pattern, text):
                main_topic = topic
                break
        
        # 重要な内容を抽出
        important_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:
                continue
                
            # 重要な内容を示すキーワード
            importance_indicators = [
                '実は', '具体的に', '例えば', 'つまり', 'そうなんです', 'ということで',
                'と思っている', 'を始めて', 'をやって', 'と感じて', 'を考えて',
                'メンバーシップ', 'SNS運用', 'コンテンツ', 'AI', 'フリーランス',
                '価格', '値段', 'サービス', '音声配信', 'ママフリーランス'
            ]
            
            if any(indicator in sentence for indicator in importance_indicators):
                cleaned = self.remove_fillers(sentence)
                if len(cleaned) > 20:
                    important_sentences.append(cleaned + '。')
        
        return main_topic, important_sentences

    def remove_fillers(self, text):
        """フィラー語除去"""
        basic_fillers = [
            r'えー+、?', r'あの+、?', r'えっと+、?', r'うーん+、?', r'まぁ+、?',
            r'なんか+、?', r'そう+、?'
        ]
        
        for filler in basic_fillers:
            text = re.sub(filler, '', text)
        
        # 冗長な表現を簡潔に
        redundant_patterns = [
            (r'だと思うんですけど、?', 'と思います'),
            (r'なんですけど、?', 'です'),
            (r'っていう風に、?', 'という形で'),
            (r'ということなんですよね', 'ということです')
        ]
        
        for pattern, replacement in redundant_patterns:
            text = re.sub(pattern, replacement, text)
        
        text = re.sub(r'\s+', ' ', text).strip()
        
        if text and not text.endswith(('。', '！', '？')):
            if re.search(r'[ですますたしいない]$', text):
                text += '。'
        
        return text

    def generate_article_with_style(self, transcript):
        """学習した文体に基づいて記事生成"""
        print("📝 ユーザーの文体に基づいて記事を生成中...")
        
        # クリーニング
        clean_text = self.clean_transcript(transcript)
        print(f"📝 クリーニング完了: {len(clean_text)}文字")
        
        # 主要テーマと重要内容抽出
        main_topic, important_sentences = self.extract_main_topic_and_content(clean_text)
        print(f"🎯 主要テーマ: {main_topic}")
        print(f"📄 抽出された重要文: {len(important_sentences)}個")
        
        # マナミさんの文体に基づいた記事構成
        article_parts = []
        
        # 導入部 - マナミさんの典型的な書き出し
        article_parts.append("マナミです。\n\n")
        
        # 状況説明と話題導入
        if 'AI' in main_topic:
            article_parts.append("AIの活用について、最近考えていることをお話しします。\n\n")
        elif '働き方' in main_topic or 'フリーランス' in main_topic:
            article_parts.append("ママフリーランスとしての働き方について、最近感じることがありました。\n\n")
        elif 'コミュニケーション' in main_topic:
            article_parts.append("コミュニケーションについて、改めて考える機会がありました。\n\n")
        elif '発信' in main_topic:
            article_parts.append("情報発信のあり方について、考え直すきっかけがありました。\n\n")
        elif '子育て' in main_topic:
            article_parts.append("3人の子どもを育てながら働く日々の中で、色々と思うことがありました。\n\n")
        else:
            article_parts.append("日々の生活の中で感じることがありました。\n\n")
        
        # メイン内容
        if important_sentences:
            # 文章を3つのブロックに分ける
            mid_point = len(important_sentences) // 2
            if len(important_sentences) >= 3:
                block1 = important_sentences[:mid_point]
                block2 = important_sentences[mid_point:]
                
                # 第1ブロック
                article_parts.append('\n'.join(block1[:3]))
                article_parts.append("\n\n---------------\n\n")
                
                # 第2ブロック
                if block2:
                    article_parts.append('\n'.join(block2[:3]))
                    article_parts.append("\n\n")
            else:
                article_parts.append('\n'.join(important_sentences))
                article_parts.append("\n\n")
        else:
            # フォールバック内容
            if 'AI' in main_topic:
                article_parts.append("AIを活用することで、働き方や生活の質を向上させていけると思います。\n\n実際に使ってみると、想像していた以上に色々なことができることがわかりました。\n\n")
            else:
                article_parts.append("実際にやってみると、思っていた以上に色々と考えることがありました。\n\n")
        
        # 結論部 - マナミさんの典型的な締めくくり
        article_parts.append("---------------\n\n")
        
        if 'AI' in main_topic:
            conclusion = """今回お話しした内容は、私自身の体験や考えに基づくものですが、同じような状況にある方の参考になれば嬉しいです。

AIを上手に活用することで、働き方や生活の質を向上させていけると思います。

皆さんもぜひ、日常の中で感じたことや工夫していることがあれば、大切にしてみてください。そうした積み重ねが、より良い生活や働き方につながっていくのではないかと思います。"""
        elif 'フリーランス' in main_topic or '働き方' in main_topic:
            conclusion = """今回お話しした内容は、私自身の体験や考えに基づくものですが、同じような状況にある方の参考になれば嬉しいです。

ママフリーランスという働き方には大変さもありますが、その分得られるものも大きいと思います。

皆さんもぜひ、日常の中で感じたことや工夫していることがあれば、大切にしてみてください。そうした積み重ねが、より良い生活や働き方につながっていくのではないかと思います。"""
        else:
            conclusion = """今回お話しした内容は、私自身の体験や考えに基づくものですが、同じような状況にある方の参考になれば嬉しいです。

日々の生活の中で感じたことを大切にしながら、前向きに取り組んでいきたいと思います。

皆さんもぜひ、日常の中で感じたことや工夫していることがあれば、大切にしてみてください。そうした積み重ねが、より良い生活や働き方につながっていくのではないかと思います。"""
        
        article_parts.append(conclusion)
        
        # 記事組み立て
        article = "".join(article_parts)
        
        total_length = len(article)
        print(f"📊 記事文字数: {total_length}文字")
        
        return article

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
        filename = f"style_based_article_{timestamp}.md"
        filepath = Path("/Users/manami/audio_to_article_new") / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(article)
            print(f"💾 記事保存完了: {filename}")
            return str(filepath)
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            return None

    def process_audio_file(self, audio_path):
        """音声ファイルの処理"""
        print(f"🔍 処理開始: {Path(audio_path).name}")
        
        # ファイル存在確認
        if not os.path.exists(audio_path):
            print(f"❌ ファイルが見つかりません: {audio_path}")
            return None
        
        # ファイルサイズ確認
        file_size = os.path.getsize(audio_path)
        print(f"📁 ファイルサイズ: {file_size / (1024*1024):.1f}MB")
        
        # 文字起こし
        transcript = self.transcribe_audio(audio_path)
        if not transcript:
            return None
        
        # 文字起こし完了
        print("\n🎉 文字起こしが完了しました！")
        
        # 記事生成
        article = self.generate_article_with_style(transcript)
        
        # 結果表示
        print("\n" + "=" * 80)
        print("📰 生成された記事:")
        print("=" * 80)
        print(article)
        print("=" * 80)
        
        # クリップボードにコピー
        print("\n📋 記事をクリップボードにコピー中...")
        self.copy_to_clipboard(article)
        
        # 保存
        saved_path = self.save_article(article)
        
        print(f"\n✅ 処理完了")
        if saved_path:
            print(f"💾 保存場所: {saved_path}")
        
        return article

    def interactive_mode(self):
        """インタラクティブモード"""
        while True:
            print("🎯 音声ファイルをドラッグ&ドロップするか、パスを入力してください")
            print("   📁 対応形式: mp3, wav, m4a, aac, flac, ogg, wma, mp4, mov等")
            print("   📋 ユーザーの文体で記事を生成します")
            print("   🚪 終了: 'q' を入力")
            audio_input = input("\n🎙️ ファイル: ").strip()
            
            if audio_input.lower() in ['q', 'quit', 'exit']:
                break
            
            if not audio_input:
                continue
            
            # パスの整理（ドラッグ&ドロップ対応）
            audio_path = audio_input.strip().strip('\n\r\t ')
            
            # クオート文字を削除
            quote_chars = ['"', "'", '`']
            for quote in quote_chars:
                if audio_path.startswith(quote) and audio_path.endswith(quote) and len(audio_path) > 1:
                    audio_path = audio_path[1:-1]
                    break
            
            # エスケープ文字処理
            escape_mappings = {
                '\\ ': ' ', '\\&': '&', '\\(': '(', '\\)': ')', '\\[': '[', '\\]': ']',
                '\\{': '{', '\\}': '}', '\\"': '"', "\\'": "'", '\\\\': '\\'
            }
            for escaped, unescaped in escape_mappings.items():
                audio_path = audio_path.replace(escaped, unescaped)
            
            if audio_path.startswith('file://'):
                audio_path = audio_path[7:]
                
            audio_path = os.path.expanduser(audio_path)
            audio_path = os.path.abspath(audio_path)
            
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

def main():
    parser = argparse.ArgumentParser(description='ユーザー文体学習型記事生成ツール')
    parser.add_argument('audio_file', nargs='?', help='音声ファイルのパス')
    
    args = parser.parse_args()
    
    generator = StyleBasedArticleGenerator()
    
    print("🎙️" + "=" * 50)
    print("   ユーザー文体学習型記事生成ツール v1.0")
    print("   音声 → 文字起こし → 文体ベース記事")
    print("=" * 52)
    print()
    
    if args.audio_file:
        # コマンドライン引数で音声ファイルが指定されている場合
        audio_path = args.audio_file.strip().strip('\n\r\t ')
        
        # パス処理
        quote_chars = ['"', "'", '`']
        for quote in quote_chars:
            if audio_path.startswith(quote) and audio_path.endswith(quote) and len(audio_path) > 1:
                audio_path = audio_path[1:-1]
                break
        
        escape_mappings = {
            '\\ ': ' ', '\\&': '&', '\\(': '(', '\\)': ')', '\\[': '[', '\\]': ']',
            '\\{': '{', '\\}': '}', '\\"': '"', "\\'": "'", '\\\\': '\\'
        }
        for escaped, unescaped in escape_mappings.items():
            audio_path = audio_path.replace(escaped, unescaped)
        
        if audio_path.startswith('file://'):
            audio_path = audio_path[7:]
            
        audio_path = os.path.expanduser(audio_path)
        audio_path = os.path.abspath(audio_path)
        
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