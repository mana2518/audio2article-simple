#!/usr/bin/env python3
"""
シンプル記事生成ツール
文字起こしから note記事風の記事を生成
"""

import os
import sys
import re
from pathlib import Path
import pyperclip

class SimpleArticleGenerator:
    def __init__(self):
        self.article_template = self.load_article_template()

    def load_article_template(self):
        """note記事のテンプレート（実際の文体に基づく）"""
        return {
            "intro": "マナミです。\n\n{main_topic}について最近考えていることがあったので、今日はそのことについてお話ししたいと思います。\n\n3人の子どもを育てながらママフリーランスとして働いている中で、{context}。今回は、そんな体験から感じたことを皆さんと共有できればと思います。",
            
            "section_break": "---------------",
            
            "conclusion": "今回お話しした内容は、私自身の体験や考えに基づくものですが、同じような状況にある方の参考になれば嬉しいです。\n\n{concluding_thought}\n\n皆さんもぜひ、日常の中で感じたことや工夫していることがあれば、大切にしてみてください。そうした積み重ねが、より良い生活や働き方につながっていくのではないかと思います。"
        }

    def clean_transcript(self, text):
        """文字起こしのクリーニング（軽量版）"""
        # 基本的なクリーニング
        text = text.strip()
        
        # よくある音声認識エラーを修正
        corrections = {
            'まなみ': 'マナミ', 'マナみ': 'マナミ',
            'さにの子ども': '3人の子ども', 'さ人の子ども': '3人の子ども',
            'SNSはしん': 'SNS発信', 'SNSのつう': 'SNS運用',
            'ままフリー': 'ママフリーランス', 'ままプリー': 'ママフリーランス',
            'コンテンツペーサク': 'コンテンツ作成', 'コンテンツ製作': 'コンテンツ作成',
            'メンバーシーピ': 'メンバーシップ', 'メンバーしップ': 'メンバーシップ',
            'ライフスタル': 'ライフスタイル', 'らふスタイル': 'ライフスタイル'
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
            
        return text

    def extract_main_theme(self, text):
        """メインテーマを抽出"""
        # テーマ関連キーワード
        theme_keywords = {
            'pricing': ['値段', '価格', '単価', 'お金', '有料', '無料', 'メンバーシップ', 'サービス'],
            'work': ['仕事', '働き方', 'フリーランス', 'クライアント', 'SNS運用'],
            'life': ['生活', '子ども', '育児', '家事', '時間', 'ライフスタイル'],
            'content': ['コンテンツ', '発信', '情報', '音声配信', 'note'],
            'business': ['ビジネス', '価値提供', 'マネタイズ', 'サポート']
        }
        
        theme_scores = {}
        for theme, keywords in theme_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                theme_scores[theme] = score
        
        # 最も多いテーマを返す
        if theme_scores:
            main_theme = max(theme_scores, key=theme_scores.get)
            return main_theme
        return 'life'

    def extract_key_points(self, text):
        """重要なポイントを抽出"""
        # 文を分割
        sentences = re.split(r'[。！？]', text)
        
        # 重要そうな文を抽出
        important_sentences = []
        
        # 重要度を示すキーワード
        important_indicators = [
            'と思います', 'と思うんです', 'と感じています', 'ということです',
            'なんですよね', 'だと思うんです', 'ということで', 'という感じで',
            'ということに', 'ということを', 'という話', 'ということが'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # 最低文字数
                # 重要度チェック
                if any(indicator in sentence for indicator in important_indicators):
                    # フィラーワードを除去
                    cleaned = self.remove_fillers(sentence)
                    if len(cleaned) > 15:
                        important_sentences.append(cleaned)
        
        return important_sentences[:6]  # 最大6文まで

    def remove_fillers(self, text):
        """フィラー語を除去"""
        fillers = [
            r'えー+', r'あの+', r'えっと+', r'うーん+', r'まぁ+',
            r'なんか+', r'ちょっと+', r'でも+', r'そう+',
            r'っていうか', r'みたいな', r'っていう感じ',
            r'だと思うんですけど', r'なんですけど'
        ]
        
        for filler in fillers:
            text = re.sub(filler, '', text)
        
        return re.sub(r'\s+', ' ', text).strip()

    def create_theme_content(self, theme, key_points):
        """テーマに基づく内容作成"""
        
        theme_configs = {
            'pricing': {
                'topic': '自分の情報や作業に値段をつけること',
                'context': '自分のサービスに価格設定をする必要を感じることがありました',
                'conclusion': 'お金を取ることは、より価値のあるサービスを提供するための必要なステップだと思います。'
            },
            'work': {
                'topic': 'フリーランスとしての働き方',
                'context': '子育てと仕事のバランスを取りながら働く中で様々な気づきがありました',
                'conclusion': 'フリーランスという働き方には大変さもありますが、その分得られるものも大きいと感じています。'
            },
            'life': {
                'topic': '最近の生活',
                'context': '毎日の子育てや家事の中で感じることがたくさんありました',
                'conclusion': '完璧を求めすぎず、その時その時でできることをやっていく姿勢を大切にしたいと思います。'
            },
            'content': {
                'topic': '情報発信について',
                'context': 'コンテンツ作成や発信について考える機会がありました',
                'conclusion': '発信を通じて多くの方とつながり、学び合えることに感謝しています。'
            },
            'business': {
                'topic': 'ビジネスについて',
                'context': 'サービス提供や価値創造について考えることがありました',
                'conclusion': '自分の価値を理解し、適切に提供していくことの大切さを感じています。'
            }
        }
        
        config = theme_configs.get(theme, theme_configs['life'])
        return config

    def generate_article(self, transcript):
        """記事生成メイン"""
        print("🔧 文字起こしを処理中...")
        
        # クリーニング
        clean_text = self.clean_transcript(transcript)
        
        # テーマ抽出
        theme = self.extract_main_theme(clean_text)
        print(f"📝 検出されたテーマ: {theme}")
        
        # 重要ポイント抽出
        key_points = self.extract_key_points(clean_text)
        print(f"📄 抽出されたポイント: {len(key_points)}個")
        
        # テーマ設定取得
        theme_config = self.create_theme_content(theme, key_points)
        
        # 記事構成
        intro = self.article_template["intro"].format(
            main_topic=theme_config['topic'],
            context=theme_config['context']
        )
        
        # メインコンテンツ（抽出したポイントを使用）
        main_content = []
        
        if len(key_points) >= 3:
            section1 = f"{key_points[0]}。\n\n" + \
                      f"{key_points[1] if len(key_points) > 1 else ''}\n\n" + \
                      "毎日の生活の中で、こうしたことを考える機会が増えています。実際に体験してみることで初めて分かることも多く、試行錯誤しながら進んでいます。"
            
            section2 = f"{key_points[2] if len(key_points) > 2 else ''}。\n\n" + \
                      f"{key_points[3] if len(key_points) > 3 else ''}\n\n" + \
                      "具体的な経験を通して学ぶことがたくさんあります。完璧ではないかもしれませんが、その時その時で最善を尽くしていこうと思います。"
            
            section3 = f"{key_points[4] if len(key_points) > 4 else ''}。\n\n" + \
                      f"{key_points[5] if len(key_points) > 5 else ''}\n\n" + \
                      "今後も継続して取り組んでいきたいと思います。皆さんにとっても何かの参考になれば嬉しいです。"
        else:
            # フォールバック
            section1 = "最近、このことについて考える機会がありました。\n\n3人の子どもを育てながら働く中で、様々な気づきがあります。"
            section2 = "実際に体験してみることで、新しい発見もたくさんありました。\n\n試行錯誤しながらも、前向きに取り組んでいます。"
            section3 = "今後も学び続けながら、より良い方法を見つけていきたいと思います。\n\n皆さんとも共有できることがあれば、またお話ししたいと思います。"
        
        main_content = [section1, section2, section3]
        
        conclusion = self.article_template["conclusion"].format(
            concluding_thought=theme_config['conclusion']
        )
        
        # 記事組み立て
        separator = f"\n\n{self.article_template['section_break']}\n\n"
        
        article = f"{intro}{separator}{main_content[0]}{separator}{main_content[1]}{separator}{main_content[2]}{separator}{conclusion}"
        
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
        filename = f"article_simple_{timestamp}.md"
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
        # 引数なしの場合はインタラクティブモード
        print("📝 使用方法を選択してください:")
        print("  1. クリップボードから読み込み")
        print("  2. 手動で文字起こしテキストを入力")
        print("  q. 終了")
        
        choice = input("\n選択 (1/2/q): ").strip()
        
        if choice.lower() in ['q', 'quit', 'exit']:
            print("👋 終了します")
            sys.exit(0)
        elif choice == '1':
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
        elif choice == '2':
            # 手動入力
            print("📝 文字起こしテキストを入力してください")
            print("   (入力完了後、空行でEnterを2回押してください)")
            print("   (キャンセルするには 'q' を入力)")
            print("-" * 50)
            
            lines = []
            empty_line_count = 0
            
            while True:
                try:
                    line = input()
                    
                    if line.strip().lower() == 'q':
                        print("👋 キャンセルしました")
                        sys.exit(0)
                    
                    if line.strip() == '':
                        empty_line_count += 1
                        if empty_line_count >= 2:
                            break
                    else:
                        empty_line_count = 0
                    
                    lines.append(line)
                    
                except KeyboardInterrupt:
                    print("\n👋 キャンセルしました")
                    sys.exit(0)
                except EOFError:
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
    generator = SimpleArticleGenerator()
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
    
    # 保存
    saved_path = generator.save_article(article)
    
    print(f"\n✅ 処理完了")
    if saved_path:
        print(f"💾 保存場所: {saved_path}")

if __name__ == "__main__":
    main()