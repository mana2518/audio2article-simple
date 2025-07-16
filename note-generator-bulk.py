#!/usr/bin/env python3
"""
大容量対応note記事生成ツール
1万文字でも確実に処理できるバルク処理対応版
"""

import os
import sys
import re
from pathlib import Path
import pyperclip

class BulkNoteGenerator:
    def __init__(self):
        self.target_length = 2500
        self.intro_length = 200
        self.main_length = 2000
        self.conclusion_length = 300

    def process_large_text(self):
        """大容量テキストの一括処理"""
        print("📝 大容量文字起こし対応 note記事生成")
        print("=" * 50)
        print("💡 使用方法:")
        print("   1. 文字起こしテキストを全選択してコピー")
        print("   2. 下記で「y」を入力")
        print("   3. Cmd+V で一括貼り付け")
        print("   4. 「END」と入力して完了")
        print("=" * 50)
        
        proceed = input("📋 クリップボードから大容量テキストを処理しますか？ (y/N): ").strip().lower()
        
        if proceed in ['y', 'yes']:
            return self.get_from_clipboard()
        else:
            return self.get_bulk_input()

    def get_from_clipboard(self):
        """クリップボードから直接取得"""
        try:
            text = pyperclip.paste().strip()
            if not text:
                print("❌ クリップボードが空です")
                return None
            
            print(f"✅ クリップボードから取得完了: {len(text)}文字")
            return text
        except Exception as e:
            print(f"❌ クリップボード読み込みエラー: {e}")
            return self.get_bulk_input()

    def get_bulk_input(self):
        """大容量テキストの一括入力"""
        print("📝 文字起こしテキストを貼り付けてください")
        print("   📋 Cmd+V で一括貼り付け可能")
        print("   ✅ 完了したら新しい行に「END」と入力")
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
                
                # 進捗表示（1000文字ごと）
                total_chars = len('\n'.join(lines))
                if total_chars > 0 and total_chars % 1000 == 0:
                    print(f"📊 現在: {total_chars}文字")
                
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

    def extract_key_content_bulk(self, text):
        """大容量テキストから重要な内容を効率的に抽出"""
        print("🔍 大容量テキストから重要内容を抽出中...")
        
        # テキストを段落に分割
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
        
        # 文に分割
        sentences = []
        for paragraph in paragraphs:
            paragraph_sentences = re.split(r'[。！？]', paragraph)
            for sentence in paragraph_sentences:
                sentence = sentence.strip()
                if len(sentence) > 20:
                    sentences.append(sentence)
        
        print(f"📊 抽出された文: {len(sentences)}個")
        
        # 優先度の高い内容を抽出
        high_priority_content = []
        medium_priority_content = []
        
        # 高優先度キーワード
        high_priority_keywords = [
            'メンバーシップ', '8月から', 'SNS運用サポート', '価格', '単価', '値段',
            '8000円', '15000円', '1万5千', 'プラン', 'サービス',
            'AI', '壁打ち', '結論から言うと', '実は', '具体的に'
        ]
        
        # 中優先度キーワード
        medium_priority_keywords = [
            'と思います', 'と思うんです', 'ということです', 'なんですよね',
            'という感じで', 'ということで', 'について', 'に関して'
        ]
        
        for sentence in sentences:
            cleaned = self.remove_fillers(sentence)
            if len(cleaned) < 15:
                continue
                
            # 高優先度チェック
            if any(keyword in sentence for keyword in high_priority_keywords):
                high_priority_content.append(cleaned + '。')
            # 中優先度チェック
            elif any(keyword in sentence for keyword in medium_priority_keywords):
                medium_priority_content.append(cleaned + '。')
        
        # 組み合わせて最適な内容を選択
        selected_content = high_priority_content[:6] + medium_priority_content[:3]
        
        # 3つのグループに分ける
        if len(selected_content) >= 3:
            third = len(selected_content) // 3
            group1 = selected_content[:third] if third > 0 else selected_content[:1]
            group2 = selected_content[third:2*third] if third > 0 else selected_content[1:2] if len(selected_content) > 1 else []
            group3 = selected_content[2*third:] if third > 0 else selected_content[2:] if len(selected_content) > 2 else []
            
            content_blocks = []
            if group1:
                content_blocks.append('\n\n'.join(group1[:4]))  # 最大4文
            if group2:
                content_blocks.append('\n\n'.join(group2[:4]))
            if group3:
                content_blocks.append('\n\n'.join(group3[:4]))
            
            return content_blocks
        
        return []

    def remove_fillers(self, text):
        """フィラー語除去（高速版）"""
        # 基本的なフィラー語のみ除去
        basic_fillers = [
            r'えー+、?', r'あの+、?', r'えっと+、?', r'うーん+、?', r'まぁ+、?',
            r'なんか+、?', r'そう+、?'
        ]
        
        for filler in basic_fillers:
            text = re.sub(filler, '', text)
        
        # 冗長な表現を簡潔に
        text = re.sub(r'だと思うんですけど、?', 'と思います', text)
        text = re.sub(r'なんですけど、?', 'です', text)
        text = re.sub(r'ということなんですよね', 'ということです', text)
        
        text = re.sub(r'\s+', ' ', text).strip()
        
        if text and not text.endswith(('。', '！', '？')):
            if re.search(r'[ですますたしいない]$', text):
                text += '。'
        
        return text

    def create_introduction(self, main_topic):
        """導入部を作成"""
        topic_descriptions = {
            '自分のサービスに値段をつけること': 'これまで無料で提供してきたサービスに価格をつけることの意味について、改めて考える機会がありました',
            'ママフリーランスとしての働き方': '子育てと仕事を両立する中で感じることがたくさんありました',
            'コミュニケーションの重要性': '相手の立場を考えたやり取りの大切さを実感する出来事がありました',
            'AIの活用について': 'AIを日常的に活用する中で感じることがありました',
            '情報発信について': '情報発信のあり方について考え直すきっかけがありました',
            '子育てと仕事の両立': '3人の子どもを育てながら働く日々の中で、色々と思うことがありました'
        }
        
        description = topic_descriptions.get(main_topic, '日々の生活の中で感じることがありました')
        
        intro = f"マナミです。\n\n{main_topic}について、{description}。\n\n今回は、そんな体験から考えたことを皆さんと共有したいと思います。"
        
        return intro

    def create_main_content(self, key_content):
        """主要内容を作成"""
        if not key_content or all(not content.strip() for content in key_content):
            return self.create_fallback_content()
        
        sections = []
        
        for i, content_block in enumerate(key_content):
            if content_block and content_block.strip():
                section = content_block.strip()
                
                # 短すぎる場合のみ補完
                if len(section) < 150:
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
        """フォールバック用コンテンツ"""
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
        specific_thoughts = {
            '自分のサービスに値段をつけること': 'お金を取ることは、より価値のあるサービスを提供するために必要なステップだと感じています。',
            'ママフリーランスとしての働き方': 'ママフリーランスという働き方には大変さもありますが、その分得られるものも大きいと思います。',
            'コミュニケーションの重要性': '相手の立場を考えたコミュニケーションの大切さを、改めて実感しています。',
            'AIの活用について': 'AIを上手に活用することで、働き方や生活の質を向上させていけると思います。',
            '情報発信について': '情報発信を通じて、多くの方とつながり学び合えることに感謝しています。',
            '子育てと仕事の両立': '子育てと仕事の両立は簡単ではありませんが、その中で得られる学びも多いです。'
        }
        
        specific_thought = specific_thoughts.get(main_topic, '日々の生活の中で感じたことを大切にしながら、前向きに取り組んでいきたいと思います。')
        
        conclusion = f"""今回お話しした内容は、私自身の体験や考えに基づくものですが、同じような状況にある方の参考になれば嬉しいです。

{specific_thought}

皆さんもぜひ、日常の中で感じたことや工夫していることがあれば、大切にしてみてください。そうした積み重ねが、より良い生活や働き方につながっていくのではないかと思います。"""
        
        return conclusion

    def generate_article(self, transcript):
        """記事生成メイン"""
        print("🔧 大容量文字起こしを処理中...")
        print(f"📊 元テキスト: {len(transcript)}文字")
        
        # クリーニング
        clean_text = self.clean_transcript(transcript)
        print(f"📝 クリーニング完了: {len(clean_text)}文字")
        
        # 主要テーマ抽出
        main_topic = self.extract_main_topic(clean_text)
        print(f"🎯 主要テーマ: {main_topic}")
        
        # 重要内容抽出（大容量対応）
        key_content = self.extract_key_content_bulk(clean_text)
        print(f"📄 抽出された重要ブロック: {len(key_content)}個")
        
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
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"note_article_bulk_{timestamp}.md"
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
    generator = BulkNoteGenerator()
    
    print("📝" + "=" * 50)
    print("   大容量対応 note記事生成ツール")
    print("   1万文字でも確実に処理")
    print("=" * 52)
    print()
    
    # 大容量テキスト処理
    transcript = generator.process_large_text()
    
    if not transcript:
        print("❌ 処理を中断しました")
        return
    
    # 記事生成
    print("\n" + "=" * 60)
    print("🤖 note記事を生成中...")
    print("=" * 60)
    
    article = generator.generate_article(transcript)
    
    # 結果表示
    print("\n" + "=" * 80)
    print("📰 生成された記事:")
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