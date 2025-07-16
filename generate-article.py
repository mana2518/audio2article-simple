#!/usr/bin/env python3
"""
記事生成専用ツール
文字起こしテキスト → 読みやすい記事生成 → クリップボード
"""

import os
import sys
import argparse
import re
from pathlib import Path
import pyperclip

class ArticleGenerator:
    def __init__(self):
        self.sample_articles = self.load_sample_articles()

    def load_sample_articles(self):
        """文体学習用のサンプル記事（実際のnote記事を参考）"""
        return {
            "lifestyle": """マナミです。

今週は子どもが熱を出し、夫も体調を崩し、誰かしらを自宅保育してるので家事育児を一人でまわしており仕事がなかなか進みません…。

そんな中でも、日々の生活の中で考えることがあったのでお話ししたいと思います。

3人の子どもを育てながらママフリーランスとして働いている中で、毎日が試行錯誤の連続です。完璧にはいかないけれど、その中で学ぶことや気づくことがたくさんあります。

今回は、そんな日常の中で感じたことについて皆さんと共有したいと思います。

---------------

毎日の生活の中には、小さな発見や学びがたくさんあります。時には大変なこともありますが、そうした経験も含めて成長につながっていると感じています。

実際に体験してみることで初めて分かることも多く、挑戦することの大切さを実感しています。

完璧を求めすぎず、その時その時でできることをやっていく。そんな姿勢を大切にしながら過ごしています。

---------------

今後もこうした日々の気づきを皆さんと共有していきたいと思います。一緒に学び合いながら成長していければと思います。

皆さんもぜひ、日常の小さな気づきや工夫を大切にしてみてください。そうした積み重ねが、より良い生活につながっていくのではないかと思います。""",
            
            "work": """マナミです。

フリーランスとして働く中で、最近特に感じていることがあります。

どんなにスキルや実績があっても、「この人とやり取りするの、なんだか疲れるな…」と思われてしまったら、仕事につながらない。これってとても大切なことだと思うんですよね。

私自身、「コミュニケーションコストが高い人とは仕事をしない」と決めています。それは相手を否定しているのではなく、自分が消耗しないための自己防衛策です。

もちろん、私も昔からできていたわけではなく、たくさんの失敗と反省を繰り返して、相手の立場を考えることの大切さを学んできました。

---------------

つい最近も、PR案件でちょっとした反省がありました。

企業の方に「希望の商品はどれですか？」と聞かれ、希望だけを伝えて返信してしまったんです。当然、その次は発送先の住所を聞かれるに決まっているのに、それを先回りして伝えなかったせいで、メールのやり取りが1往復増えてしまいました。

本当にちっちゃいことなんですけど、「相手が次にどう動くか」を考えて配慮するだけで、お互いの作業効率が格段に上がるんですよね。

私が大切にしているのは「状況の報告」と「具体的なお願い」をセットで伝えること。状況にもよりますが、なるべくこちらから選択肢を提示して、少しでも相手が判断しやすいように心がけています。

---------------

私もまだまだ失敗ばかりで反省は多いです。でも、そうした経験も含めて学んでいけたらと思います。

フリーランスの働き方では、こうしたコミュニケーションがとても重要だと日々感じています。皆さんも、お互いに気持ちよく働けるような関係作りを大切にしていけたらいいですね。""",
            
            "technology": """マナミです。

今日は「AIの業務活用」について考えたことをお話ししようと思います。

「AIブームの中、業務活用は3割強にとどまる」というニュースを見て、色々と思うことがありました。特に、年代別で見ると「20代の6割が活用する一方、50代はわずか3割」という結果も興味深いですよね。

さらに面白いと感じたのは、「生成AIの使用頻度が高い人ほど、AIによる人材の置き換えに不安を感じている」という結果です。

これは一見すると意外に思えるかもしれません。しかし、「AIの能力をよく知っているからこそ、その可能性と脅威をリアルに感じている」ということの表れなのだと思います。

---------------

このニュースを見て、私は世代間のギャップについても考えました。

保育の現場にいた時も、同世代の同僚とは価値観が合っても、他の世代の人とは話が合いにくい、と感じることがよくありました。

フリーランスになって一番良かったと感じるのは、「一緒に働く人を選べる」という感覚を持てたことです。今は、同じ価値観を持つ人たちとコミュニティで繋がり、共に学べる働き方にとても満足しています。

ただ、今後のことを考えると、価値観の合う人とだけではなく、様々な立場の人たちと協力していく必要もありますよね。

---------------

AIに限らず、どんなことでも「食わず嫌い」はもったいないな、と思います。まずは何でも試してみて、「自分には合うか」「今のタイミングで使えるか」を判断する。

新しいものに触れ、知ることで、働き方や生き方の選択肢は確実に増えていくと思うんですよね。

これからは、AIを単なる業務効率化のツールとしてだけでなく、時には世代間のギャップを埋めるコミュニケーションツールとして活用していく。そんな視点も必要かもしれませんね。"""
        }

    def get_transcript_from_input(self) -> str:
        """文字起こしテキストを直接入力で取得"""
        print("📝 文字起こしテキストを貼り付けてください")
        print("   (貼り付け後、空行でEnterを2回押すと処理開始)")
        print("   (キャンセルするには 'q' を入力)")
        print("-" * 50)
        
        lines = []
        empty_line_count = 0
        
        while True:
            try:
                line = input()
                
                if line.strip().lower() == 'q':
                    return None
                
                if line.strip() == '':
                    empty_line_count += 1
                    if empty_line_count >= 2:  # 空行が2回連続で入力終了
                        break
                else:
                    empty_line_count = 0
                
                lines.append(line)
                
            except KeyboardInterrupt:
                print("\n❌ キャンセルされました")
                return None
            except EOFError:
                break
        
        transcript = '\n'.join(lines).strip()
        
        if not transcript:
            print("❌ 文字起こしテキストが入力されませんでした")
            return None
        
        print(f"\n📖 文字起こし取得完了: {len(transcript)}文字")
        return transcript

    def clean_transcript(self, transcript: str) -> str:
        """文字起こしテキストの大幅修正"""
        text = transcript.strip()
        
        # より包括的な修正パターン
        corrections = {
            'まなみ': 'マナミ', 'マナみ': 'マナミ', '学み': 'マナミ',
            'さあにの子だま': '3人の子ども', 'サニーの子ども': '3人の子ども', 'さらにの子ども': '3人の子ども',
            'SNSはしん': 'SNS発信', 'SNS発信や': 'SNS発信',
            'コンテンツペーサコ': 'コンテンツ作成', 'コンテンチューサコーチュー': 'コンテンツ作成',
            'ままプリ': 'ママフリーランス', 'ままプール': 'ママフリーランス', 'ままフリーラス': 'ママフリーランス',
            'フォアン': '不安', 'フベンサ': '不便さ',
            '限代構': '家事代行', '価値大根': '家事代行', '始大公': '家事代行', '家自大公': '家事代行',
            'ファミサポ': 'ファミリーサポート',
            'エンポオニャ': '遠方', 'あさなこいや': '遠方',
            'ホイクエント': '保育園', 'そうげえ': '送迎',
            '自自弾家': '時短家電', '自単家電': '時短家電',
            'PDCAで回して': 'PDCAサイクルで改善して',
            'マコージ': '町田市', 'へねブッタオレル': '発熱',
            'インフレンジャー': 'インフルエンザ',
            '仕末': '週末', 'どにち': '土日',
            'リキール': '解決', 'デベスト': 'ベスト',
            'スイッチボート': 'スイッチボット', '水一ボート': 'スイッチボット'
        }
        
        for old, new in corrections.items():
            text = text.replace(old, new)
        
        # フィラー語と不要な表現を除去
        fillers = [
            r'はいこんにちは[^\。]*?です',
            r'えー+、?', r'あの+、?', r'えっと+、?', r'うーん+、?', r'まぁ+、?',
            r'なんか+、?', r'ちょっと+、?', r'でも+、?', r'そう+、?',
            r'っていう+ふう+に', r'みたいな+感じ', r'って+いう+の+は',
            r'だと+思う+ん+です+けど', r'なん+です+よ+ね',
            r'って+いう+こと+で', r'そう+いう+こと+で',
            r'で+で+で+', r'と+と+と+', r'ん+ん+ん+',
            r'って+って+', r'だ+だ+だ+', r'う+う+う+'
        ]
        
        for filler in fillers:
            text = re.sub(filler, ' ', text)
        
        # 句読点を正規化
        text = re.sub(r'[、,]+', '、', text)
        text = re.sub(r'[。\.]+', '。', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def extract_key_themes(self, clean_text: str) -> dict:
        """音声から主要テーマを抽出"""
        
        # キーワード分析（実際のnote記事のテーマに基づく）
        themes = {
            'work': ['仕事', 'フリーランス', 'クライアント', '働き方', '在宅', 'コミュニケーション', 'PR案件', 'メール', 'やり取り', 'サービス', 'メンバーシップ', '価格', '単価'],
            'technology': ['AI', '生成AI', 'ChatGPT', 'ツール', 'システム', 'アプリ', 'デジタル', 'オンライン', 'リモート'],
            'lifestyle': ['生活', '日常', '工夫', '改善', '時間', '家族', '子ども', '夫', '育児', '家事', '保育園', '送迎', '熱', '体調', '保育'],
            'childcare': ['子育て', '保育園', 'ファミリーサポート', '子ども', '育児', '3人', '0歳', '送迎', '自宅保育', 'ワンオペ'],
            'money': ['お金', '価格', '単価', '料金', '費用', '売上', '収入', '家計', '値段', 'コスト'],
            'communication': ['コミュニケーション', '伝える', '相談', '話し合い', 'やり取り', 'メール', '連絡', '会話', '説明']
        }
        
        detected_themes = {}
        for theme, keywords in themes.items():
            count = sum(1 for keyword in keywords if keyword in clean_text)
            if count > 0:
                detected_themes[theme] = count
        
        # 最も多く言及されたテーマを特定
        main_theme = max(detected_themes.items(), key=lambda x: x[1])[0] if detected_themes else 'lifestyle'
        
        return {'main_theme': main_theme, 'all_themes': detected_themes}

    def extract_meaningful_sentences(self, clean_text: str) -> list:
        """意味のある文を抽出"""
        
        # 文を分割
        sentences = re.split(r'[。！？]', clean_text)
        meaningful = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # 最小文字数と内容チェック
            if len(sentence) < 15:
                continue
                
            # 意味のない文をスキップ
            skip_patterns = [
                r'^[はい、そう、でも、まあ]+$',
                r'^[あのえーっと\s]+$',
                r'ありがとうございました$'
            ]
            
            if any(re.search(pattern, sentence) for pattern in skip_patterns):
                continue
            
            # 文として成立しているかチェック
            if any(word in sentence for word in ['です', 'ます', 'した', 'ある', 'いる', 'なる']):
                meaningful.append(sentence + '。')
        
        return meaningful[:12]  # 最大12文

    def analyze_writing_style(self, sample_text: str) -> dict:
        """文体パターンを分析"""
        style_patterns = {
            'intro_pattern': r'マナミです。\n\n今回は(.+?)について',
            'section_separator': r'---------------',
            'conclusion_pattern': r'皆さん(も|にも)(.+?)と思います。',
            'personal_touch': ['3人の子ども', 'ママフリーランス', '私は', '我が家'],
            'polite_ending': ['と思います', 'でしょうか', 'ではないかと']
        }
        
        return style_patterns

    def create_article_sections(self, sentences: list, theme: str) -> list:
        """テーマに応じたセクション作成"""
        
        if not sentences:
            return self.create_fallback_sections(theme)
        
        sections = []
        
        # テーマ別のセクション構成
        if theme == 'products':
            sections = self.create_product_review_sections(sentences)
        elif theme == 'housework':
            sections = self.create_housework_sections(sentences)
        elif theme == 'work':
            sections = self.create_work_sections(sentences)
        elif theme == 'childcare':
            sections = self.create_childcare_sections(sentences)
        else:
            sections = self.create_general_sections(sentences)
        
        return sections

    def create_product_review_sections(self, sentences: list) -> list:
        """商品レビューのセクション"""
        sections = []
        
        section1 = f"""{' '.join(sentences[:4])}

商品レビューを作成する際は、実際の体験と感じたことを正直にお伝えすることを心がけています。使ってみて良かった点だけでなく、気になった点があれば合わせてご紹介するようにしています。"""
        
        section2 = f"""{' '.join(sentences[4:8]) if len(sentences) > 4 else '実際に使用してみた感想や、日常生活での活用方法についてお話しします。'}

商品を使う前と後での変化や、家族の反応なども含めて、リアルな使用感をお伝えできればと思います。同じような商品を検討している方の参考になれば嬉しいです。"""
        
        section3 = f"""{' '.join(sentences[8:]) if len(sentences) > 8 else '今後もこうした商品レビューを通して、皆さんの日常生活に役立つ情報をお届けしたいと思います。'}

商品選びの参考になるような情報提供を心がけながら、今後も様々な商品を試していきたいと思います。"""
        
        return [section1, section2, section3]

    def create_housework_sections(self, sentences: list) -> list:
        """家事テーマのセクション"""
        sections = []
        
        section1 = f"""{' '.join(sentences[:4])}

3人の子どもがいる我が家では、毎日の家事が大変な作業の一つです。効率化や外部サービスの利用など、様々な選択肢がある中で、自分なりの方法を模索しています。"""
        
        section2 = f"""{' '.join(sentences[4:8]) if len(sentences) > 4 else '日々試行錯誤しながら、家族にとって最適な方法を見つけようとしています。'}

家事は単なる作業ではなく、家族の生活の質に直結する重要な要素だと考えています。そのため、効率だけでなく、家族みんなが快適に過ごせることを重視しています。"""
        
        section3 = f"""{' '.join(sentences[8:]) if len(sentences) > 8 else '今後も家族の成長や変化に合わせて、柔軟に家事のやり方を調整していきたいと思います。'}

完璧を求めすぎず、家族みんなが協力しながら、無理のない範囲で家事を分担していくことが大切だと感じています。"""
        
        return [section1, section2, section3]

    def create_work_sections(self, sentences: list) -> list:
        """仕事テーマのセクション"""
        sections = []
        
        section1 = f"""{' '.join(sentences[:4])}

ママフリーランスとして働く中で、子育てと仕事のバランスを取ることは日々の大きな課題です。柔軟な働き方ができる反面、時間管理や集中できる環境作りが重要になってきます。"""
        
        section2 = f"""{' '.join(sentences[4:8]) if len(sentences) > 4 else '在宅ワークのメリットを活かしながら、効率的に仕事を進める方法を模索しています。'}

クライアントワークでは、事前のコミュニケーションを大切にして、お互いの期待値を明確にすることを心がけています。"""
        
        section3 = f"""{' '.join(sentences[8:]) if len(sentences) > 8 else '家族の状況に合わせて働き方を調整しながら、長期的なキャリア形成も視野に入れています。'}

フリーランスという働き方を通じて、多くの経験を積みながら成長していきたいと思います。"""
        
        return [section1, section2, section3]

    def create_childcare_sections(self, sentences: list) -> list:
        """子育てテーマのセクション"""
        sections = []
        
        section1 = f"""{' '.join(sentences[:4])}

3人の子どもを育てる中で、毎日が試行錯誤の連続です。子どもの成長に合わせて対応を変えていく必要があり、その都度新しい発見があります。"""
        
        section2 = f"""{' '.join(sentences[4:8]) if len(sentences) > 4 else '子どもたちとの時間を大切にしながら、それぞれの個性に合わせた関わり方を心がけています。'}

子育てに正解はないと思いますが、子どもたちと一緒に成長していく過程を楽しみながら過ごしています。"""
        
        section3 = f"""{' '.join(sentences[8:]) if len(sentences) > 8 else '子どもたちの成長に合わせて、親としても成長していきたいと思います。'}

子どもたちが自分らしく育っていけるよう、サポートしながら見守っていきたいと思います。"""
        
        return [section1, section2, section3]

    def create_general_sections(self, sentences: list) -> list:
        """一般的なセクション"""
        sections = []
        
        third = len(sentences) // 3
        
        section1 = f"""{' '.join(sentences[:third]) if sentences else '日常生活の中で気づいたことや感じたことを皆さんと共有したいと思います。'}

毎日の生活の中には、小さな発見や学びがたくさんあります。そうした気づきを大切にしながら過ごしています。"""
        
        section2 = f"""{' '.join(sentences[third:2*third]) if len(sentences) > third else '様々な場面で学んだことや感じたことがあります。'}

実際に経験してみることで初めて分かることも多く、挑戦することの大切さを実感しています。"""
        
        section3 = f"""{' '.join(sentences[2*third:]) if len(sentences) > 2*third else '今後も新しい挑戦を続けながら成長していきたいと思います。'}

これからも皆さんと一緒に学び合いながら、より良い日々を過ごしていきたいと思います。"""
        
        return [section1, section2, section3]

    def create_fallback_sections(self, theme: str) -> list:
        """フォールバック用セクション"""
        return [
            "最近の生活の中で感じていることについてお話ししたいと思います。日々の暮らしの中には多くの学びがあり、それらを皆さんと共有できればと思います。",
            "具体的な体験を通して学んだことがたくさんあります。小さなことでも、実際にやってみることで新しい発見があることが多いです。",
            "今後もこうした日々の気づきを大切にしながら、皆さんと共有していきたいと思います。一緒に学び合いながら成長していければと思います。"
        ]

    def generate_article(self, transcript: str) -> str:
        """記事生成メイン"""
        print("🔧 文字起こしをクリーニング中...")
        
        # 文字起こしクリーニング
        clean_text = self.clean_transcript(transcript)
        
        # テーマ分析
        theme_data = self.extract_key_themes(clean_text)
        main_theme = theme_data['main_theme']
        
        print(f"📝 検出されたテーマ: {main_theme}")
        
        # 意味のある文を抽出
        meaningful_sentences = self.extract_meaningful_sentences(clean_text)
        print(f"📄 抽出された文: {len(meaningful_sentences)}個")
        
        # セクション作成
        sections = self.create_article_sections(meaningful_sentences, main_theme)
        
        # テーマに応じたタイトルと導入
        theme_titles = {
            'work': '働き方について考えていること',
            'technology': 'AIやテクノロジーについて思うこと', 
            'childcare': '子育てについて感じること',
            'lifestyle': '最近の生活について',
            'money': 'お金について考えていること',
            'communication': 'コミュニケーションについて思うこと'
        }
        
        title = theme_titles.get(main_theme, '最近考えていること')
        
        # 記事構成
        intro = f"""マナミです。

今回は{title}についてお話ししたいと思います。

3人の子どもを育てながらママフリーランスとして働いている中で、日々様々なことを考えたり体験したりしています。今回は、その中でも特に皆さんと共有したいと思った内容についてお話しします。

同じような立場の方や、似たような状況にある方の参考になれば嬉しいです。"""
        
        conclusion = f"""今回お話しした内容は、私自身の経験や考えに基づくものですが、皆さんの日常生活にも何かしらのヒントになればと思います。

子育てと仕事を両立しながらの日々は決して楽ではありませんが、その中にも多くの学びや気づきがあります。今後もこうした経験を皆さんと共有しながら、一緒に成長していければと思います。

皆さんもぜひ、日常の小さな気づきや工夫を大切にしてみてください。そうした積み重ねが、より良い生活につながっていくのではないかと思います。"""
        
        # 記事組み立て
        article = f"{intro}\n\n---------------\n\n{sections[0]}\n\n---------------\n\n{sections[1]}\n\n---------------\n\n{sections[2]}\n\n---------------\n\n{conclusion}"
        
        return article

    def copy_to_clipboard(self, text: str):
        """クリップボードにコピー"""
        try:
            pyperclip.copy(text)
            print("📋 記事をクリップボードにコピーしました！")
        except Exception as e:
            print(f"⚠️ クリップボードコピー失敗: {e}")

    def save_article(self, article: str, transcript_path: str) -> str:
        """記事を保存（ファイル指定時）"""
        # 保存ファイル名を生成
        transcript_name = Path(transcript_path).stem.replace('transcript_', '')
        article_filename = f"article_{transcript_name}.md"
        article_path = Path("/Users/manami/audio_to_article_new") / article_filename
        
        try:
            with open(article_path, 'w', encoding='utf-8') as f:
                f.write(article)
            
            print(f"💾 記事保存完了: {article_filename}")
            return str(article_path)
            
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            return None

    def save_article_with_timestamp(self, article: str) -> str:
        """記事を保存（タイムスタンプ付き）"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        article_filename = f"article_{timestamp}.md"
        article_path = Path("/Users/manami/audio_to_article_new") / article_filename
        
        try:
            with open(article_path, 'w', encoding='utf-8') as f:
                f.write(article)
            
            print(f"💾 記事保存完了: {article_filename}")
            return str(article_path)
            
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            return None

    def process_transcript_input(self):
        """貼り付けられた文字起こしテキストを処理して記事を生成"""
        
        # 文字起こしテキストを取得
        transcript = self.get_transcript_from_input()
        if not transcript:
            return None
        
        # 記事生成
        print("🤖 記事生成中...")
        article = self.generate_article(transcript)
        
        # 結果表示
        print("\n" + "=" * 80)
        print("📰 生成された記事:")
        print("=" * 80)
        print(article)
        print("=" * 80)
        
        # クリップボードにコピー
        self.copy_to_clipboard(article)
        
        # 記事保存（タイムスタンプ付き）
        saved_path = self.save_article_with_timestamp(article)
        
        print(f"\n✅ 処理完了")
        if saved_path:
            print(f"💾 保存場所: {saved_path}")
        
        return article

    def process_transcript_file(self, transcript_path: str):
        """文字起こしファイルを処理して記事を生成（ファイル指定時）"""
        print(f"🔍 処理開始: {Path(transcript_path).name}")
        
        # 文字起こし読み込み
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = f.read().strip()
            print(f"📖 文字起こし読み込み完了: {len(transcript)}文字")
        except Exception as e:
            print(f"❌ ファイル読み込みエラー: {e}")
            return None
        
        # 記事生成
        print("🤖 記事生成中...")
        article = self.generate_article(transcript)
        
        # 結果表示
        print("\n" + "=" * 80)
        print("📰 生成された記事:")
        print("=" * 80)
        print(article)
        print("=" * 80)
        
        # クリップボードにコピー
        self.copy_to_clipboard(article)
        
        # 記事保存
        saved_path = self.save_article(article, transcript_path)
        
        print(f"\n✅ 処理完了")
        if saved_path:
            print(f"💾 保存場所: {saved_path}")
        
        return article

def main():
    parser = argparse.ArgumentParser(description='記事生成専用ツール')
    parser.add_argument('transcript_file', nargs='?', help='文字起こしファイルのパス')
    parser.add_argument('--stdin', action='store_true', help='標準入力から文字起こしテキストを読み込み')
    
    args = parser.parse_args()
    
    generator = ArticleGenerator()
    
    # 標準入力から読み込み（リダイレクト対応）
    if not sys.stdin.isatty() or args.stdin:
        print("📝 標準入力から文字起こしテキストを読み込み中...")
        try:
            transcript = sys.stdin.read().strip()
            if transcript:
                print(f"📖 文字起こし取得完了: {len(transcript)}文字")
                print("🤖 記事生成中...")
                article = generator.generate_article(transcript)
                
                # 結果表示
                print("\n" + "=" * 80)
                print("📰 生成された記事:")
                print("=" * 80)
                print(article)
                print("=" * 80)
                
                # クリップボードにコピー
                generator.copy_to_clipboard(article)
                
                # 記事保存
                saved_path = generator.save_article_with_timestamp(article)
                
                print(f"\n✅ 処理完了")
                if saved_path:
                    print(f"💾 保存場所: {saved_path}")
                return
            else:
                print("❌ 標準入力からデータが読み込めませんでした")
                return
        except Exception as e:
            print(f"❌ 標準入力読み込みエラー: {e}")
            return
    
    print("📝" + "=" * 50)
    print("   記事生成専用ツール")
    print("   Step 2: 文字起こし → 記事")
    print("=" * 52)
    print()
    
    # コマンドライン引数で文字起こしファイルが指定されている場合
    if args.transcript_file:
        transcript_path = args.transcript_file.strip().strip('"').strip("'")
        transcript_path = os.path.expanduser(transcript_path)
        
        if os.path.exists(transcript_path):
            generator.process_transcript_file(transcript_path)
        else:
            print(f"❌ ファイルが見つかりません: {transcript_path}")
        return
    
    # インタラクティブモード（文字起こしテキスト貼り付け）
    while True:
        print("🎯 以下から選択してください:")
        print("   1. 文字起こしテキストを貼り付けて記事生成")
        print("   2. 文字起こしファイルを指定して記事生成")
        print("   q. 終了")
        
        choice = input("選択 (1/2/q): ").strip()
        
        if choice.lower() in ['q', 'quit', 'exit']:
            break
        elif choice == '1':
            # 文字起こしテキスト貼り付けモード
            generator.process_transcript_input()
        elif choice == '2':
            # ファイル指定モード
            file_input = input("📄 ファイルパス: ").strip()
            
            if not file_input:
                continue
            
            # パスの整理
            transcript_path = file_input.strip()
            if transcript_path.startswith('"') and transcript_path.endswith('"'):
                transcript_path = transcript_path[1:-1]
            elif transcript_path.startswith("'") and transcript_path.endswith("'"):
                transcript_path = transcript_path[1:-1]
            
            transcript_path = transcript_path.replace('\\ ', ' ')
            transcript_path = os.path.expanduser(transcript_path)
            
            if os.path.exists(transcript_path):
                generator.process_transcript_file(transcript_path)
            else:
                print("❌ ファイルが見つかりません")
                continue
        else:
            print("❌ 無効な選択です")
            continue
        
        # 次の処理を確認
        print("\n" + "=" * 50)
        next_action = input("🔄 続けて処理しますか？ (y/N): ").lower().strip()
        if next_action not in ['y', 'yes']:
            break
    
    print("👋 お疲れさまでした！")

if __name__ == "__main__":
    main()