#!/usr/bin/env python3
"""
改良版音声記事生成ツール
音声ファイル → 高精度文字起こし → note風記事生成
"""

import os
import sys
import argparse
from pathlib import Path
import whisper
import re
from datetime import datetime
import pyperclip

class EnhancedAudioArticleGenerator:
    def __init__(self):
        self.model = None
        self.model_name = "medium"  # 日本語精度向上のためmediumモデル使用
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
                print("💡 baseモデルにフォールバック中...")
                try:
                    self.model_name = "base"
                    self.model = whisper.load_model(self.model_name)
                    print("✅ baseモデル読み込み完了")
                except Exception as e2:
                    print(f"❌ baseモデルも読み込めませんでした: {e2}")
                    sys.exit(1)

    def transcribe_audio(self, audio_path: str) -> str:
        """高精度音声文字起こし"""
        try:
            self.load_whisper_model()
            print("🎵 高精度文字起こし処理中...")
            
            # 日本語特化の高品質設定
            enhanced_prompt = (
                "マナミです。3人の子どもを育てながらSNS発信やコンテンツ作成を中心に"
                "お仕事をしているママフリーランスです。今日は皆さんにお話ししたい"
                "ことがあります。以下は日本語の音声配信の内容です。"
            )
            
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
                initial_prompt=enhanced_prompt
            )
            
            transcript = result["text"]
            print(f"✅ 文字起こし完了: {len(transcript)}文字")
            
            # 基本的な句読点整理
            transcript = self.add_punctuation(transcript)
            return transcript
            
        except Exception as e:
            print(f"❌ 文字起こしエラー: {e}")
            return None

    def add_punctuation(self, text):
        """句読点の自動挿入と整理"""
        # 長い文の区切りに句読点を追加
        text = re.sub(r'([です|ます|だと思います|ということです])\s*([あそでまそれで今])', r'\1。\2', text)
        text = re.sub(r'([でしょう|ですね|ますね])\s*([あそでまそれで今])', r'\1。\2', text)
        
        # 不自然な連続スペースを除去
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def clean_transcript_enhanced(self, text):
        """高度な文字起こしクリーニング"""
        text = text.strip()
        
        # 基本的な音声認識エラーの修正
        corrections = {
            'まなみ': 'マナミ', 'マナみ': 'マナミ', '学み': 'マナミ', 'まにみ': 'マナミ',
            'さにの子ども': '3人の子ども', 'さ人の子ども': '3人の子ども', 'サニーの子ども': '3人の子ども',
            '3人の子供たち': '3人の子ども', '子供': '子ども', '子どもたち': '子ども',
            'SNSはしん': 'SNS発信', 'SNSのつう': 'SNS運用', 'SNS4サポート': 'SNS運用サポート',
            'ままフリー': 'ママフリーランス', 'ままプリー': 'ママフリーランス', 'ままプリランス': 'ママフリーランス',
            'コンテンツペーサク': 'コンテンツ作成', 'コンテンツ製作': 'コンテンツ作成',
            'メンバーシーピ': 'メンバーシップ', 'メンバーしップ': 'メンバーシップ',
            '伴奏型': '伴走型', 'バンソー型': '伴走型',
            'インスタ': 'Instagram', 'フォロー': 'フォロー'
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text

    def extract_main_topic_enhanced(self, text):
        """メイントピックの高精度抽出"""
        # より詳細なパターンマッチング
        topic_patterns = [
            (r'発信.*ジャンル|複数.*発信|アカウント.*分け|プラットフォーム.*分け', '発信ジャンルが複数あるときの考え方'),
            (r'値段.*つける|価格設定|お金.*取る|有料.*サービス|メンバーシップ.*価格', '自分のサービスに値段をつけること'),
            (r'働き方|ママフリーランス|仕事.*育児|子育て.*仕事', 'ママフリーランスとしての働き方'),
            (r'SNS.*運用|Instagram.*運用|アカウント.*運用', 'SNS運用について'),
            (r'コミュニケーション|やり取り|相手.*立場|伝え方', 'コミュニケーションの重要性'),
            (r'AI.*活用|AI.*相談|AIと.*壁打ち', 'AIの活用について'),
            (r'コンテンツ.*作成|情報.*発信|投稿.*作成', '情報発信について'),
            (r'子ども.*育て|家事.*育児|ワンオペ|保育園', '子育てと仕事の両立'),
            (r'時間.*使い方|生活|日常|ライフスタイル', '日々の生活について')
        ]
        
        for pattern, topic in topic_patterns:
            if re.search(pattern, text):
                return topic
        
        return '最近考えていること'

    def extract_structured_content(self, text):
        """構造化されたコンテンツ抽出"""
        # 文を分割
        sentences = re.split(r'[。！？]', text)
        
        # 重要なコンテンツを分類
        intro_content = []
        main_content = []
        examples = []
        conclusions = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:
                continue
                
            # 導入部分の特定
            if any(word in sentence for word in ['今日は', '最近', 'お話しします', '考えています']):
                intro_content.append(sentence)
            
            # 具体例の特定
            elif any(word in sentence for word in ['例えば', '実際に', '具体的に', 'という感じで']):
                examples.append(sentence)
            
            # 結論部分の特定
            elif any(word in sentence for word in ['まとめ', 'つまり', 'ということで', 'と思います']):
                conclusions.append(sentence)
            
            # メインコンテンツ
            elif any(indicator in sentence for indicator in [
                'メンバーシップ', 'SNS運用', 'アカウント', 'Instagram', 
                'プラットフォーム', 'フォロー', 'サービス', 'コンテンツ',
                'と思っている', 'を始めて', 'をやって', 'ということで',
                'と感じて', 'を考えて', 'が必要', 'をしようと'
            ]):
                cleaned = self.remove_fillers_enhanced(sentence)
                if len(cleaned) > 20:
                    main_content.append(cleaned)
        
        return {
            'intro': intro_content[:3],
            'main': main_content,
            'examples': examples,
            'conclusions': conclusions
        }

    def remove_fillers_enhanced(self, text):
        """高度なフィラー語除去"""
        # 基本的なフィラー語
        fillers = [
            r'えー+、?', r'あの+、?', r'えっと+、?', r'うーん+、?', r'まぁ+、?',
            r'なんか+、?', r'そう+、?', r'んー+、?', r'ちょっと+、?'
        ]
        
        for filler in fillers:
            text = re.sub(filler, '', text)
        
        # 冗長な表現の簡潔化
        redundant_patterns = [
            (r'だと思うんですけど、?', 'と思います'),
            (r'なんですけど、?', 'です'),
            (r'っていう風に、?', 'という形で'),
            (r'ということなんですよね', 'ということです'),
            (r'という感じで、?', 'ということで'),
            (r'みたいな感じ、?', 'のような'),
            (r'って感じ、?', 'という')
        ]
        
        for pattern, replacement in redundant_patterns:
            text = re.sub(pattern, replacement, text)
        
        # スペースの正規化
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 文末の整理
        if text and not text.endswith(('。', '！', '？')):
            if re.search(r'[ですますたしいない]$', text):
                text += '。'
        
        return text

    def create_note_style_article(self, content_data, main_topic):
        """note風記事の生成"""
        article_parts = []
        
        # タイトル生成
        title = self.generate_title(main_topic, content_data)
        article_parts.append(f"# {title}")
        article_parts.append("")
        
        # 導入部
        intro = self.create_enhanced_introduction(main_topic, content_data)
        article_parts.append(intro)
        article_parts.append("")
        
        # メインコンテンツをセクションに分割
        sections = self.create_structured_sections(content_data)
        
        for i, section in enumerate(sections):
            if section['title'] and section['content']:
                article_parts.append(f"## {section['title']}")
                article_parts.append("")
                article_parts.append(section['content'])
                article_parts.append("")
        
        # 結論部
        conclusion = self.create_enhanced_conclusion(main_topic, content_data)
        article_parts.append("## まとめ")
        article_parts.append("")
        article_parts.append(conclusion)
        
        return "\n".join(article_parts)

    def generate_title(self, main_topic, content_data):
        """タイトル生成"""
        if '発信ジャンル' in main_topic:
            return '発信したいジャンルが複数あるときの考え方'
        elif '値段' in main_topic:
            return '自分のサービスに価格をつけるということ'
        elif 'SNS運用' in main_topic:
            return 'SNS運用で大切にしていること'
        elif 'ママフリーランス' in main_topic:
            return 'ママフリーランスとして働くということ'
        else:
            # コンテンツから重要なキーワードを抽出してタイトル化
            all_content = ' '.join([' '.join(content_data['main'])])
            if 'アカウント' in all_content and '複数' in all_content:
                return '複数の発信をしたいときのアカウント運用'
            return main_topic

    def create_enhanced_introduction(self, main_topic, content_data):
        """強化された導入部作成"""
        intro_base = "マナミです。\n\n"
        
        # コンテンツから導入部を生成
        if content_data['intro']:
            topic_intro = self.remove_fillers_enhanced(content_data['intro'][0])
            if len(topic_intro) > 20:
                intro_base += f"{topic_intro}。\n\n"
        
        # 主要テーマに基づく背景説明
        if '発信ジャンル' in main_topic:
            context = "発信したい内容やジャンルが複数あるとき、どう考えればいいのか。今回は実際のSNS運用サポートの事例を通して、そのヒントをお伝えしたいと思います。"
        elif '値段' in main_topic:
            context = "これまで無料で提供してきたサービスに価格をつけることについて、改めて考える機会がありました。そこで感じたことを皆さんと共有したいと思います。"
        elif 'SNS運用' in main_topic:
            context = "SNS運用について、日々感じることや大切にしていることをお話ししたいと思います。"
        else:
            context = "日々の経験の中で感じたことを、皆さんと共有したいと思います。"
        
        return intro_base + context

    def create_structured_sections(self, content_data):
        """構造化されたセクション作成"""
        sections = []
        main_content = content_data['main']
        examples = content_data['examples']
        
        if not main_content:
            return self.create_fallback_sections()
        
        # メインコンテンツを3つのセクションに分割
        section_size = max(1, len(main_content) // 3)
        
        section_titles = [
            "実際の事例から",
            "具体的な考え方", 
            "私なりの結論"
        ]
        
        for i in range(3):
            start_idx = i * section_size
            end_idx = start_idx + section_size if i < 2 else len(main_content)
            
            section_content = main_content[start_idx:end_idx]
            
            if section_content:
                # セクション内容を構成
                content_text = ""
                
                for content in section_content[:3]:  # 最大3つの内容
                    content_text += content + "。\n\n"
                
                # 例があれば追加
                if i == 1 and examples:  # 2番目のセクションに例を追加
                    example_text = self.remove_fillers_enhanced(examples[0]) if examples else ""
                    if example_text:
                        content_text += f"例えば、{example_text}。\n\n"
                
                sections.append({
                    'title': section_titles[i],
                    'content': content_text.strip()
                })
        
        return sections

    def create_fallback_sections(self):
        """フォールバック用セクション"""
        return [
            {
                'title': '最近考えていること',
                'content': '日々の生活や仕事の中で、いろいろと考えることがあります。3人の子どもを育てながらママフリーランスとして働く中で、思うようにいかないこともありますが、その分学ぶことも多いです。'
            },
            {
                'title': '実際にやってみて',
                'content': '実際に体験してみると、想像していた以上に難しい部分もありました。でも、そうした経験を通して新しい気づきもたくさんありました。一つひとつ丁寧に取り組んでいくことの大切さを感じています。'
            },
            {
                'title': 'これからのこと',
                'content': '完璧を求めすぎず、その時その時でできることをやっていく。そんな姿勢が大切なのかもしれないと思います。'
            }
        ]

    def create_enhanced_conclusion(self, main_topic, content_data):
        """強化された結論部作成"""
        # 結論コンテンツがあれば使用
        conclusion_base = ""
        if content_data['conclusions']:
            conclusion_base = self.remove_fillers_enhanced(content_data['conclusions'][0]) + "。\n\n"
        
        # テーマ別の結論
        if '発信ジャンル' in main_topic:
            specific_conclusion = (
                "発信したいジャンルが複数あるときは：\n\n"
                "1. **まずは1つのアカウントでできることを考える**\n"
                "2. **自分らしさやストーリー性でつなげられないか検討する**\n"
                "3. **明らかに分けたい場合はプラットフォームを分ける**\n"
                "4. **「何屋さんか」が分からなくなる混ぜすぎは避ける**\n\n"
            )
        elif '値段' in main_topic:
            specific_conclusion = "お金を取ることは、より価値のあるサービスを提供するために必要なステップだと感じています。\n\n"
        elif 'SNS運用' in main_topic:
            specific_conclusion = "SNS運用は試行錯誤の連続ですが、その中で得られる学びや出会いに感謝しています。\n\n"
        else:
            specific_conclusion = "日々の経験を大切にしながら、前向きに取り組んでいきたいと思います。\n\n"
        
        general_conclusion = (
            "何か皆さんの参考になれば嬉しいです。"
            "皆さんもぜひ、日常の中で感じたことや工夫していることがあれば、"
            "大切にしてみてください。そうした積み重ねが、より良い生活や働き方に"
            "つながっていくのではないかと思います。"
        )
        
        return conclusion_base + specific_conclusion + general_conclusion

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
        filename = f"note_article_{timestamp}.md"
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
        
        # 高精度文字起こし
        transcript = self.transcribe_audio(audio_path)
        if not transcript:
            return None
        
        # 高度なクリーニング
        cleaned_text = self.clean_transcript_enhanced(transcript)
        print(f"🧹 クリーニング完了: {len(cleaned_text)}文字")
        
        # メイントピック抽出
        main_topic = self.extract_main_topic_enhanced(cleaned_text)
        print(f"🎯 主要テーマ: {main_topic}")
        
        # 構造化コンテンツ抽出
        content_data = self.extract_structured_content(cleaned_text)
        print(f"📊 抽出コンテンツ: メイン{len(content_data['main'])}個, 例{len(content_data['examples'])}個")
        
        # note風記事生成
        article = self.create_note_style_article(content_data, main_topic)
        
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
        print(f"📊 最終記事文字数: {len(article)}文字")
        if saved_path:
            print(f"💾 保存場所: {saved_path}")
        
        return article

    def interactive_mode(self):
        """インタラクティブモード"""
        print("🎙️" + "=" * 50)
        print("   改良版音声記事生成ツール v2.0")
        print("   音声 → 高精度文字起こし → note風記事")
        print("=" * 52)
        print()
        
        while True:
            print("🎯 音声ファイルをドラッグ&ドロップするか、パスを入力してください")
            print("   📁 対応形式: mp3, wav, m4a, aac, flac, ogg, wma, mp4, mov等")
            print("   📋 改良点: 高精度文字起こし + note風記事構成")
            print("   🚪 終了: 'q' を入力")
            
            audio_input = input("\n🎙️ ファイル: ").strip()
            
            if audio_input.lower() in ['q', 'quit', 'exit']:
                break
            
            if not audio_input:
                continue
            
            # パスの整理（ドラッグ&ドロップ対応）
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
    parser = argparse.ArgumentParser(description='改良版音声記事生成ツール')
    parser.add_argument('audio_file', nargs='?', help='音声ファイルのパス')
    
    args = parser.parse_args()
    
    generator = EnhancedAudioArticleGenerator()
    
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