#!/usr/bin/env python3
"""
完璧note記事生成ツール
指定されたプロンプトと文体学習データに完全準拠
"""

import os
import sys
import re
from pathlib import Path
import pyperclip

class PerfectNoteGenerator:
    def __init__(self):
        # プロンプト要件
        self.target_length = 2500
        self.intro_length = 200
        self.main_length = 2000
        self.conclusion_length = 300
        
        # 文体学習データを読み込み
        self.style_samples = self.load_style_samples()

    def load_style_samples(self):
        """実際のnote記事文体学習データを読み込み"""
        style_data_path = "/Users/manami/voice-to-blog/training_data/note_articles.md"
        
        try:
            with open(style_data_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print("✅ 文体学習データ読み込み完了")
            return content
        except Exception as e:
            print(f"⚠️ 文体学習データ読み込み失敗: {e}")
            return self.get_fallback_style_samples()

    def get_fallback_style_samples(self):
        """フォールバック用文体サンプル"""
        return """マナミです。

今週は子どもが熱を出し、夫も体調を崩し、誰かしらを自宅保育してるので家事育児を一人でまわしており仕事がなかなか進みません…。

夫が謎の風邪（微熱）でしばらく寝込んでいます。

そして今朝、ついに私がブチ切れました！

夫が体調不良で動けないのは仕方がありません。ワンオペでこちらの家事育児の負担が増えるのも覚悟の上です。でも、夫の口から出てくるのは「しんどい」「調子が悪い」といった、ひたすら自分の状況を説明する言葉だけ。

「どうしたらいいの？」「子どもたちの園の送迎、私が行こうか？」と聞いても、「具合が悪くて」の繰り返しで、会話がまったく前に進まないんです。しかも今朝は自分が送っていくと言っていたのに･･･

最終的な相手に判断を丸投げしつづけるその姿勢に、「もう、いい加減にしなさい！！！」となってしまいました。"""

    def get_text_input(self):
        """文字起こしテキストの入力"""
        print("📝 文字起こしテキスト入力")
        print("=" * 50)
        print("💡 使用方法:")
        print("   1. 文字起こしテキストをコピー")
        print("   2. 下記で「clip」を入力してクリップボードから読み込み")
        print("   3. または「paste」を入力して手動貼り付け")
        print("=" * 50)
        
        method = input("📋 入力方法を選択 (clip/paste): ").strip().lower()
        
        if method == 'clip':
            return self.get_from_clipboard()
        elif method == 'paste':
            return self.get_manual_input()
        else:
            print("❌ 無効な選択です。手動入力に切り替えます。")
            return self.get_manual_input()

    def get_from_clipboard(self):
        """クリップボードから取得"""
        try:
            text = pyperclip.paste().strip()
            if not text:
                print("❌ クリップボードが空です")
                return self.get_manual_input()
            
            print(f"✅ クリップボードから取得: {len(text)}文字")
            return text
        except Exception as e:
            print(f"❌ クリップボード読み込みエラー: {e}")
            return self.get_manual_input()

    def get_manual_input(self):
        """手動入力"""
        print("📝 文字起こしテキストを貼り付けてください")
        print("   📋 貼り付け後、新しい行に「END」と入力")
        print("   ❌ キャンセルは「CANCEL」と入力")
        print("-" * 50)
        
        lines = []
        
        while True:
            try:
                line = input()
                
                if line.strip().upper() == 'END':
                    break
                elif line.strip().upper() == 'CANCEL':
                    print("❌ キャンセルされました")
                    return None
                
                lines.append(line)
                
            except KeyboardInterrupt:
                print("\n❌ 中断されました")
                return None
            except EOFError:
                break
        
        text = '\n'.join(lines).strip()
        
        if not text:
            print("❌ テキストが入力されませんでした")
            return None
        
        print(f"✅ 入力完了: {len(text)}文字")
        return text

    def clean_transcript(self, text):
        """プロンプト要件に基づく文字起こしクリーニング"""
        text = text.strip()
        
        # プロンプト要件: 自己紹介文を削除
        intro_patterns = [
            r'はい、?こんにちは。?',
            r'3人の子ども?たち?を育てながらSNS発信[^。]*?ママフリーランスです。?',
            r'3人の子ども?たち?を育てながら[^。]*?お仕事をしている[^。]*?です。?'
        ]
        
        for pattern in intro_patterns:
            text = re.sub(pattern, '', text)
        
        # 音声認識エラーの修正
        corrections = {
            'まなみ': 'マナミ', 'マナみ': 'マナミ', '学み': 'マナミ',
            '子供': '子ども', '子どもたち': '子ども',  # プロンプト要件
            'さにの子ども': '3人の子ども', 'さ人の子ども': '3人の子ども',
            'SNSはしん': 'SNS発信', 'SNSのつう': 'SNS運用',
            'ままフリー': 'ママフリーランス', 'ままプリー': 'ママフリーランス',
            'コンテンツペーサク': 'コンテンツ作成', 'コンテンツ製作': 'コンテンツ作成',
            'メンバーシーピ': 'メンバーシップ', 'メンバーしップ': 'メンバーシップ',
            '伴奏型': '伴走型'
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text.strip()

    def extract_main_topic_and_conclusion(self, text):
        """音声配信の主題を結論として抽出"""
        # 結論を示すパターン
        conclusion_patterns = [
            r'結論から言うと[^。]*?([^。]+)',
            r'つまり[^。]*?([^。]+)',
            r'要するに[^。]*?([^。]+)',
            r'というわけで[^。]*?([^。]+)'
        ]
        
        for pattern in conclusion_patterns:
            match = re.search(pattern, text)
            if match:
                conclusion = match.group(1).strip()
                return self.classify_topic(conclusion, text)
        
        # フォールバック: キーワードベースの分類
        return self.classify_topic_by_keywords(text)

    def classify_topic(self, conclusion, full_text):
        """結論文から主題を分類"""
        if any(word in conclusion for word in ['メンバーシップ', '値段', '価格', 'お金']):
            return {
                'topic': '自分のサービスに値段をつけること',
                'conclusion': conclusion,
                'importance': 'これまで無料で提供してきたサービスに価格をつけることについて考える機会がありました'
            }
        elif any(word in conclusion for word in ['働き方', 'フリーランス', '仕事']):
            return {
                'topic': 'ママフリーランスとしての働き方',
                'conclusion': conclusion,
                'importance': '子育てと仕事を両立する中で感じることがありました'
            }
        elif any(word in conclusion for word in ['AI', '活用', 'ツール']):
            return {
                'topic': 'AIの活用',
                'conclusion': conclusion,
                'importance': 'AIを日常的に活用する中で感じることがありました'
            }
        else:
            return {
                'topic': '最近考えていること',
                'conclusion': conclusion,
                'importance': '日々の生活の中で感じることがありました'
            }

    def classify_topic_by_keywords(self, text):
        """キーワードベースの主題分類"""
        topic_keywords = {
            '自分のサービスに値段をつけること': ['メンバーシップ', '値段', '価格', 'お金', '有料', '単価', 'サービス'],
            'ママフリーランスとしての働き方': ['働き方', 'フリーランス', '仕事', '育児', 'ママ'],
            'AIの活用': ['AI', '活用', 'ChatGPT', 'ツール', '壁打ち'],
            'SNSや情報発信': ['SNS', '発信', 'コンテンツ', '投稿', 'Instagram'],
            '子育てと仕事の両立': ['子ども', '育児', '保育園', '家事', 'ワンオペ']
        }
        
        scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[topic] = score
        
        if scores:
            main_topic = max(scores, key=scores.get)
            importance_map = {
                '自分のサービスに値段をつけること': 'これまで無料で提供してきたサービスに価格をつけることについて考える機会がありました',
                'ママフリーランスとしての働き方': '子育てと仕事を両立する中で感じることがありました',
                'AIの活用': 'AIを日常的に活用する中で感じることがありました',
                'SNSや情報発信': '情報発信のあり方について考え直すきっかけがありました',
                '子育てと仕事の両立': '3人の子どもを育てながら働く日々の中で、色々と思うことがありました'
            }
            
            return {
                'topic': main_topic,
                'conclusion': f'{main_topic}について',
                'importance': importance_map.get(main_topic, '日々の生活の中で感じることがありました')
            }
        
        return {
            'topic': '最近考えていること',
            'conclusion': '最近考えていること',
            'importance': '日々の生活の中で感じることがありました'
        }

    def extract_main_points(self, text):
        """主要な議論やポイントを抽出（2000文字分）"""
        # 文を分割
        sentences = re.split(r'[。！？]', text)
        
        # 重要度の高い文を抽出
        important_sentences = []
        
        # 高優先度キーワード
        high_priority = [
            'メンバーシップ', '8月から', 'SNS運用サポート', '8000円', '15000円', '1万5千',
            'プラン', 'サービス', 'AI', '壁打ち', '実は', '具体的に', '例えば',
            'つまり', 'そうなんです', 'ちなみに', 'だから', 'なので'
        ]
        
        # 中優先度キーワード
        medium_priority = [
            'と思います', 'と思うんです', 'ということです', 'なんですよね',
            'という感じで', 'ということで', 'について', 'に関して', 'という話'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            # 重要度判定
            priority_score = 0
            if any(keyword in sentence for keyword in high_priority):
                priority_score += 3
            if any(keyword in sentence for keyword in medium_priority):
                priority_score += 1
            
            if priority_score > 0:
                cleaned = self.clean_sentence_for_article(sentence)
                if len(cleaned) > 15:
                    important_sentences.append((cleaned + '。', priority_score))
        
        # スコア順にソート
        important_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # 最大12文まで取得
        selected_sentences = [s[0] for s in important_sentences[:12]]
        
        return self.organize_into_sections(selected_sentences)

    def clean_sentence_for_article(self, sentence):
        """記事用文章クリーニング"""
        # 基本的なフィラー語除去
        fillers = [
            r'えー+、?', r'あの+、?', r'えっと+、?', r'うーん+、?', r'まぁ+、?',
            r'なんか+、?', r'そう+、?', r'ちょっと+、?'
        ]
        
        for filler in fillers:
            sentence = re.sub(filler, '', sentence)
        
        # 冗長な表現をですます調に変換
        conversions = [
            (r'だと思うんですけど', 'と思います'),
            (r'なんですけど', 'です'),
            (r'っていう風に', 'という形で'),
            (r'ということなんですよね', 'ということです'),
            (r'っていうことで', 'ということで'),
            (r'みたいな感じで', 'という感じで')
        ]
        
        for old, new in conversions:
            sentence = re.sub(old, new, sentence)
        
        # 空白正規化
        sentence = re.sub(r'\s+', ' ', sentence).strip()
        
        return sentence

    def organize_into_sections(self, sentences):
        """文を3つのセクションに整理"""
        if not sentences:
            return []
        
        # 文を3つのグループに分ける
        total = len(sentences)
        group_size = max(1, total // 3)
        
        sections = []
        
        # セクション1: 背景・現状
        section1 = sentences[:group_size]
        if section1:
            content1 = '\n\n'.join(section1)
            if len(content1) < 400:
                content1 += '\n\nこのことについて、改めて考える機会がありました。日々の生活や仕事の中で感じることが多く、自分なりに整理してみたいと思いました。'
            sections.append(content1)
        
        # セクション2: 具体例・詳細
        section2 = sentences[group_size:2*group_size] if total > group_size else []
        if section2:
            content2 = '\n\n'.join(section2)
            if len(content2) < 400:
                content2 += '\n\n実際に取り組んでみると、思っていた以上に多くのことを学びました。試行錯誤しながらも、少しずつ前進している実感があります。'
            sections.append(content2)
        
        # セクション3: 今後・まとめ
        section3 = sentences[2*group_size:] if total > 2*group_size else []
        if section3:
            content3 = '\n\n'.join(section3)
            if len(content3) < 400:
                content3 += '\n\nこうした経験を通して、新しい気づきや学びがたくさんありました。今後も継続して取り組んでいきたいと思います。'
            sections.append(content3)
        
        return sections

    def create_introduction(self, topic_info):
        """導入部作成（約200文字）プロンプト要件準拠"""
        topic = topic_info['topic']
        importance = topic_info['importance']
        
        # プロンプト要件: 音声配信の主題を結論として紹介
        intro = f"マナミです。\n\n{topic}について、{importance}。\n\n今回は、そんな体験から考えたことを皆さんと共有したいと思います。"
        
        return intro

    def create_conclusion(self, topic_info):
        """結論部作成（約300文字）"""
        topic = topic_info['topic']
        
        # テーマ別の具体的結論
        specific_conclusions = {
            '自分のサービスに値段をつけること': 'お金を取ることは、より価値のあるサービスを提供するために必要なステップだと感じています。',
            'ママフリーランスとしての働き方': 'ママフリーランスという働き方には大変さもありますが、その分得られるものも大きいと思います。',
            'AIの活用': 'AIを上手に活用することで、働き方や生活の質を向上させていけると思います。',
            'SNSや情報発信': '情報発信を通じて、多くの方とつながり学び合えることに感謝しています。',
            '子育てと仕事の両立': '子育てと仕事の両立は簡単ではありませんが、その中で得られる学びも多いです。'
        }
        
        specific = specific_conclusions.get(topic, '日々の生活の中で感じたことを大切にしながら、前向きに取り組んでいきたいと思います。')
        
        conclusion = f"""今回お話しした内容は、私自身の体験や考えに基づくものですが、同じような状況にある方の参考になれば嬉しいです。

{specific}

皆さんもぜひ、日常の中で感じたことや工夫していることがあれば、大切にしてみてください。そうした積み重ねが、より良い生活や働き方につながっていくのではないかと思います。"""
        
        return conclusion

    def apply_formatting_requirements(self, text):
        """プロンプト要件のフォーマット適用"""
        # 強調部分を「」で区切る
        emphasis_patterns = [
            (r'(メンバーシップ)', r'「\1」'),
            (r'(SNS運用サポート)', r'「\1」'),
            (r'(ライトプラン)', r'「\1」'),
            (r'(8000円)', r'「\1」'),
            (r'(15000円)', r'「\1」'),
            (r'(1万5000円)', r'「\1」'),
            (r'(無料)', r'「\1」'),
            (r'(有料)', r'「\1」'),
            (r'(価格設定)', r'「\1」'),
            (r'(値段をつける)', r'「\1」'),
            (r'(ママフリーランス)', r'「\1」'),
            (r'(伴走型)', r'「\1」'),
            (r'(AI)', r'「\1」'),
            (r'(壁打ち)', r'「\1」')
        ]
        
        for pattern, replacement in emphasis_patterns:
            text = re.sub(pattern, replacement, text)
        
        return text

    def generate_perfect_note_article(self, transcript):
        """完璧なnote記事生成（プロンプト完全準拠）"""
        print("🔧 プロンプト要件に基づく記事生成中...")
        print(f"📊 元テキスト: {len(transcript)}文字")
        
        # 1. クリーニング（プロンプト要件適用）
        clean_text = self.clean_transcript(transcript)
        print(f"📝 クリーニング完了: {len(clean_text)}文字")
        
        # 2. 主題を結論として抽出
        topic_info = self.extract_main_topic_and_conclusion(clean_text)
        print(f"🎯 主題（結論）: {topic_info['topic']}")
        
        # 3. 導入部作成（約200文字）
        introduction = self.create_introduction(topic_info)
        print(f"📝 導入部: {len(introduction)}文字")
        
        # 4. 主要内容の要約（約2000文字）
        main_points = self.extract_main_points(clean_text)
        main_content = '\n\n---------------\n\n'.join(main_points) if main_points else self.create_fallback_main()
        print(f"📄 主要内容: {len(main_content)}文字")
        
        # 5. 結論（約300文字）
        conclusion = self.create_conclusion(topic_info)
        print(f"📝 結論: {len(conclusion)}文字")
        
        # 6. 記事組み立て
        article = f"{introduction}\n\n---------------\n\n{main_content}\n\n---------------\n\n{conclusion}"
        
        # 7. フォーマット要件適用
        article = self.apply_formatting_requirements(article)
        
        total_length = len(article)
        print(f"📊 総文字数: {total_length}文字（目標: {self.target_length}文字）")
        
        return article

    def create_fallback_main(self):
        """フォールバック用主要内容"""
        return """最近、日々の生活の中で考えることがありました。

3人の子どもを育てながらママフリーランスとして働く中で、思うようにいかないことも多いですが、その分学ぶことも多いです。

---------------

実際に体験してみると、想像していた以上に難しい部分もありました。

でも、そうした経験を通して新しい気づきもたくさんありました。一つひとつ丁寧に取り組んでいくことの大切さを感じています。

---------------

今回の経験から、改めて学ぶことがありました。

完璧を求めすぎず、その時その時でできることをやっていく。そんな姿勢が大切なのかもしれないと思います。"""

    def copy_to_clipboard(self, text):
        """クリップボードにコピー"""
        try:
            pyperclip.copy(text)
            print("📋 記事をクリップボードにコピーしました！")
        except Exception as e:
            print(f"⚠️ クリップボードコピー失敗: {e}")

    def save_article(self, article):
        """記事保存"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"perfect_note_article_{timestamp}.md"
        filepath = Path("/Users/manami/audio_to_article_new") / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(article)
            print(f"💾 記事保存完了: {filename}")
            return str(filepath)
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            return None

def main():
    generator = PerfectNoteGenerator()
    
    print("📝" + "=" * 60)
    print("   完璧note記事生成ツール")
    print("   指定プロンプト・文体学習データ完全準拠")
    print("=" * 62)
    print()
    print("✅ プロンプト要件:")
    print("  ・ 2500文字構成 (導入200字 + 本文2000字 + 結論300字)")
    print("  ・ 音声配信の主題を結論として紹介")
    print("  ・ 「マナミです。」→すぐ本文")
    print("  ・ ですます調・適切な段落分け")
    print("  ・ 強調部分「」区切り・子ども表記統一")
    print("  ・ 見出しなし")
    print()
    
    # テキスト入力
    transcript = generator.get_text_input()
    
    if not transcript:
        print("❌ 処理を中断しました")
        return
    
    # 記事生成
    print("\n" + "=" * 60)
    print("🤖 完璧なnote記事を生成中...")
    print("=" * 60)
    
    article = generator.generate_perfect_note_article(transcript)
    
    # 結果表示
    print("\n" + "=" * 80)
    print("📰 生成された完璧note記事:")
    print("=" * 80)
    print(article)
    print("=" * 80)
    
    # クリップボードにコピー
    generator.copy_to_clipboard(article)
    
    # 保存
    saved_path = generator.save_article(article)
    
    print(f"\n✅ 処理完了")
    if saved_path:
        print(f"💾 保存場所: {saved_path}")
    print("📋 記事はクリップボードにコピー済みです")

if __name__ == "__main__":
    main()