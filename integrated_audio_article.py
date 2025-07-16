#!/usr/bin/env python3
"""
統合音声記事生成ツール
音声ファイル → 文字起こし → note記事 一括処理
"""

import os
import sys
import argparse
from pathlib import Path
import whisper
import re
from datetime import datetime
import pyperclip

class IntegratedAudioArticleGenerator:
    def __init__(self):
        self.model = None
        self.model_name = "base"  # 高速処理
        self.target_length = 2500  # 約2500文字

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

    def extract_main_topic(self, text):
        """主要テーマを抽出"""
        topic_patterns = [
            (r'値段をつける|価格設定|お金.*取る|有料.*サービス|メンバーシップ', '自分のサービスに値段をつけること'),
            (r'働き方|フリーランス|仕事.*育児|ママフリーランス', 'ママフリーランスとしての働き方'),
            (r'コミュニケーション|やり取り|相手.*立場|伝え方', 'コミュニケーションの重要性'),
            (r'AI.*活用|AI.*相談|AIと.*壁打ち', 'AIの活用について'),
            (r'SNS.*発信|コンテンツ.*作成|情報.*発信', '情報発信について'),
            (r'子ども.*育て|家事.*育児|ワンオペ|保育園', '子育てと仕事の両立'),
            (r'生活|日常|ライフスタイル|時間.*使い方', '日々の生活について')
        ]
        
        for pattern, topic in topic_patterns:
            if re.search(pattern, text):
                return topic
        
        return '最近考えていること'

    def extract_key_content(self, text):
        """重要な内容を抽出"""
        sentences = re.split(r'[。！？]', text)
        concrete_content = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            # 具体的な内容を示すキーワード
            concrete_indicators = [
                'メンバーシップ', '8月から', 'SNS運用サポート', '価格', '単価', '値段',
                '8000円', '15000円', '1万5千', '無料', '有料', 'プラン',
                'AI', '壁打ち', 'サービス', 'コンテンツ', '音声配信',
                '実は', '具体的に', '例えば', 'つまり', 'そうなんです'
            ]
            
            # 体験や考えを表す表現
            experience_indicators = [
                'と思っている', 'を始めて', 'をやって', 'ということで',
                'と感じて', 'を考えて', 'が必要', 'をしようと'
            ]
            
            has_concrete = any(indicator in sentence for indicator in concrete_indicators)
            has_experience = any(indicator in sentence for indicator in experience_indicators)
            
            if has_concrete or has_experience:
                cleaned = self.remove_fillers(sentence)
                if len(cleaned) > 15:
                    concrete_content.append(cleaned + '。')
        
        # 3つのグループに分ける
        if len(concrete_content) >= 3:
            third = len(concrete_content) // 3
            group1 = concrete_content[:third] if third > 0 else concrete_content[:1]
            group2 = concrete_content[third:2*third] if third > 0 else concrete_content[1:2] if len(concrete_content) > 1 else []
            group3 = concrete_content[2*third:] if third > 0 else concrete_content[2:] if len(concrete_content) > 2 else []
            
            content_blocks = []
            if group1:
                content_blocks.append('\n\n'.join(group1[:3]))
            if group2:
                content_blocks.append('\n\n'.join(group2[:3]))
            if group3:
                content_blocks.append('\n\n'.join(group3[:3]))
            
            return content_blocks
        
        return []

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

    def create_introduction(self, main_topic):
        """導入部を作成"""
        if '値段' in main_topic or 'サービス' in main_topic:
            importance = 'これまで無料で提供してきたサービスに価格をつけることの意味について、改めて考える機会がありました'
        elif '働き方' in main_topic:
            importance = '子育てと仕事を両立する中で感じることがたくさんありました'
        elif 'コミュニケーション' in main_topic:
            importance = '相手の立場を考えたやり取りの大切さを実感する出来事がありました'
        elif 'AI' in main_topic:
            importance = 'AIを日常的に活用する中で感じることがありました'
        elif '発信' in main_topic:
            importance = '情報発信のあり方について考え直すきっかけがありました'
        elif '子育て' in main_topic:
            importance = '3人の子どもを育てながら働く日々の中で、色々と思うことがありました'
        else:
            importance = '日々の生活の中で感じることがありました'
        
        conclusion_statement = f'{main_topic}について、{importance}。'
        intro = f"マナミです。\n\n{conclusion_statement}\n\n今回は、そんな体験から考えたことを皆さんと共有したいと思います。"
        
        return intro

    def create_main_content(self, key_content):
        """主要内容を作成"""
        if not key_content or all(not content.strip() for content in key_content):
            return self.create_fallback_content()
        
        sections = []
        
        for i, content_block in enumerate(key_content):
            if content_block and content_block.strip():
                section = content_block.strip()
                
                if len(section) < 200:
                    if i == 0:
                        section += '\n\nこのことについて、改めて考える機会がありました。'
                    elif i == 1:
                        section += '\n\n実際にやってみると、思っていた以上に色々と考えることがありました。'
                    else:
                        section += '\n\nこうした経験を通して、新しい気づきもありました。'
                
                sections.append(section)
        
        if not sections:
            return self.create_fallback_content()
        
        return '\n\n---------------\n\n'.join(sections)

    def create_fallback_content(self):
        """フォールバック用のメインコンテンツ"""
        return """最近、日々の生活の中で考えることがありました。

3人の子どもを育てながらママフリーランスとして働く中で、思うようにいかないことも多いですが、その分学ぶことも多いです。

---------------

実際に体験してみると、想像していた以上に難しい部分もありました。

でも、そうした経験を通して新しい気づきもたくさんありました。一つひとつ丁寧に取り組んでいくことの大切さを感じています。

---------------

今回の経験から、改めて学ぶことがありました。

完璧を求めすぎず、その時その時でできることをやっていく。そんな姿勢が大切なのかもしれないと思います。"""

    def create_conclusion(self, main_topic):
        """結論部を作成"""
        if '値段' in main_topic or 'サービス' in main_topic:
            specific_thought = 'お金を取ることは、より価値のあるサービスを提供するために必要なステップだと感じています。'
        elif '働き方' in main_topic:
            specific_thought = 'ママフリーランスという働き方には大変さもありますが、その分得られるものも大きいと思います。'
        elif 'コミュニケーション' in main_topic:
            specific_thought = '相手の立場を考えたコミュニケーションの大切さを、改めて実感しています。'
        elif 'AI' in main_topic:
            specific_thought = 'AIを上手に活用することで、働き方や生活の質を向上させていけると思います。'
        elif '発信' in main_topic:
            specific_thought = '情報発信を通じて、多くの方とつながり学び合えることに感謝しています。'
        elif '子育て' in main_topic:
            specific_thought = '子育てと仕事の両立は簡単ではありませんが、その中で得られる学びも多いです。'
        else:
            specific_thought = '日々の生活の中で感じたことを大切にしながら、前向きに取り組んでいきたいと思います。'
        
        conclusion = f"""今回お話しした内容は、私自身の体験や考えに基づくものですが、同じような状況にある方の参考になれば嬉しいです。

{specific_thought}

皆さんもぜひ、日常の中で感じたことや工夫していることがあれば、大切にしてみてください。そうした積み重ねが、より良い生活や働き方につながっていくのではないかと思います。"""
        
        return conclusion

    def generate_article(self, transcript):
        """記事生成メイン"""
        print("🔧 文字起こしを記事に変換中...")
        
        # クリーニング
        clean_text = self.clean_transcript(transcript)
        print(f"📝 クリーニング完了: {len(clean_text)}文字")
        
        # 主要テーマ抽出
        main_topic = self.extract_main_topic(clean_text)
        print(f"🎯 主要テーマ: {main_topic}")
        
        # 重要内容抽出
        key_content = self.extract_key_content(clean_text)
        print(f"📄 抽出された重要文: {len(key_content)}個")
        
        # 各セクション作成
        introduction = self.create_introduction(main_topic)
        main_content = self.create_main_content(key_content)
        conclusion = self.create_conclusion(main_topic)
        
        # 記事組み立て
        article = f"{introduction}\n\n---------------\n\n{main_content}\n\n---------------\n\n{conclusion}"
        
        total_length = len(article)
        print(f"📊 記事文字数: {total_length}文字（目標: {self.target_length}文字）")
        
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
        filename = f"article_integrated_{timestamp}.md"
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
        """音声ファイルの統合処理"""
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
        
        # 記事生成
        article = self.generate_article(transcript)
        
        # 結果表示
        print("\n" + "=" * 80)
        print("📰 生成された記事:")
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
        while True:
            print("🎯 音声ファイルをドラッグ&ドロップするか、パスを入力してください")
            print("   📁 対応形式: mp3, wav, m4a, aac, flac, ogg, wma, mp4, mov等")
            print("   📋 ドラッグ&ドロップ: Finderから直接ファイルをドラッグしてください")
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
    parser = argparse.ArgumentParser(description='統合音声記事生成ツール')
    parser.add_argument('audio_file', nargs='?', help='音声ファイルのパス')
    
    args = parser.parse_args()
    
    generator = IntegratedAudioArticleGenerator()
    
    print("🎙️" + "=" * 50)
    print("   統合音声記事生成ツール v5.0")
    print("   音声 → 文字起こし → note記事")
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