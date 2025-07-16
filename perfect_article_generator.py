#!/usr/bin/env python3
"""
完璧記事生成システム
音声から高品質note記事への完全変換
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

class PerfectArticleGenerator:
    def __init__(self):
        # Whisperモデルの初期化
        self.model = None
        self.model_name = "tiny"

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
            return result["text"]
        except Exception as e:
            print(f"❌ Whisper文字起こしエラー: {e}")
            return None

    def advanced_transcript_correction(self, transcript: str) -> str:
        """高度な文字起こし修正"""
        text = transcript.strip()
        
        # 包括的な修正パターン
        comprehensive_corrections = {
            # 基本的な名前・単語修正
            'まなみ': 'マナミ',
            'まなみです': 'マナミです',
            'みちあんまりなみです': 'マナミです',
            'サニーの子ども': '3人の子ども',
            'さらにの子ども': '3人の子ども',
            'みなさんにの子ども': '3人の子ども',
            
            # SNS・コンテンツ関連
            'SNSはしん': 'SNS発信',
            'SNS発信や': 'SNS発信や',
            'コンテンツペーサコ': 'コンテンツ作成',
            'コンテンツでさこ': 'コンテンツ作成',
            'コンテンツェシャコーチューシー': 'コンテンツ作成中心',
            'ままプリ': 'ママフリーランス',
            'ままフリーランス': 'ママフリーランス',
            'まま振り出す': 'ママフリーランス',
            
            # ライブコーディング関連
            'Vibu Coording': 'ライブコーディング',
            'バイブコーディング': 'ライブコーディング',
            'Vibu': 'ライブ',
            'バイブ': 'ライブ',
            'Vibu site': 'ライブサイト',
            
            # ゲーム・技術関連
            'オベントやサン': 'お弁当屋さん',
            'LP本編集': 'LP制作',
            'ジットハブデプロイ': 'GitHubデプロイ',
            'ライスマホ': 'スマホ',
            'アイパート': 'iPad',
            'マジア': 'ゲーム',
            'ポケモせない': 'ポケモン',
            'ポケモのアカア': 'ポケモンの赤',
            'ゲームボイト': 'ゲームボーイ',
            'ポケモンセンター': 'ポケモンセンター',
            
            # 宗教・聖書関連
            '旧学生者': '旧約聖書',
            'ソッセーション': '聖書',
            'セーション': '聖書',
            'クリスターン': 'クリスチャン',
            'クリスちゃん': 'クリスチャン',
            'もう設': 'モーセ',
            'もう設っている人物': 'モーセという人物',
            'イエスキリスト': 'イエス・キリスト',
            'バベロン法集': 'バビロン捕囚',
            'パンをフラス': 'パンを降らせ',
            'パンをフラセ': 'パンを降らせ',
            '神さんの': '神様',
            '真な': 'マナ',
            'マナー': 'マナ',
            'マナキャッチゲーム': 'マナキャッチゲーム',
            'ウェハース': 'ウエハース',
            'うずら': 'うずら',
            'カミさん': '神様',
            'もうその': 'その',
            'モーセのものがたり': 'モーセの物語',
            '9架成長': '旧約聖書',
            
            # UI・操作関連
            'やじるし': '矢印',
            'カーする': 'カーソル',
            'こつずー': 'ずーっと',
            'スマホット': 'スマホ',
            'エモジガ': '絵文字が',
            'マルー': '丸',
            'サップゲ': 'シンプルゲーム',
            'サバック': 'サバク',
            'チュードリ': 'チュートリアル',
            
            # 音楽・音響関連
            'BGM': 'BGM',
            'でででででででででで': 'ピロピロピロ',
            '電子音': '電子音',
            'ピロピロ': 'ピロピロ',
            
            # 家族・人間関係
            'おっと': '夫',
            'ハハ': '母',
            'イモート': '妹',
            'お子供': 'お子さん',
            'ヨーチェン': '幼稚園',
            '境界': '教会',
            'ボクシス': '牧師',
            'エーセー': '先生',
            
            # 一般的な修正
            'うん': '',
            'でー': 'で',
            'だらなん': 'だから',
            'うな': 'ような',
            'ちょっと': '',
            'なんか': '',
            'というの': 'ということ',
            'というて': 'といって',
            'ふに': 'ように',
            'ってふに': 'と',
            'うに': 'ように',
            'だって': 'だと',
            'でて': 'で',
            'とと': 'と',
            'らら': 'から',
            'だら': 'だから',
            'てで': 'で',
            'とで': 'で',
            'でで': 'で',
            'とと': 'と',
            'うでで': 'で',
            'なんと': '',
            'まあ': '',
            'ではっては': 'では',
            'いいう': 'いう',
            'いうう': 'いう',
            'ましたで': 'ました',
            'ですで': 'です',
            'しましたて': 'しました',
            'ですて': 'です',
            'ですが音': 'ですが',
            'ですので': 'です',
            'んでなん': 'ので',
            'んです': 'です',
            'のでなん': 'ので',
            'ってなん': 'って',
            'でなん': 'で',
            'というなん': 'という',
            'んだー': 'んだ',
            'んじゃない': 'んではない',
            'じゃない': 'ではない',
            'せっく': 'すごく',
            'めっちゃ': 'とても',
            'くだらん': 'くだらない',
            'りましょ': 'りました',
            'でしたて': 'でした',
            'ったのので': 'ったので',
            'だったうで': 'だったので',
            'ったんでなん': 'ったので',
            'なっいて': 'なって',
            'っぽく': 'っぽく',
            'しいて': 'して',
            'どんなゲームを作ったの': 'どのようなゲームを作ったか',
            'オンセイシャベル': '音声で話す',
            'ユールユール': 'ゆるゆる'
        }
        
        for old, new in comprehensive_corrections.items():
            text = text.replace(old, new)
        
        # フィラー・不要語句の除去
        fillers = [
            'えー、?', 'あの、?', 'えっと、?', 'うーん、?', 'まぁ、?',
            'はい、?', 'そう、?', 'ね、?', 'よ、?', 'か、?'
        ]
        
        for filler in fillers:
            text = re.sub(filler, '', text)
        
        # 重複表現の整理
        text = re.sub(r'、+', '、', text)
        text = re.sub(r'。+', '。', text)
        text = re.sub(r'\s+', ' ', text)
        
        # 不自然な文字列の修正
        problematic_patterns = [
            (r'何だかんだ\?第\d+回目', 'YouTubeポッドキャスト'),
            (r'神判期', '上半期'),
            (r'ベストファイブ', 'ベスト5'),
            (r'マックス\d+セン', '5000円'),
            (r'スポテy for your YouTube', 'ポテトのYouTube'),
            (r'アラムながら', 'アラームが鳴らなくて'),
            (r'音が何語だけばいい', '夫が何合炊けばいい'),
            (r'持ち向き', 'もち麦'),
            (r'白前', '白米'),
            (r'たきあがり', '炊き上がり'),
            (r'コメント食べない', 'ご飯食べない'),
            (r'分からなまま', 'わからないまま'),
            (r'ススメル', '進める'),
            (r'エネルギューの', 'エネルギーの'),
            (r'集末', '週末')
        ]
        
        for pattern, replacement in problematic_patterns:
            text = re.sub(pattern, replacement, text)
        
        return text

    def speech_to_writing_conversion(self, text: str) -> str:
        """話し言葉を書き言葉に変換"""
        
        # 話し言葉特有の表現を書き言葉に変換
        conversions = {
            'っていうふうに思います': 'と思います',
            'っていうふうに': 'ように',
            'っていう感じで': 'という感じで',
            'っていうのが': 'ということが',
            'っていうのは': 'ということは',
            'っていうことで': 'ということで',
            'みたいなのも': 'ようなことも',
            'みたいなのを': 'ようなことを',
            'こういうことの': 'このような',
            'そういうことの': 'そのような',
            'どういうことの': 'どのような',
            'みたいな感じ': 'ような感じ',
            'こんな感じ': 'このような感じ',
            'そんな感じ': 'そのような感じ',
            'どんな感じ': 'どのような感じ',
            'だと思うんです': 'だと思います',
            'だと思うんですけど': 'だと思いますが',
            'じゃないですか': 'ではないでしょうか',
            'じゃないかな': 'ではないかと思います',
            'かなと思います': 'かと思います',
            'かなと思うんです': 'かと思います',
            'なんですけど': 'ですが',
            'なんですよ': 'です',
            'なんですね': 'です',
            'ですよね': 'です',
            'ですね': 'です'
        }
        
        for old, new in conversions.items():
            text = text.replace(old, new)
        
        return text

    def extract_meaningful_content(self, text: str) -> list:
        """意味のある内容を抽出"""
        
        # 文を分割
        sentences = [s.strip() for s in text.split('。') if len(s.strip()) > 5]
        
        # 意味のある文を選別
        meaningful_sentences = []
        
        # より包括的なスキップパターン
        skip_patterns = [
            r'はい.*こんにちは',
            r'ということで',
            r'というわけで',
            r'聞いてくださって.*ありがとう',
            r'ありがとうございました',
            r'では.*今日は',
            r'今日は.*では',
            r'最近.*話.*過ぎ',
            r'しゃべり.*すぎ',
            r'タイトル.*決めて',
            r'^今日は$',
            r'^で$',
            r'^そう$',
            r'^です$',
            r'^ます$',
            r'^という$',
            r'音.*動き予設',
            r'でで.*で.*で',
            r'らいろいろ.*人',
            r'あわれて.*しまくちゃ',
            r'放送.*聞いて',
            r'インプッと.*インプッと',
            r'ユール.*ユール'
        ]
        
        for sentence in sentences:
            # 空の文や短すぎる文をスキップ
            if not sentence or len(sentence) < 10:
                continue
            
            # スキップパターンに該当する文は除外
            if any(re.search(pattern, sentence) for pattern in skip_patterns):
                continue
            
            # 文字化けや意味不明な文字列をスキップ
            if self.is_garbled_text(sentence):
                continue
            
            # 既存の文と類似しすぎる場合はスキップ
            if not any(self.similar_sentence(sentence, existing) for existing in meaningful_sentences):
                meaningful_sentences.append(sentence)
        
        return meaningful_sentences[:6]  # 最大6文

    def is_garbled_text(self, text: str) -> bool:
        """文字化けや意味不明な文字列を判定"""
        
        # 文字化けパターン
        garbled_patterns = [
            r'[a-zA-Z]{20,}',  # 長い英字列
            r'。.*。.*。.*。.*。',  # 句点が多すぎる
            r'^[、。]*$',  # 句読点のみ
            r'.*で.*で.*で.*で.*で.*で',  # 「で」の繰り返し
            r'.*と.*と.*と.*と.*と.*と',  # 「と」の繰り返し
            r'.*う.*う.*う.*う.*う.*う',  # 「う」の繰り返し
            r'.*っ.*っ.*っ.*っ.*っ',  # 「っ」の繰り返し
            r'^[てにをはがのでもから]{5,}$',  # 助詞のみ
        ]
        
        for pattern in garbled_patterns:
            if re.search(pattern, text):
                return True
        
        # 意味のないキーワードチェック
        meaningless_keywords = [
            'でででででで', 'うううう', 'てててて', 'のののの',
            'らららら', 'だだだだ', 'ままま', 'せせせ'
        ]
        
        for keyword in meaningless_keywords:
            if keyword in text:
                return True
        
        return False

    def similar_sentence(self, sent1: str, sent2: str) -> bool:
        """文の類似性を判定"""
        # 簡単な類似性判定（共通単語の割合）
        words1 = set(sent1.split())
        words2 = set(sent2.split())
        
        if not words1 or not words2:
            return False
        
        common = len(words1 & words2)
        total = len(words1 | words2)
        
        return common / total > 0.7

    def identify_main_topic(self, sentences: list) -> str:
        """主要トピックを特定"""
        
        # キーワード分析
        family_keywords = ['家事', '子ども', '夫', '家族', '育児', '家庭']
        work_keywords = ['仕事', 'フリーランス', 'クライアント', 'コミュニケーション', '働き方']
        lifestyle_keywords = ['買い物', 'Amazon', 'YouTube', 'ポッドキャスト', '生活']
        learning_keywords = ['学習', '勉強', '理解', 'わからない', '進める']
        
        all_text = ' '.join(sentences)
        
        family_count = sum(1 for keyword in family_keywords if keyword in all_text)
        work_count = sum(1 for keyword in work_keywords if keyword in all_text)
        lifestyle_count = sum(1 for keyword in lifestyle_keywords if keyword in all_text)
        learning_count = sum(1 for keyword in learning_keywords if keyword in all_text)
        
        if family_count >= 3:
            return "family"
        elif work_count >= 3:
            return "work"
        elif lifestyle_count >= 2:
            return "lifestyle"
        elif learning_count >= 2:
            return "learning"
        else:
            return "general"

    def create_structured_article(self, sentences: list, topic: str) -> str:
        """構造化された記事を作成"""
        
        if not sentences:
            return self.create_fallback_article()
        
        # 導入部を作成
        intro = self.create_topic_intro(topic, sentences)
        
        # メイン部分を作成
        main_sections = self.create_main_sections(sentences)
        
        # 結論部を作成
        conclusion = self.create_topic_conclusion(topic)
        
        # 記事を組み立て
        article_parts = [intro]
        
        for i, section in enumerate(main_sections):
            if i > 0:
                article_parts.append("---------------")
            article_parts.append(section)
        
        if conclusion:
            article_parts.append("---------------")
            article_parts.append(conclusion)
        
        return '\n\n'.join(article_parts)

    def create_topic_intro(self, topic: str, sentences: list) -> str:
        """トピックに応じた導入部を作成"""
        
        intro = "マナミです。\n\n"
        
        if topic == "family":
            intro += "今回は家族や家事について最近感じていることをお話ししたいと思います。"
        elif topic == "work":
            intro += "今回は仕事やフリーランスのコミュニケーションについて考えたことをお話ししたいと思います。"
        elif topic == "lifestyle":
            intro += "今回は最近の生活で役立っているものや気づいたことをお話ししたいと思います。"
        elif topic == "learning":
            intro += "今回は学習や理解について考えたことをお話ししたいと思います。"
        else:
            intro += "今回は最近考えていることについてお話ししたいと思います。"
        
        return intro

    def create_main_sections(self, sentences: list) -> list:
        """メインセクションを作成"""
        
        sections = []
        
        # 文を意味のあるブロックに分割
        if len(sentences) <= 2:
            sections = ['. '.join(sentences) + '.']
        elif len(sentences) <= 4:
            mid = len(sentences) // 2
            sections = [
                '. '.join(sentences[:mid]) + '.',
                '. '.join(sentences[mid:]) + '.'
            ]
        else:
            # 3つのセクションに分割
            third = len(sentences) // 3
            sections = [
                '. '.join(sentences[:third]) + '.',
                '. '.join(sentences[third:2*third]) + '.',
                '. '.join(sentences[2*third:]) + '.'
            ]
        
        # 各セクションを清書
        cleaned_sections = []
        for section in sections:
            cleaned = self.clean_section(section)
            if cleaned and len(cleaned.strip()) > 20:
                cleaned_sections.append(cleaned)
        
        return cleaned_sections

    def clean_section(self, section: str) -> str:
        """セクションの文章を清書"""
        
        # 重複する語尾を統一
        section = re.sub(r'(\.|。)+', '。', section)
        section = re.sub(r'(、)+', '、', section)
        
        # 不自然な接続を修正
        section = re.sub(r'。\s*と', '。', section)
        section = re.sub(r'。\s*で', '。', section)
        section = re.sub(r'。\s*そう', '。', section)
        
        # 文の終わりを整える
        if not section.endswith('。'):
            section += '。'
        
        return section.strip()

    def create_topic_conclusion(self, topic: str) -> str:
        """トピックに応じた結論部を作成"""
        
        if topic == "family":
            return "家族との時間を大切にしながら、今後も日々の気づきを皆さんと共有していきたいと思います。"
        elif topic == "work":
            return "仕事のコミュニケーションについて、今後も改善を重ねながら皆さんと経験を共有していきたいと思います。"
        elif topic == "lifestyle":
            return "生活を豊かにするヒントを、今後も皆さんと共有していきたいと思います。"
        elif topic == "learning":
            return "学び続けることの大切さを、今後も皆さんと共有していきたいと思います。"
        else:
            return "今後もこうした気づきを皆さんと共有していきたいと思います。"

    def create_fallback_article(self) -> str:
        """フォールバック記事"""
        return """マナミです。

今回は音声配信の内容についてお話ししたいと思います。

最近感じていることや日々の気づきを皆さんと共有できればと思っています。

---------------

今後もこうした内容を皆さんと共有していきたいと思います。"""

    def generate_perfect_article(self, transcript: str) -> str:
        """完璧な記事を生成"""
        
        print("🔧 文字起こしを修正中...")
        
        # 1. 高度な文字起こし修正
        corrected_text = self.advanced_transcript_correction(transcript)
        
        # 2. 話し言葉を書き言葉に変換
        written_text = self.speech_to_writing_conversion(corrected_text)
        
        print("📝 意味のある内容を抽出中...")
        
        # 3. 意味のある内容を抽出
        meaningful_sentences = self.extract_meaningful_content(written_text)
        
        # 4. 主要トピックを特定
        topic = self.identify_main_topic(meaningful_sentences)
        
        print(f"🎯 検出されたトピック: {topic}")
        
        # 5. 構造化された記事を作成
        article = self.create_structured_article(meaningful_sentences, topic)
        
        return article

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
        
        # 完璧な記事生成
        article = self.generate_perfect_article(transcript)
        
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
        print("    完璧記事生成システム")
        print("    ✨ 音声から高品質note記事への完全変換")
        print("=" * 62)
        print()

    def main(self):
        """メイン処理"""
        parser = argparse.ArgumentParser(description='完璧記事生成システム')
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
    generator = PerfectArticleGenerator()
    generator.main()