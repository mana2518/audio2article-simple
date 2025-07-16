#!/usr/bin/env python3
"""
ターミナル用音声から記事化ツール (シンプル版)
GUI無しでクリップボードコピー対応
"""

import sys
import os
import argparse
import tempfile
import subprocess
from pathlib import Path
import google.generativeai as genai
from google.cloud import speech
import MeCab
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

class AudioToArticleCLI:
    def __init__(self):
        # Google Gemini設定
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_model = None
            
        # Google Cloud Speech-to-Text設定
        self.speech_client = None
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            try:
                self.speech_client = speech.SpeechClient()
            except Exception as e:
                print(f"Speech-to-Text初期化エラー: {e}")
                
        # MeCab設定
        try:
            self.mecab_tagger = MeCab.Tagger()
        except Exception:
            self.mecab_tagger = None
            
        # 文体学習用ファイルパス
        self.style_file_path = "/Users/manami/(N)note本文.md"
        
        # 文体サンプルを読み込み
        self.style_text = self.load_style_sample()
        
        # 学習済み文体特徴
        self.style_features = self.analyze_style_features()

    def print_banner(self):
        """バナー表示"""
        print("🎙️" + "="*50)
        print("    音声から記事化ツール (ターミナル版)")
        print("    📚 文体学習機能搭載")
        print("="*52)
        
        # 文体学習状況を表示
        if self.style_features.get("loaded_from_file", False):
            print("✅ 文体学習済み: note本文.mdから文体を学習")
        else:
            print("⚠️ デフォルト文体を使用")
        print()

    def convert_audio_format(self, input_path: str, output_path: str) -> bool:
        """音声ファイルをWAVに変換"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path, '-acodec', 'pcm_s16le', 
                '-ar', '16000', '-ac', '1', output_path, '-y'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ 音声変換エラー: {e}")
            return False

    def transcribe_with_gemini(self, audio_path: str) -> str:
        """Gemini APIを使用した音声文字起こし"""
        try:
            if not self.gemini_model:
                return None
            
            print("🤖 Gemini APIで文字起こし中...")
            with open(audio_path, "rb") as audio_file:
                audio_file_obj = genai.upload_file(audio_file, mime_type="audio/wav")
            
            prompt = "この音声ファイルの内容を日本語で文字起こししてください。正確に、自然な文章として出力してください。"
            response = self.gemini_model.generate_content([audio_file_obj, prompt])
            
            # ファイルを即座に削除
            genai.delete_file(audio_file_obj.name)
            return response.text
        except Exception as e:
            print(f"❌ Gemini文字起こしエラー: {e}")
            return None

    def transcribe_with_speech_api(self, audio_path: str) -> str:
        """Google Cloud Speech-to-Text API"""
        try:
            if not self.speech_client:
                return None
                
            print("🗣️ Google Cloud Speech-to-Textで文字起こし中...")
            with open(audio_path, "rb") as audio_file:
                content = audio_file.read()
            
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="ja-JP",
            )
            response = self.speech_client.recognize(config=config, audio=audio)
            return " ".join([result.alternatives[0].transcript for result in response.results])
        except Exception as e:
            print(f"❌ Speech-to-Text エラー: {e}")
            return None

    def load_style_sample(self) -> str:
        """文体サンプルファイルを読み込み"""
        try:
            if os.path.exists(self.style_file_path):
                with open(self.style_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 最初の3つの記事を抽出（文体学習用）
                    lines = content.split('\n')
                    sample_lines = []
                    article_count = 0
                    
                    for line in lines:
                        if line.strip() and not line.startswith('(') and not line.startswith('2025/'):
                            sample_lines.append(line)
                            if len(sample_lines) >= 50:  # 50行程度のサンプル
                                break
                    
                    return '\n'.join(sample_lines)
            else:
                # フォールバック用デフォルト文体
                return """マナミです。

今回は「SNS運用で疲れた時の対処法」についてお話しします。

SNSを始めたばかりの頃は、毎日投稿することや「いいね」の数を気にしてしまいがちです。でも、そんな風に頑張りすぎていると、だんだん疲れてきてしまうんですよね。

私も最初の頃は、毎日何かを投稿しなければいけないと思っていました。でも、それってすごく大変なことなんです。毎日ネタを考えて、写真を撮って、文章を書いて...。気がつくと、SNSのことばかり考えている自分がいました。

そんな時に大切なのは「無理をしないこと」です。投稿の頻度を下げても大丈夫ですし、たまには休んでも構いません。フォロワーの方々は、あなたが無理をしていることよりも、自然体でいることを望んでいるはずです。"""
        except Exception as e:
            print(f"❌ 文体ファイル読み込みエラー: {e}")
            return """マナミです。

今回は「SNS運用で疲れた時の対処法」についてお話しします。

SNSを始めたばかりの頃は、毎日投稿することや「いいね」の数を気にしてしまいがちです。でも、そんな風に頑張りすぎていると、だんだん疲れてきてしまうんですよね。"""

    def analyze_style_features(self) -> dict:
        """文体特徴を詳細分析"""
        if not self.gemini_model:
            return {}
        
        try:
            analysis_prompt = f"""以下の文章の文体特徴を詳細に分析してください。

【分析対象】
{self.style_text}

【分析項目】
1. 文体の基本的な特徴（ですます調、だである調など）
2. 頻出する表現パターン
3. 感情表現の特徴
4. 接続詞の使い方
5. 改行や段落分けの特徴
6. 話し言葉的な表現
7. 強調表現の特徴
8. 文章の構成パターン

分析結果をJSON形式で返してください。"""
            
            response = self.gemini_model.generate_content(analysis_prompt)
            # 簡易的な特徴抽出（実際のJSONパースは省略）
            return {
                "analysis": response.text,
                "loaded_from_file": os.path.exists(self.style_file_path)
            }
        except Exception as e:
            print(f"❌ 文体分析エラー: {e}")
            return {}

    def analyze_style_with_mecab(self, text: str) -> str:
        """MeCabと学習済み特徴による文体分析"""
        if not self.mecab_tagger:
            return "・文体は「ですます調」を基本とします。"
        
        try:
            node = self.mecab_tagger.parseToNode(text)
            endings = {}
            
            while node:
                if node.feature.startswith("助動詞") and node.surface in ["です", "ます"]:
                    prev_node = node.prev
                    if prev_node and prev_node.feature.startswith("動詞"):
                        ending = f"{prev_node.surface}{node.surface}"
                        endings[ending] = endings.get(ending, 0) + 1
                node = node.next
            
            # 学習済み特徴を活用した指示
            style_instruction = "・文体は「ですます調」を基本とします。\n"
            
            if self.style_features.get("loaded_from_file", False):
                style_instruction += "・読み込んだnote記事の文体を参考にしてください。\n"
                style_instruction += "・話し言葉的な表現（「〜なんですよね」「〜だと思うんです」など）を適度に使用してください。\n"
                style_instruction += "・「」で強調表現を使用してください。\n"
                style_instruction += "・体験談や具体例を交えた親しみやすい文体にしてください。\n"
                style_instruction += "・改行を適切に使用して読みやすくしてください。\n"
            
            if not endings:
                return style_instruction
            
            sorted_endings = sorted(endings.items(), key=lambda x: x[1], reverse=True)
            top_endings = [e[0] for e in sorted_endings[:3]]
            
            return f"{style_instruction}・特に「{'」「'.join(top_endings)}」などの丁寧な表現を参考にしてください。"
        except Exception as e:
            print(f"❌ MeCab解析エラー: {e}")
            return "・文体は「ですます調」を基本とします。"

    def generate_article(self, transcript: str) -> str:
        """記事生成"""
        if not self.gemini_model:
            raise Exception("Gemini APIキーが設定されていません")
        
        print("✍️ AI記事生成中...")
        style_prompt = self.analyze_style_with_mecab(self.style_text)
        
        # 学習済み文体とユーザー指定プロンプトを統合
        base_prompt = f"""# 目的
あなたは優秀なライターです。noteに掲載する記事を作成します。

# 最重要
文体や口調は主に「知識」の中にある「編集済み　note本文」を参考にしてください。なるべく話しているような雰囲気を残してほしいです。

【文体学習済みサンプル】
{self.style_text[:1000]}...

【AI分析による文体特徴】
{self.style_features.get('analysis', '文体分析結果がありません')[:500]}...

# 要求仕様
添付するテキストは、音声配信の内容の文字起こしデータ（日本語）です。全体を通して2500文字程度に収めるように構成してください。以下の構成に従って要約を行ってください。

1. 導入部（約200文字）:
   - 音声配信の主題を結論、その重要性を簡潔に紹介します。

2. 主要内容の要約（約2000文字）:
   - 主要な議論やポイントを、明確かつ簡潔に要約します。

3. 結論（約300文字）:

このプロセスを通じて、リスナーが元の音声配信から得ることができる主要な知見と情報を効果的に伝えることが目的です。各セクションは情報を適切に要約し、読者にとって理解しやすく、かつ情報量が豊富であることを心掛けてください。

# その他の制約
・最初の自己紹介文「3人の子供達を育てながらSNS発信をしているママフリーランスです」は削除し、「マナミです。」→すぐ本文へ続けてください。
・「ですます調」にしてください。
・内容から段落わけ、改行を適切に行ってください
・強調するところは「」で区切ってください
・子供は「子ども」と表記してください
・見出しをつけないでください"""
        
        final_prompt = f"{base_prompt}\n\n# 文体指示\n{style_prompt}\n\n# 文字起こしテキスト\n{transcript}"
        
        response = self.gemini_model.generate_content(final_prompt)
        return response.text

    def copy_to_clipboard(self, text: str) -> bool:
        """クリップボードにコピー"""
        try:
            # pyperclipを試す
            import pyperclip
            pyperclip.copy(text)
            return True
        except ImportError:
            pass
        
        try:
            # macOS
            subprocess.run(['pbcopy'], input=text.encode(), check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        try:
            # Linux (xclip)
            subprocess.run(['xclip', '-selection', 'clipboard'], 
                         input=text.encode(), check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        try:
            # Linux (xsel)
            subprocess.run(['xsel', '--clipboard', '--input'], 
                         input=text.encode(), check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return False

    def display_result(self, article: str, filename: str):
        """結果を表示"""
        print("\n" + "="*60)
        print("✨ 記事生成完了！")
        print("="*60)
        print(f"📁 元ファイル: {filename}")
        print(f"📝 文字数: {len(article)}文字")
        print("="*60)
        print()
        print(article)
        print()
        print("="*60)
        
        # クリップボードにコピー
        if self.copy_to_clipboard(article):
            print("📋 記事がクリップボードにコピーされました！")
        else:
            print("⚠️ クリップボードコピーに失敗しました")
        
        # ファイル保存のオプション
        save_option = input("\n💾 ファイルに保存しますか？ (y/N): ").lower().strip()
        if save_option in ['y', 'yes']:
            try:
                safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                output_path = f"{safe_filename}_article.md"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(article)
                print(f"✅ ファイルが {output_path} に保存されました！")
            except Exception as e:
                print(f"❌ 保存に失敗しました: {e}")

    def process_audio_file(self, audio_path: str):
        """音声ファイルの処理メイン"""
        try:
            filename = Path(audio_path).name
            print(f"🎵 処理開始: {filename}")
            
            # 音声ファイル変換
            wav_path = None
            file_ext = Path(audio_path).suffix.lower()
            
            if file_ext != '.wav':
                print("🔄 音声ファイルを変換中...")
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    wav_path = temp_wav.name
                
                if not self.convert_audio_format(audio_path, wav_path):
                    wav_path = audio_path
            else:
                wav_path = audio_path
            
            # 文字起こし
            print("📝 文字起こし中...")
            transcript = self.transcribe_with_gemini(wav_path)
            
            if not transcript and self.speech_client:
                transcript = self.transcribe_with_speech_api(wav_path)
            
            if not transcript:
                raise Exception("音声の文字起こしに失敗しました。音声ファイルを確認してください。")
            
            # 記事生成
            article = self.generate_article(transcript)
            
            # 結果表示
            self.display_result(article, filename)
            
        except Exception as e:
            print(f"❌ 処理中にエラーが発生しました: {e}")
        finally:
            # 一時ファイルの完全削除
            try:
                if wav_path and wav_path != audio_path and os.path.exists(wav_path):
                    os.remove(wav_path)
            except Exception as e:
                print(f"⚠️ 一時ファイル削除エラー: {e}")
            
            # メモリ上のデータをクリア
            transcript = None
            wav_path = None

def main():
    cli = AudioToArticleCLI()
    cli.print_banner()
    
    parser = argparse.ArgumentParser(description="音声ファイルから記事を生成")
    parser.add_argument("audio_file", nargs="?", help="音声ファイルのパス")
    
    args = parser.parse_args()
    
    if args.audio_file:
        # コマンドライン引数から
        if not os.path.exists(args.audio_file):
            print("❌ ファイルが見つかりません:", args.audio_file)
            return
        
        cli.process_audio_file(args.audio_file)
    else:
        # インタラクティブモード
        print("💡 使用方法:")
        print("   1. ターミナルにファイルをドラッグ&ドロップ")
        print("   2. またはコマンド: python terminal_simple.py [音声ファイルパス]")
        print()
        
        while True:
            try:
                file_path = input("🎙️ 音声ファイルのパスを入力 (または 'q' で終了): ").strip()
                
                if file_path.lower() == 'q':
                    break
                
                # ドラッグ&ドロップ時の引用符を削除
                file_path = file_path.strip('"').strip("'")
                
                if not os.path.exists(file_path):
                    print("❌ ファイルが見つかりません")
                    continue
                
                cli.process_audio_file(file_path)
                
                # 続行確認
                continue_option = input("\n🔄 別のファイルを処理しますか？ (y/N): ").lower().strip()
                if continue_option not in ['y', 'yes']:
                    break
                
            except KeyboardInterrupt:
                print("\n👋 終了します")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()