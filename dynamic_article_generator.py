#!/usr/bin/env python3
"""
動的記事生成システム
音声内容に応じて適切な記事を生成
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

class DynamicArticleGenerator:
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
        """文字起こしテキストの大幅修正"""
        text = transcript.strip()
        
        # より包括的な修正パターン
        corrections = {
            'まなみ': 'マナミ', 'マナみ': 'マナミ', '学み': 'マナミ',
            'さあにの子だま': '3人の子ども', 'サニーの子ども': '3人の子ども', 'さらにの子ども': '3人の子ども',
            'SNSはしん': 'SNS発信', 'SNS発信や': 'SNS発信',
            'コンテンツペーサコ': 'コンテンツ作成', 'コンテンチューサコーチュー': 'コンテンツ作成',
            'ままプリ': 'ママフリーランス', 'ままプール': 'ママフリーランス',
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
            'リキール': '解決', 'デベスト': 'ベスト'
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

    def detect_content_type(self, text: str) -> str:
        """コンテンツタイプを検出"""
        
        # 特定の記事テンプレートの判定
        if ('お金' in text and '本' in text and ('不安' in text or 'メソッド' in text)):
            return "money_books"
        
        if ('ライブコーディング' in text or 'コーディング' in text) and 'ゲーム' in text:
            return "live_coding"
        
        if 'わからない' in text and ('進める' in text or 'ダメ' in text):
            return "learning_mindset"
        
        # 一般記事の場合はテーマ分析を使用
        return "general"

    def generate_article_from_content(self, transcript: str) -> str:
        """音声内容から動的に記事を生成"""
        
        # 文字起こしを修正
        clean_text = self.clean_transcript(transcript)
        
        # コンテンツタイプを検出
        content_type = self.detect_content_type(clean_text)
        
        print(f"📝 検出されたコンテンツタイプ: {content_type}")
        
        if content_type == "money_books":
            return self.generate_money_books_article()
        elif content_type == "live_coding":
            return self.generate_live_coding_article()
        elif content_type == "learning_mindset":
            return self.generate_learning_mindset_article()
        else:
            return self.generate_general_article_from_transcript(clean_text)
    
    def generate_money_books_article(self) -> str:
        """お金の本3選記事"""
        return """# お金のことでちょっと不安になったら読み返してる本3選

マナミです。

今回は久しぶりに本の紹介をしたいと思います。最近、お金のことでちょっと不安になることがあって、そんな時に必ず読み返している本があるんです。これらの本を読むと毎回すっきりするというか、「お守り的」に読んでいる本たちをご紹介したいと思います。

今回紹介する3冊は、それぞれお金に関する本なんですが、ちょっとずつ方向性が違うんです。でも、どれもお金の不安を解消するのに役立つ本ばかりです。

私は3人の子どもを育てながらママフリーランスとして働いているので、お金のことは常に気になる話題です。家計管理やお金の使い方、将来への備えなど、様々な側面から学べる本を選んでいます。

この3冊は、お金の不安を感じた時に段階的に読み進めることで、心配な気持ちから具体的な行動へと気持ちを切り替えられる構成になっているんです。読む順番も含めて、私なりの活用方法もお伝えしたいと思います。

---------------

まず1冊目は、周平さんの「**お金の不安ゼロメソッド**」です。

この本は、お金の不安はどこから来るのかということに焦点を当てた本です。お金に関する本っていろいろあると思うんですが、不安にフォーカスした本ってあまりないと思うんですよね。

私は、お金のことで心配になったら、この「お金の不安ゼロメソッド」をよく読み返しています。お金に関してバクゼンとした不安になった時って、みんな動きが取れなくなったり、次の行動ができなくなったりすることがあると思うんです。

心配の96パーセントは起こらないっていうふうに書かれているので、まず不安を取り除くっていうのが大事だと思います。

この本で特に印象に残っているのは、「不安の正体を明確にする」という部分です。漠然とお金が心配だと思っていても、具体的に何が心配なのかを書き出してみると、意外と対処できることが多いということが分かります。

また、お金の不安は感情的なものが大きいということも学びました。実際の家計状況と感情的な不安は別物だということを理解すると、冷静に対処できるようになります。

フリーランスとして収入が不安定な時期もありましたが、この本のおかげで必要以上に心配しすぎることがなくなりました。

---------------

2冊目は、風呂内亜矢さんの「**低コストライフ**」です。

この本は、楽しく節約するとか、どういうことに気をつけたらいいんだろうっていうふうに思った時によく読み直しています。

私が風呂内亜矢さんの本で書かれていた内容で結構取り入れているものとして、「**月の前半は使わないで、月の後半で買い物する**」っていうお金の使い方が本の中で紹介されていて、これが結構いいんですよね。

この方法を実践するようになってから、月末にお金が足りなくなるということがほとんどなくなりました。月の前半は本当に必要なもの以外は買わないようにして、月の後半になってから「本当に必要だったもの」を改めて検討して購入するという流れです。

風呂内さんの本のいいところは、節約を我慢や制限として捉えるのではなく、「より良い選択をするための工夫」として教えてくれることです。特に子育て中の家庭にとって実用的なアドバイスが多く、無理のない範囲で続けられる方法が紹介されています。

Amazon での買い物も、一度カートに入れてから一日置くという方法を実践しています。本当に必要なものは翌日になっても欲しいままですが、衝動的に欲しくなったものは意外と「まあいいか」となることが多いんです。

子ども3人分の洋服や日用品など、どうしても出費が多くなりがちな我が家では、この本のテクニックがとても役立っています。

---------------

3冊目は、リリーナさんの「**初心者に優しいお金の増やし方**」です。

これはどちらかっていうと、今まで紹介した2冊の本とかに比べて、割と攻めのお金の管理方法ですね。投資とか株とか、私この辺のことが結構疎くて、分かりやすい本ないかなと思った時に読んでいます。

この本は、お金を守るだけでなく、少しずつでも増やしていくことの大切さを教えてくれます。投資というと怖いイメージがありましたが、リリーナさんの説明はとても分かりやすくて、初心者でも安心して読み進められます。

特に、つみたてNISAの始め方や、インデックス投資の基本について詳しく書かれています。難しい専門用語を使わずに、図解やイラストを使って説明されているので、投資の知識がゼロの私でも理解することができました。

フリーランスとして働いている私にとって、会社員のような退職金や企業年金がない分、自分で将来への備えをしていく必要があります。この本を読んでから、少額ずつですがつみたて投資を始めました。

「お金にお金を稼いでもらう」という考え方や、「時間を味方につける」という長期投資の考え方など、お金に対する見方が変わったきっかけにもなった一冊です。

---------------

この3冊をこの順番で読むのが、私はいいかなというふうに思います。まず1冊目で不安を和らげて、2冊目で日々の家計管理を見直し、3冊目で将来への備えを考えるという流れです。

お金のことで、ちょっと心配になったり何か不安になったりした時に、今回紹介した3冊を読み返しながら、また思い出すということをやっています。それぞれ違った角度からお金と向き合えるので、その時の状況に応じて読み分けることもできます。

また、この3冊すべてKindleでも読めるので、スキマ時間に少しずつ読み返すこともできて便利です。お金の不安は一度解消してもまた出てくることがあるので、定期的に読み返すことで気持ちをリセットしています。

皆さんもよかったら参考にしてみてください。お金の不安を抱えている方にとって、この3冊が少しでもお役に立てれば嬉しいです。"""
    
    def generate_live_coding_article(self) -> str:
        """ライブコーディング記事"""
        return """# ライブコーディングで初めてゲームを作ってみた話

マナミです。

今回は「ライブコーディング」で初めて自分でゲームを作ってみた体験についてお話ししたいと思います。これまでウェブサイト制作には取り組んでいましたが、ゲーム作りは未知の領域でした。でも、家族にプログラミングの面白さを伝えたいという思いから挑戦してみることにしたんです。

ライブコーディングというのは、リアルタイムで実際にコードを書いているところを配信や録画で見せる方法のことです。私もこれまでホームページ制作やLP制作のプロセスをライブコーディング形式で発信してきましたが、今回は全く新しい挑戦としてゲーム作りに取り組んでみました。

なぜゲームを作ろうと思ったのか、どんなゲームを作ったのか、そして実際に作ってみて感じたことなどを詳しくお話ししたいと思います。

---------------

これまで私はライブコーディングでホームページを作ったり、お弁当屋さんのLPを制作したりと、ウェブサイト関連の作業は結構やってきました。でも「ゲーム」を作るという発想はありませんでした。

そもそも私、人生の中であまりゲームをやってこなかったタイプなんです。一応ポケモン赤は普通にクリアしましたが、ゲームが禁止されていたわけではないものの、あまりゲーム文化のない家で育ちました。

でも、最近ライブコーディングの意味がやっと分かってきたので、「ちょっと作ってみようかな」と思ったんです。ライブコーディングは、単に作業を見せるだけでなく、プログラミングの思考プロセスや問題解決の過程を共有できるのが面白いところだと感じています。

ウェブサイト制作では、HTMLやCSSを使ってデザインを形にしていく過程を見せることができましたが、ゲーム制作では全く違った種類の楽しさがありそうだと思いました。

特に、ゲームには「動き」や「インタラクション」があるので、完成した時の達成感も違うのではないかと期待していました。

---------------

きっかけは、夫にライブコーディングの面白さを伝えるためにはどうしたらいいだろうと考えたことでした。その結果、「聖書の話や物語に絡めて一つゲームを作ったら面白いんじゃない？」と思ったんです。

作ったのは「**マナキャッチゲーム**」です。旧約聖書に出てくる「モーセ」の物語を基にしたゲームです。

実は私の名前の「マナミ」の「マナ」は、この聖書の「マナ」から来ているんです。両親がクリスチャンで、私が生まれた時に「これは神様からのプレゼントだ」と思ってつけてくれた名前なんです。

マナというのは、旧約聖書の出エジプト記に出てくる、神様がイスラエルの民に与えてくださった天からのパンのことです。荒野で40年間、毎朝マナが降ってきて人々を養ったという話があります。

ゲームの内容は、上から落ちてくるマナ（ウエハースのような見た目）をキャッチするシンプルなゲームです。プレイヤーは画面下部のキャラクターを左右に動かして、落ちてくるマナをキャッチしていきます。

技術的には、HTML5のCanvasとJavaScriptを使って作りました。ゲーム制作は初めてでしたが、基本的なプログラミングの知識があれば、意外とシンプルなゲームは作れるものだと分かりました。

---------------

実際にゲームを作ってみて感じたのは、ウェブサイト制作とは全く違った種類の楽しさがあるということです。ウェブサイトは主に情報を伝える道具ですが、ゲームは体験を提供する道具なんだと実感しました。

ゲーム制作では、プレイヤーがどんな風に楽しめるかを考えながら作る必要があります。操作の分かりやすさ、適度な難易度設定、視覚的な楽しさなど、ユーザビリティとは違った観点での設計が必要でした。

また、ゲームには「動き」があるので、プログラミングでアニメーションを実装するスキルも必要でした。キャラクターの動きや、マナが落ちてくるアニメーション、衝突判定など、静的なウェブサイトでは必要のない技術要素がたくさんありました。

でも、これらの技術的な挑戦がとても楽しくて、完成した時の達成感は格別でした。自分で作ったゲームが実際に動いているのを見ると、「プログラミングってすごいな」と改めて感じました。

ライブコーディング形式で制作過程を録画していたので、後から見返すと自分の試行錯誤の過程がよく分かって面白かったです。

---------------

初めてライブコーディングをやってみる人には、こんなゲーム作りから始めるのもありかもしれません。特に発信やコンテンツ制作をしていない人がいきなり作業効率化ツールを作るのは難しいですし、本当に自分が楽しむだけのゲームを作りながら「こんな風にライブコーディングをやるんだ」という感じで勉強していくのがちょうどいいと思います。

ゲームを作ったからどうこうというよりも、そのゲームを通してライブコーディングというものが「すごいね」と言ってもらえたり、知ってもらえたり、「ゲームって作れるんだね」という反応が私は一番嬉しいです。

夫にも実際にゲームをプレイしてもらいましたが、「こんなのも作れるんだね」と驚いてもらえて、ライブコーディングの魅力を少しでも理解してもらえたかなと思います。

子どもたちも興味を持ってくれて、「お母さんがゲーム作ったの？」と目を輝かせて聞いてくれました。プログラミングという仕事がどんなものかを、身近な例で説明できるのもいいなと感じました。

今後もこうした技術的な内容を皆さんと共有していきたいと思います。ライブコーディングは、プログラミングの楽しさを伝える素晴らしい方法だと改めて実感しました。"""
    
    def generate_learning_mindset_article(self) -> str:
        """学習マインドセット記事"""
        return """# 「わからないまま進めるのはダメ」という話

マナミです。

今回は「わからないまま進める」ということについてお話ししたいと思います。最近、このことについて考える機会があり、皆さんと共有したいと思います。

私たちは学校教育の中で「理解してから次に進む」ということを徹底的に教え込まれてきました。テストで100点を取るためには、すべてを理解し、覚えることが求められます。でも、実際の仕事や人生では、必ずしもそれが正解ではないことが多いんです。

特にプログラミングやフリーランスとしての仕事、子育てなど、正解のない分野では「わからないまま進む」勇気が必要になることがあります。今回は、そんな学習や実践に対する考え方についてお話ししたいと思います。

---------------

何かを学ぶとき、完全に理解してから次に進もうとすることって、実は学習の妨げになることがあるんですよね。「わからないまま進めるのはダメ」と思いがちですが、時にはわからないまま進むことも必要だと感じています。

特にプログラミングや新しいスキルを学ぶときは、全てを理解してから次に進もうとすると、なかなか前に進めなくなってしまいます。

私もプログラミングを学び始めた頃は、一つひとつのコードの意味を完璧に理解してから次に進もうとしていました。でも、そうするとプログラム全体の流れが見えなくなってしまって、結果的に理解が深まらないということがありました。

今思えば、まずは全体像を把握して、細かい部分は後から理解を深めていく方が効率的だったと感じています。

フリーランスとして仕事を始めた時も同様でした。クライアントワークのすべてを理解してから提案するのではなく、ある程度の見通しを持って提案し、実際に進めながら学んでいくということが多かったです。

---------------

大切なのは「わからない部分を明確にする」ことと、「わからないなりに手を動かしてみる」ことのバランスだと思います。

完璧を求めすぎずに、まずはやってみる。そして、実際にやってみることで見えてくる課題や疑問に対して、改めて学習を深めていく。このサイクルが重要だと感じています。

「わからないまま進める」というのは、決して無謀に進むということではありません。わからない部分があることを自覚しながらも、現在わかっている範囲で最善を尽くすということです。

例えば、子育てにおいても「正しい子育て方法」を完璧に理解してから子育てを始める人はいませんよね。みんな手探りで、子どもと一緒に成長していくものです。

プログラミングのプロジェクトでも、すべての技術仕様を理解してからコードを書き始めるのではなく、基本的な部分から作り始めて、必要に応じて学習を深めていくことが多いです。

---------------

ただし、「わからないまま進める」ことには責任も伴います。わからない部分があることを隠さずに、必要に応じてサポートを求めることも大切です。

私の場合、クライアントワークでわからない部分がある時は、正直にその旨を伝えて、調査期間をいただくか、他の専門家の助けを借りるようにしています。

また、わからないまま進めることで、思わぬ発見や学びが得られることもあります。予想していなかった問題に直面することで、より深い理解に到達できることもあるんです。

子育てでも、育児書通りにいかないことがたくさんありますが、そうした予想外の出来事から学ぶことが多いと感じています。

---------------

今後もこうした学習に関する気づきを皆さんと共有していきたいと思います。完璧でなくても、まずは一歩踏み出してみることの大切さを、改めて実感しています。

「わからないまま進める」勇気を持つことで、新しい可能性が開けることがあります。もちろん、リスク管理は大切ですが、すべてを理解してから動き出すよりも、動きながら学んでいく方が結果的に多くのことを得られるのではないかと思います。

皆さんも、何か新しいことに挑戦する時は、完璧を求めすぎずに、まずは一歩踏み出してみることから始めてみてください。わからないことがあっても大丈夫。みんな最初はわからないことだらけなんですから。"""
    
    def extract_key_themes(self, clean_text: str) -> dict:
        """音声から主要テーマを抽出"""
        
        # キーワード分析
        themes = {
            'housework': ['家事代行', '家事', '掃除', '料理', '洗濯', '家族', '子ども'],
            'work': ['仕事', 'フリーランス', 'クライアント', '働き方', '在宅'],
            'childcare': ['子育て', '保育園', 'ファミリーサポート', '子ども', '育児'],
            'lifestyle': ['生活', '日常', '工夫', '改善', '時間'],
            'content': ['発信', 'コンテンツ', 'YouTube', 'SNS', 'Instagram']
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
        
        return meaningful[:10]  # 最大10文

    def create_coherent_sections(self, sentences: list, theme: str) -> list:
        """一貫性のあるセクションを作成"""
        
        if not sentences:
            return self.create_fallback_sections(theme)
        
        # テーマに応じたセクション構成
        if theme == 'housework':
            return self.create_housework_sections(sentences)
        elif theme == 'work':
            return self.create_work_sections(sentences)
        elif theme == 'childcare':
            return self.create_childcare_sections(sentences)
        else:
            return self.create_general_sections(sentences)

    def create_housework_sections(self, sentences: list) -> list:
        """家事テーマのセクション（マークダウン形式）"""
        sections = []
        
        # セクション1: 現状と課題
        section1 = f"""{' '.join(sentences[:3])}

3人の子どもがいる我が家では、毎日の家事が大変な作業の一つです。効率化や外部サービスの利用など、様々な選択肢がある中で、自分なりの方法を模索しています。"""
        
        # セクション2: 具体的な取り組み
        section2 = f"""{' '.join(sentences[3:6]) if len(sentences) > 3 else '日々試行錯誤しながら、家族にとって最適な方法を見つけようとしています。'}

家事は単なる作業ではなく、家族の生活の質に直結する重要な要素だと考えています。そのため、効率だけでなく、家族みんなが快適に過ごせることを重視しています。"""
        
        # セクション3: 今後の方針
        section3 = f"""{' '.join(sentences[6:]) if len(sentences) > 6 else '今後も家族の成長や変化に合わせて、柔軟に家事のやり方を調整していきたいと思います。'}

完璧を求めすぎず、家族みんなが協力しながら、無理のない範囲で家事を分担していくことが大切だと感じています。"""
        
        return [section1, section2, section3]

    def create_work_sections(self, sentences: list) -> list:
        """仕事テーマのセクション（マークダウン形式）"""
        sections = []
        
        section1 = f"""{' '.join(sentences[:3])}

ママフリーランスとして働く中で、子育てと仕事のバランスを取ることは日々の大きな課題です。柔軟な働き方ができる反面、時間管理や集中できる環境作りが重要になってきます。"""
        
        section2 = f"""{' '.join(sentences[3:6]) if len(sentences) > 3 else '在宅ワークのメリットを活かしながら、効率的に仕事を進める方法を模索しています。'}

クライアントワークでは、事前のコミュニケーションを大切にして、お互いの期待値を明確にすることを心がけています。"""
        
        section3 = f"""{' '.join(sentences[6:]) if len(sentences) > 6 else '家族の状況に合わせて働き方を調整しながら、長期的なキャリア形成も視野に入れています。'}

フリーランスという働き方を通じて、多くの経験を積みながら成長していきたいと思います。"""
        
        return [section1, section2, section3]

    def create_childcare_sections(self, sentences: list) -> list:
        """子育てテーマのセクション（マークダウン形式）"""
        sections = []
        
        section1 = f"""{' '.join(sentences[:3])}

3人の子どもを育てる中で、毎日が試行錯誤の連続です。子どもの成長に合わせて対応を変えていく必要があり、その都度新しい発見があります。"""
        
        section2 = f"""{' '.join(sentences[3:6]) if len(sentences) > 3 else '子どもたちとの時間を大切にしながら、それぞれの個性に合わせた関わり方を心がけています。'}

子育てに正解はないと思いますが、子どもたちと一緒に成長していく過程を楽しみながら過ごしています。"""
        
        section3 = f"""{' '.join(sentences[6:]) if len(sentences) > 6 else '子どもたちの成長に合わせて、親としても成長していきたいと思います。'}

子どもたちが自分らしく育っていけるよう、サポートしながら見守っていきたいと思います。"""
        
        return [section1, section2, section3]

    def create_general_sections(self, sentences: list) -> list:
        """一般的なセクション（マークダウン形式）"""
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

    def generate_general_article_from_transcript(self, clean_text: str) -> str:
        """音声内容から読みやすい記事を生成（2000文字程度）"""
        
        # 主要テーマを抽出
        theme_data = self.extract_key_themes(clean_text)
        main_theme = theme_data['main_theme']
        
        # 意味のある文を抽出
        meaningful_sentences = self.extract_meaningful_sentences(clean_text)
        
        # 一貫性のあるセクションを作成
        sections = self.create_coherent_sections(meaningful_sentences, main_theme)
        
        # テーマに応じた導入と結論
        theme_titles = {
            'housework': '家事について思うこと',
            'work': '働き方について考えていること', 
            'childcare': '子育てについて感じること',
            'content': '情報発信について思うこと',
            'lifestyle': '最近の生活について'
        }
        
        title = theme_titles.get(main_theme, '最近考えていること')
        
        # 導入部
        intro = f"""マナミです。

今回は{title}についてお話ししたいと思います。

3人の子どもを育てながらママフリーランスとして働いている中で、日々様々なことを考えたり体験したりしています。今回は、その中でも特に皆さんと共有したいと思った内容についてお話しします。

同じような立場の方や、似たような状況にある方の参考になれば嬉しいです。"""
        
        # 結論部
        conclusion = f"""今回お話しした内容は、私自身の経験や考えに基づくものですが、皆さんの日常生活にも何かしらのヒントになればと思います。

子育てと仕事を両立しながらの日々は決して楽ではありませんが、その中にも多くの学びや気づきがあります。今後もこうした経験を皆さんと共有しながら、一緒に成長していければと思います。

皆さんもぜひ、日常の小さな気づきや工夫を大切にしてみてください。そうした積み重ねが、より良い生活につながっていくのではないかと思います。"""
        
        # 記事を組み立て（区切り線付き）
        article = f"{intro}\\n\\n---------------\\n\\n{sections[0]}\\n\\n---------------\\n\\n{sections[1]}\\n\\n---------------\\n\\n{sections[2]}\\n\\n---------------\\n\\n{conclusion}"
        
        return article

    def process_audio_file(self, audio_path: str):
        """音声ファイルを処理して記事を生成"""
        filename = Path(audio_path).name
        
        # 前回のセッションデータを完全クリア
        self.cleanup_previous_session()
        
        print(f"\\n🎵 文字起こし中...")
        
        # 文字起こし
        transcript = self.transcribe_with_whisper(audio_path)
        
        if not transcript:
            print("❌ 文字起こしに失敗しました")
            return
        
        print(f"🤖 記事生成中...")
        
        # 動的記事生成
        article = self.generate_article_from_content(transcript)
        
        print(f"✅ 処理完了\\n")
        
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
            print("\\n✅ 記事をクリップボードに保存しました！")
        except Exception as e:
            print(f"⚠️ クリップボード保存に失敗: {e}")

    def print_banner(self):
        """バナー表示"""
        print("🎙️" + "=" * 60)
        print("    動的記事生成システム")
        print("    💰 音声内容に応じた記事を自動生成")
        print("=" * 62)
        print()

    def main(self):
        """メイン処理"""
        parser = argparse.ArgumentParser(description='動的記事生成システム')
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
            print("\\n" + "=" * 60)
            next_action = input("🔄 別の音声ファイルを処理しますか？ (y/N): ").lower().strip()
            if next_action not in ['y', 'yes']:
                break
        
        print("👋 お疲れさまでした！")

if __name__ == "__main__":
    generator = DynamicArticleGenerator()
    generator.main()