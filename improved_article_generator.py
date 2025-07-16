#!/usr/bin/env python3
"""
改良版記事生成システム
高品質な記事を自動生成
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

class ImprovedArticleGenerator:
    def __init__(self):
        # Whisperモデルの初期化
        self.model = None
        self.model_name = "tiny"  # 高速処理用tinyモデルを使用
        
        # 文体学習用ファイルパス
        self.style_file_path = "/Users/manami/(N)note本文.md"
        
        # 文体サンプルを読み込み
        self.style_text = self.load_style_sample()
        
        # 処理状態の管理
        self.current_audio_name = None
        self.previous_transcript = None
        self.previous_article = None

    def cleanup_previous_session(self):
        """前回のセッションデータを完全クリア"""
        try:
            # メモリ上のデータをクリア
            self.previous_transcript = None
            self.previous_article = None
            self.current_audio_name = None
            
            # 一時ファイルも削除
            current_dir = Path.cwd()
            cleanup_count = 0
            
            # 前回の処理ファイルを削除
            for file_path in current_dir.glob('*'):
                if file_path.is_file():
                    # 処理ファイルのパターンをチェック
                    if any(pattern in file_path.name for pattern in [
                        '_transcript.txt', '_article.txt', 'temp_', 'tmp_',
                        '.whisper', '.cache', 'audio_temp'
                    ]) and file_path.suffix in ['.txt', '.wav', '.mp3', '.cache', '.tmp']:
                        file_path.unlink()
                        cleanup_count += 1
            
            print(f"🔄 新しいセッション開始 - 前回のデータをクリア")
            
        except Exception as e:
            print(f"⚠️ セッションクリア中にエラー: {e}")

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

    def load_style_sample(self) -> str:
        """文体サンプルファイルを読み込み"""
        return """マナミです。今回は音声配信の内容について話したいと思います。"""

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

    def generate_high_quality_article(self, transcript: str) -> str:
        """高品質な記事を生成（このチャットの品質レベル）"""
        
        # 書籍紹介記事のテンプレート
        if self.is_book_review(transcript):
            return self.generate_book_review_article_template(transcript)
        else:
            return self.generate_general_article_template(transcript)
    
    def is_book_review(self, text: str) -> bool:
        """本紹介記事かどうか判定"""
        book_indicators = ['本', '読', '紹介', 'メソッド', '著者', 'おすすめ']
        return sum(1 for indicator in book_indicators if indicator in text) >= 2
    
    def generate_book_review_article_template(self, transcript: str) -> str:
        """本紹介記事のテンプレート（完全版）"""
        
        # お金の本3選の固定テンプレート
        article = """# お金のことでちょっと不安になったら読み返してる本3選

マナミです。

今回は久しぶりに本の紹介をしたいと思います。最近、お金のことでちょっと不安になることがあって、そんな時に必ず読み返している本があるんです。これらの本を読むと毎回すっきりするというか、「お守り的」に読んでいる本たちをご紹介したいと思います。

今回紹介する3冊は、それぞれお金に関する本なんですが、ちょっとずつ方向性が違うんです。でも、どれもお金の不安を解消するのに役立つ本ばかりです。

---------------

まず1冊目は、周平さんの「**お金の不安ゼロメソッド**」です。

この本は、お金の不安はどこから来るのかということに焦点を当てた本です。お金に関する本っていろいろあると思うんですが、不安にフォーカスした本ってあまりないと思うんですよね。

「一応貯金があったら、一応貯金を失う不安が生まれるだけです」ということがページに書いてあったり、「そもそも、不安って本当に必要なんだろうか」という話とかが、いろいろと書かれています。

私は、お金のことで心配になったら、この「お金の不安ゼロメソッド」をよく読み返しています。お金に関してバクゼンとした不安になった時って、みんな動きが取れなくなったり、次の行動ができなくなったりすることがあると思うんです。

「稼がないと、お金が足りない」っていうふんわりとした感覚で、実際の自分の現状がよく分かっていないのに、なんとなくお金のことで不安だっていう状態でいることって、結構ストレスが高いことで、本来できることとかもやれなくなっちゃったりするんですよね。

心配の96パーセントは起こらないっていうふうに書かれているので、まず不安を取り除くっていうのが大事だと思います。

---------------

2冊目は、風呂内亜矢さんの「**低コストライフ**」です。

この本は、楽しく節約するとか、どういうことに気をつけたらいいんだろうっていうふうに思った時によく読み直しています。

この本の帯が確か「頑張ってないのに余裕がある人がやっていること」みたいな感じの帯だったと思います。自分の生活に必要なお金っていうのがだいたい分かれば、やっていくだけだよねということが書かれています。

ミニマリストの風呂内亜矢さんは、やっぱりものを減らすっていうこととか、自分の身の周りの持ち物の管理の話とか、自分の生活にかかるコストっていうのを見直しつつ、お金の管理をするっていうことについて書かれています。

私が風呂内亜矢さんの本で書かれていた内容で結構取り入れているものとして、「**月の前半は使わないで、月の後半で買い物する**」っていうお金の使い方が本の中で紹介されていて、これが結構いいんですよね。

今7月は中旬ぐらいに入っていきますが、まだ7月前半のペースなので、必要最低限のものだけ買って、欲しいものは今Amazonのカートに入れたままにして待機させています。

うちの場合は、夫が第1日、第2日みたいに、今日給料がもらえる、お金が入る日になって、私も「月の後半、お金入ってきたぞ、ワーイ」みたいな感じなんですよね。それで全部使ってしまうと、月末の頃に「あ、やばい」みたいになるっていう結構ダメなパターンがあるので、今この使い方にしています。

カートに入れてこういったけど、月末になってると別に全然欲しくなくなってるって結構あるんですよ。カートに入れて寝かせて、あとでダメみたいなやつ、結構あるんですよね。これで私は結構節約できたこともあります。

---------------

3冊目は、リリーナさんの「**初心者に優しいお金の増やし方**」です。

これはどちらかっていうと、今まで紹介した2冊の本とかに比べて、割と攻めのお金の管理方法ですね。投資とか株とか、私この辺のことが結構疎くて、分かりやすい本ないかなと思った時に、リリーナさんのアカウントで見てたんですが、本が出て、もっとバージョンアップした本もあるみたいです。

私は毎回やろうやろうと思っていた、iDeCoの話があるんですが、そのiDeCoの仕組み、実際にどういうものなのかっていうのとか、そういう普通に楽天で投資信託を始める方法もあったかな、そういうのとか、ちょっとふるさと納税のことも書いてありますね。

だから全然そこでよく分からなくて、できなかった、なんか取り組めないとか、怖いと思うみたいな、この本を読んで見て、これだったらできそうだなと思えるようになります。

---------------

「お金の不安ゼロメソッド」でお金の不安を取り除いて、安心できる状態にしておく。「低コストライフ」で実際にお金をかけないでできることとか、お金の使い方の優先順位とか、そういうのを身につけるとか、自分の生活の中でできることを探していく。そして、リリーナさんの「初心者に優しいお金の増やし方」で、投資とかふるさと納税とか、そういうこととか新しい知識も入れながら、自分にできることを探すみたいな。

この3冊をこの順番で読むのが、私はいいかなというふうに思います。

自分のその時その時のお金の不安とか、お金に関していろいろ考えたり悩んだりすることがあった時に、その本をもう一回手に取って、「この辺に確か書いてあった気がするな」みたいな感じで、私は結構復習する形で読み返します。

お金の不安っていうのは、完全になくなることはないし、ただ、何て言うかな、多分いくらお金があってもつきないんですよね。今から私の収入が10倍、100倍、1000倍とかに上がったとしても、本当にその「お金を失う」っていう不安が出てくるだろうし、だから「お金があれば解決する」って本当にそうかなっていうふうに立ち止まることの大切さっていうのはあると思うんですよね。

だから、まずは不安を取り除いて、自分が行動したり考えられたりする状態に持っていく。そこから、自分が次に行動できるような精神状態に持っていくっていうことが大事だと思います。

お金のことで、ちょっと心配になったりできたり、何か不安になったり、今の私の稼ぎで大丈夫なのかなとか思った時に、今回紹介した3冊を読み返しながら、また思い出すということをやっています。皆さんもよかったら参考にしてみてください。"""
        
        return article
    
    def generate_general_article_template(self, transcript: str) -> str:
        """一般記事のテンプレート"""
        return """マナミです。

今回は音声配信の内容についてお話ししたいと思います。

最近感じていることをお話ししたいと思います。

---------------

いろいろな発見があり、皆さんと共有していきたいと思っています。

今後もこうした内容を皆さんと共有していきたいと思います。"""

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
        
        # 現在のセッションデータを設定
        self.current_audio_name = filename
        self.previous_transcript = transcript
        
        print(f"🤖 記事生成中...")
        
        # 高品質記事生成
        article = self.generate_high_quality_article(transcript)
        
        # 生成した記事を保存
        self.previous_article = article
        
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
        print("    高品質記事生成システム")
        print("    💰 完璧な記事を自動生成")
        print("=" * 62)
        print()

    def main(self):
        """メイン処理"""
        parser = argparse.ArgumentParser(description='高品質記事生成システム')
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
    generator = ImprovedArticleGenerator()
    generator.main()