#!/usr/bin/env python3
"""
note記事風記事生成ツール
実際のnote記事の文体学習データに基づく高品質記事生成
"""

import os
import sys
import re
from pathlib import Path
import pyperclip
import time
from tqdm import tqdm
import anthropic

class NoteStyleGenerator:
    def __init__(self):
        self.target_length = 2500  # 約2500文字
        self.intro_length = 200    # 導入部約200文字
        self.main_length = 2000    # 主要内容約2000文字
        self.conclusion_length = 300  # 結論約300文字
        
        # Claude APIクライアント初期化
        self.client = anthropic.Anthropic()
        
        # マナミさんの文体学習データ（実際のnote記事から抽出）
        self.style_samples = self.load_style_samples()

    def load_style_samples(self):
        """マナミさんの文体学習データを読み込み"""
        style_file = Path("/Users/manami/(N)note本文.md")
        if style_file.exists():
            try:
                with open(style_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content[:10000]  # 最初の10000文字を使用
            except Exception as e:
                print(f"⚠️ スタイルファイル読み込みエラー: {e}")
                return ""
        return ""

    def show_progress(self, description, duration=1):
        """プログレスバー表示"""
        for i in tqdm(range(100), desc=description, bar_format='{desc}: {percentage:3.0f}%|{bar}| {elapsed}<{remaining}'):
            time.sleep(duration/100)

    def clean_transcript(self, text):
        """文字起こしのクリーニング（高精度版）"""
        text = text.strip()
        
        # 音声認識エラーの修正
        corrections = {
            'まなみ': 'マナミ', 'マナみ': 'マナミ', '学み': 'マナミ',
            'さにの子ども': '3人の子ども', 'さ人の子ども': '3人の子ども', 'サニーの子ども': '3人の子ども',
            'SNSはしん': 'SNS発信', 'SNSのつう': 'SNS運用', 'SNS4サポート': 'SNS運用サポート',
            'ままフリー': 'ママフリーランス', 'ままプリー': 'ママフリーランス', 'ままプリランス': 'ママフリーランス',
            'コンテンツペーサク': 'コンテンツ作成', 'コンテンツ製作': 'コンテンツ作成', 'コンテンチューサコーチュー': 'コンテンツ作成',
            'メンバーシーピ': 'メンバーシップ', 'メンバーしップ': 'メンバーシップ',
            'ライフスタル': 'ライフスタイル', 'らふスタイル': 'ライフスタイル',
            '伴奏型': '伴走型', 'バンソー型': '伴走型',
            '子どもたち': '子ども', '子供': '子ども', '娘が': '娘が',
            'です。': 'です。', 'ます。': 'ます。'
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text

    def extract_main_topic(self, text):
        """主要テーマを抽出"""
        # 音声配信でよく言及されるキーワードから主題を判定
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
        """重要な内容を段落ごとに抽出"""
        # まず、長い文章塊を作る（文単位ではなく、内容のまとまりで）
        content_blocks = []
        
        # 文を分割
        sentences = re.split(r'[。！？]', text)
        
        # 具体的な内容を含む文を優先的に抽出
        concrete_content = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # 短すぎる文は除外
                continue
            
            # 具体的な内容を示すキーワード
            concrete_indicators = [
                'メンバーシップ', '8月から', 'SNS運用サポート', '価格', '単価', '値段',
                '8000円', '15000円', '1万5千', '無料', '有料', 'プラン',
                'AI', '壁打ち', 'サービス', 'コンテンツ', '音声配信',
                '実は', '具体的に', '例えば', 'つまり', 'そうなんです',
                'ちなみに', 'というのは', 'だから'
            ]
            
            # 体験や考えを表す表現
            experience_indicators = [
                'と思っている', 'を始めて', 'をやって', 'ということで',
                'と感じて', 'を考えて', 'が必要', 'をしようと',
                'ということに', 'という話', 'ということが'
            ]
            
            # 具体的内容があるか体験談があるかチェック
            has_concrete = any(indicator in sentence for indicator in concrete_indicators)
            has_experience = any(indicator in sentence for indicator in experience_indicators)
            
            if has_concrete or has_experience:
                # フィラー語除去
                cleaned = self.remove_fillers(sentence)
                if len(cleaned) > 15:
                    concrete_content.append(cleaned + '。')
        
        # より長い文章ブロックを作成
        if len(concrete_content) >= 3:
            # 内容を3つのテーマグループに分ける
            third = len(concrete_content) // 3
            
            group1 = concrete_content[:third] if third > 0 else concrete_content[:1]
            group2 = concrete_content[third:2*third] if third > 0 else concrete_content[1:2] if len(concrete_content) > 1 else []
            group3 = concrete_content[2*third:] if third > 0 else concrete_content[2:] if len(concrete_content) > 2 else []
            
            # 各グループから文章ブロックを作成
            content_blocks = []
            if group1:
                content_blocks.append('\n\n'.join(group1[:3]))  # 最大3文
            if group2:
                content_blocks.append('\n\n'.join(group2[:3]))
            if group3:
                content_blocks.append('\n\n'.join(group3[:3]))
            
            return content_blocks
        
        # フォールバック: 重要度指標のある文を使用
        importance_indicators = [
            'と思います', 'と思うんです', 'ということです', 'なんですよね',
            'だと思うんです', 'ということで', 'という感じで'
        ]
        
        important_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 30:
                if any(indicator in sentence for indicator in importance_indicators):
                    cleaned = self.remove_fillers(sentence)
                    if len(cleaned) > 20:
                        important_sentences.append(cleaned + '。')
        
        if important_sentences:
            # 重要な文も3つのグループに分ける
            third = len(important_sentences) // 3
            if third > 0:
                group1 = important_sentences[:third]
                group2 = important_sentences[third:2*third]
                group3 = important_sentences[2*third:]
                return ['\n\n'.join(group1[:2]), '\n\n'.join(group2[:2]), '\n\n'.join(group3[:2])]
            else:
                return ['\n\n'.join(important_sentences[:2]), '', '']
        
        return []

    def remove_fillers(self, text):
        """フィラー語とノイズを除去"""
        # 基本的なフィラー語
        basic_fillers = [
            r'えー+、?', r'あの+、?', r'えっと+、?', r'うーん+、?', r'まぁ+、?',
            r'なんか+、?', r'そう+、?'
        ]
        
        # 軽度のフィラー語（一部残す）
        light_fillers = [
            r'ちょっと+、?', r'って感じで、?', r'みたいな、?'
        ]
        
        # 基本フィラー語を除去
        for filler in basic_fillers:
            text = re.sub(filler, '', text)
        
        # 軽度フィラー語は一部のみ除去（自然さを保つため）
        for filler in light_fillers:
            text = re.sub(filler, '', text, count=1)  # 1回だけ除去
        
        # 冗長な表現を簡潔に
        redundant_patterns = [
            (r'だと思うんですけど、?', 'と思います'),
            (r'なんですけど、?', 'です'),
            (r'っていう風に、?', 'という形で'),
            (r'ということなんですよね', 'ということです'),
            (r'っていうことで、?', 'ということで'),
            (r'っていうか、?', ''),
            (r'みたいな感じで、?', 'という感じで')
        ]
        
        for pattern, replacement in redundant_patterns:
            text = re.sub(pattern, replacement, text)
        
        # 繰り返し語句の除去（3回以上の繰り返しのみ）
        text = re.sub(r'(.{2,})\1{2,}', r'\1', text)
        
        # 空白の正規化
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 文の終わりを整える
        if text and not text.endswith(('。', '！', '？')):
            # 最後に動詞や形容詞で終わっている場合は「。」を追加
            if re.search(r'[ですますたしいない]$', text):
                text += '。'
        
        return text

    def create_introduction(self, main_topic, key_content):
        """導入部を作成（約200文字）"""
        # 主題の重要性を表現
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
        
        # 主題を結論として提示
        conclusion_statement = f'{main_topic}について、{importance}。'
        
        intro = f"マナミです。\n\n{conclusion_statement}\n\n今回は、そんな体験から考えたことを皆さんと共有したいと思います。"
        
        # 文字数調整
        if len(intro) > self.intro_length + 50:
            intro = f"マナミです。\n\n{main_topic}について考える機会がありました。今回は、そのことについてお話ししたいと思います。"
        
        return intro

    def create_main_content(self, key_content, target_length):
        """主要内容を作成（約2000文字）"""
        if not key_content or all(not content.strip() for content in key_content):
            return self.create_fallback_content()
        
        # 抽出された内容ブロックをそのまま使用
        sections = []
        
        # 各セクションに抽出された内容を直接使用
        for i, content_block in enumerate(key_content):
            if content_block and content_block.strip():
                # 内容ブロックをそのまま使用し、必要に応じて補完
                section = content_block.strip()
                
                # 短すぎる場合のみ補完
                if len(section) < 200:
                    if i == 0:  # 最初のセクション
                        section += '\n\nこのことについて、改めて考える機会がありました。'
                    elif i == 1:  # 中間のセクション
                        section += '\n\n実際にやってみると、思っていた以上に色々と考えることがありました。'
                    else:  # 最後のセクション
                        section += '\n\nこうした経験を通して、新しい気づきもありました。'
                
                sections.append(section)
        
        # セクションが足りない場合は空のセクションは作らない
        while len(sections) < 3 and any(sections):
            if len(sections) == 1:
                # 1つしかない場合は分割を試みる
                first_section = sections[0]
                if len(first_section) > 400:
                    # 長い場合は中間で分割
                    split_point = len(first_section) // 2
                    sentences = first_section.split('。')
                    mid_point = len(sentences) // 2
                    
                    part1 = '。'.join(sentences[:mid_point]) + '。'
                    part2 = '。'.join(sentences[mid_point:])
                    
                    sections = [part1, part2]
                else:
                    break
            elif len(sections) == 2:
                break
            else:
                break
        
        # 最低1つのセクションは確保
        if not sections:
            return self.create_fallback_content()
        
        return '\n\n---------------\n\n'.join(sections)

    def build_section(self, sentences, target_length, section_type):
        """セクションを構築"""
        if not sentences:
            return self.get_fallback_section(section_type)
        
        # 文を結合
        content = '\n\n'.join(sentences[:3])  # 最大3文まで
        
        # セクションタイプに応じた補完
        if section_type == 'context':
            if len(content) < target_length - 200:
                content += '\n\nこうしたことを日々の生活の中で考えるようになりました。実際に体験してみると、思っていた以上に難しいことも多く、試行錯誤しながら進んでいます。'
        elif section_type == 'experience':
            if len(content) < target_length - 200:
                content += '\n\n具体的な経験を通して学ぶことがたくさんあります。うまくいかないことも多いですが、その都度「どうすれば良いか」を考えながら取り組んでいます。'
        elif section_type == 'insight':
            if len(content) < target_length - 200:
                content += '\n\nこうした経験から、改めて感じることがあります。完璧ではないかもしれませんが、自分なりに考えて行動することの大切さを実感しています。'
        
        return content

    def get_fallback_section(self, section_type):
        """フォールバック用のセクション"""
        fallbacks = {
            'context': '最近、このことについて考える機会がありました。\n\n子育てと仕事を両立する日々の中で、色々と感じることがあります。思うようにいかないことも多いですが、その分学ぶことも多いです。',
            'experience': '実際に体験してみると、想像していた以上に難しい部分もありました。\n\nでも、そうした経験を通して新しい気づきもたくさんありました。一つひとつ丁寧に取り組んでいくことの大切さを感じています。',
            'insight': '今回の経験から、改めて学ぶことがありました。\n\n完璧を求めすぎず、その時その時でできることをやっていく。そんな姿勢が大切なのかもしれないと思います。'
        }
        return fallbacks.get(section_type, '')

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
        """結論部を作成（約300文字）"""
        # テーマに応じた結論
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

    def generate_with_claude(self, transcript):
        """Claude APIを使用してマナミさんの文体で記事生成"""
        prompt = f"""
以下は音声配信の文字起こしです。これをマナミさんの文体でnote記事として整理してください。

# 文体の特徴（実際のnote記事から学習）:
{self.style_samples[:3000]}

# 記事の構成要件:
- 冒頭は必ず「マナミです。」で始める
- 導入部（約200文字）: 話題の背景と重要性を説明
- 主要内容（約2000文字）: 具体的な体験談と学びを3つのセクションに分け、「---------------」で区切る
- 結論部（約300文字）: 読者へのメッセージと今後の展望
- 「です/ます」調で統一
- 「子ども」表記を使用
- 「」で強調したい部分を囲む
- 会話調で親しみやすく、でも専門的すぎない
- 具体的な体験談を交える
- 読者に共感してもらえる内容

# 文字起こし:
{transcript}

上記の文字起こしを、マナミさんの文体学習データの特徴を活かして、読みやすく構造化されたnote記事として再構成してください。
"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.3,
                messages=[{
                    "role": "user", 
                    "content": prompt
                }]
            )
            return response.content[0].text
        except Exception as e:
            print(f"⚠️ Claude API エラー: {e}")
            return self.generate_fallback_article(transcript)

    def generate_fallback_article(self, transcript):
        """フォールバック記事生成（API失敗時）"""
        clean_text = self.clean_transcript(transcript)
        main_topic = self.extract_main_topic(clean_text)
        key_content = self.extract_key_content(clean_text)
        
        introduction = self.create_introduction(main_topic, key_content)
        main_content = self.create_main_content(key_content, self.main_length)
        conclusion = self.create_conclusion(main_topic)
        
        return f"{introduction}\n\n---------------\n\n{main_content}\n\n---------------\n\n{conclusion}"

    def generate_article(self, transcript):
        """記事生成メイン"""
        print("\n🎯 記事生成を開始します...")
        
        # Step 1: 文字起こし処理
        self.show_progress("📝 文字起こしをクリーニング中", 1)
        clean_text = self.clean_transcript(transcript)
        print(f"✅ クリーニング完了: {len(clean_text)}文字")
        
        # Step 2: 文体学習データ確認
        self.show_progress("📚 文体学習データを読み込み中", 0.5)
        if self.style_samples:
            print("✅ マナミさんの文体データを使用")
        else:
            print("⚠️ 文体データが見つかりません - フォールバックモードで実行")
        
        # Step 3: Claude APIで記事生成
        self.show_progress("🤖 AI記事生成中", 3)
        article = self.generate_with_claude(clean_text)
        
        # Step 4: 後処理
        self.show_progress("✨ 最終調整中", 0.5)
        
        # 文字数確認
        total_length = len(article)
        print(f"\n📊 生成完了: {total_length}文字")
        
        return article

    def format_as_markdown(self, text):
        """マークダウン形式でフォーマット"""
        # 既にマークダウン形式の場合はそのまま返す
        if "```" in text or text.startswith("#"):
            return text
            
        # プレーンテキストをマークダウンに変換
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
                
            # 区切り線の処理
            if line == '---------------':
                formatted_lines.append('\n---\n')
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)

    def copy_to_clipboard(self, text):
        """マークダウン形式でクリップボードにコピー"""
        try:
            markdown_text = self.format_as_markdown(text)
            pyperclip.copy(markdown_text)
            print("📋 記事をマークダウン形式でクリップボードにコピーしました！")
        except Exception as e:
            print(f"⚠️ クリップボードコピー失敗: {e}")

    def save_article(self, article):
        """記事保存"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"note_article_{timestamp}.md"
        filepath = Path("/Users/manami/audio_to_article_new") / filename
        
        try:
            markdown_text = self.format_as_markdown(article)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            print(f"💾 記事をマークダウン形式で保存完了: {filename}")
            return str(filepath)
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            return None

def main():
    # コマンドライン引数をチェック
    if len(sys.argv) > 1:
        if sys.argv[1] == "--clipboard" or sys.argv[1] == "-c":
            # クリップボードから読み込み
            try:
                transcript = pyperclip.paste().strip()
                if not transcript:
                    print("❌ クリップボードが空です")
                    sys.exit(1)
                print(f"📋 クリップボードから読み込み完了: {len(transcript)}文字")
            except Exception as e:
                print(f"❌ クリップボード読み込みエラー: {e}")
                sys.exit(1)
        else:
            # ファイルから読み込み
            transcript_file = sys.argv[1]
            
            if not os.path.exists(transcript_file):
                print(f"❌ ファイルが見つかりません: {transcript_file}")
                sys.exit(1)
            
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript = f.read().strip()
                print(f"📖 ファイルから読み込み完了: {len(transcript)}文字")
            except Exception as e:
                print(f"❌ ファイル読み込みエラー: {e}")
                sys.exit(1)
    else:
        # インタラクティブモード
        print("📝 note記事風記事生成ツール")
        print("  1. クリップボードから読み込み")
        print("  2. 手動で文字起こしテキストを入力")
        print("  q. 終了")
        
        choice = input("\n選択 (1/2/q): ").strip()
        
        if choice.lower() in ['q', 'quit', 'exit']:
            print("👋 終了します")
            sys.exit(0)
        elif choice == '1':
            try:
                transcript = pyperclip.paste().strip()
                if not transcript:
                    print("❌ クリップボードが空です")
                    sys.exit(1)
                print(f"📋 クリップボードから読み込み完了: {len(transcript)}文字")
            except Exception as e:
                print(f"❌ クリップボード読み込みエラー: {e}")
                sys.exit(1)
        elif choice == '2':
            print("📝 文字起こしテキストを入力してください")
            print("   (入力完了後、空行でEnterを2回押してください)")
            print("-" * 50)
            
            lines = []
            empty_line_count = 0
            
            while True:
                try:
                    line = input()
                    if line.strip() == '':
                        empty_line_count += 1
                        if empty_line_count >= 2:
                            break
                    else:
                        empty_line_count = 0
                    lines.append(line)
                except (KeyboardInterrupt, EOFError):
                    break
            
            transcript = '\n'.join(lines).strip()
            if not transcript:
                print("❌ 文字起こしテキストが入力されませんでした")
                sys.exit(1)
            print(f"📝 入力完了: {len(transcript)}文字")
        else:
            print("❌ 無効な選択です")
            sys.exit(1)
    
    # 記事生成
    print("\n" + "=" * 60)
    print("🤖 マナミさんの文体でnote記事を生成中...")
    print("=" * 60)
    
    generator = NoteStyleGenerator()
    article = generator.generate_article(transcript)
    
    # 結果表示
    print("\n" + "=" * 80)
    print("📰 生成された記事:")
    print("=" * 80)
    print(article)
    print("=" * 80)
    
    # マークダウン形式でクリップボードにコピー
    generator.copy_to_clipboard(article)
    
    # 保存
    saved_path = generator.save_article(article)
    
    print(f"\n✅ 処理完了")
    if saved_path:
        print(f"💾 保存場所: {saved_path}")
    print("📋 記事はマークダウン形式でクリップボードにコピー済みです")

if __name__ == "__main__":
    main()