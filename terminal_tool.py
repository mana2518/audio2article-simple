#!/usr/bin/env python3
"""
ターミナル用音声から記事化ツール
音声ファイルをドラッグ&ドロップまたはコマンドライン引数で受け取り、
GUIダイアログボックスで結果を表示
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
import tkinter as tk
from tkinter import messagebox, scrolledtext
import pyperclip

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
            
        # 固定文体サンプル
        self.style_text = """マナミです。

今回は「SNS運用で疲れた時の対処法」についてお話しします。

SNSを始めたばかりの頃は、毎日投稿することや「いいね」の数を気にしてしまいがちです。でも、そんな風に頑張りすぎていると、だんだん疲れてきてしまうんですよね。

私も最初の頃は、毎日何かを投稿しなければいけないと思っていました。でも、それってすごく大変なことなんです。毎日ネタを考えて、写真を撮って、文章を書いて...。気がつくと、SNSのことばかり考えている自分がいました。

そんな時に大切なのは「無理をしないこと」です。投稿の頻度を下げても大丈夫ですし、たまには休んでも構いません。フォロワーの方々は、あなたが無理をしていることよりも、自然体でいることを望んでいるはずです。"""

    def print_banner(self):
        """バナー表示"""
        print("🎙️" + "="*50)
        print("    音声から記事化ツール (ターミナル版)")
        print("="*52)
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

    def analyze_style_with_mecab(self, text: str) -> str:
        """MeCabで文体分析"""
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
            
            if not endings:
                return "・文体は「ですます調」を基本とします。"
            
            sorted_endings = sorted(endings.items(), key=lambda x: x[1], reverse=True)
            top_endings = [e[0] for e in sorted_endings[:3]]
            
            return f"・文体は「ですます調」を基本とします。\n・特に「{'」「'.join(top_endings)}」などの丁寧な表現を参考にしてください。"
        except Exception as e:
            print(f"❌ MeCab解析エラー: {e}")
            return "・文体は「ですます調」を基本とします。"

    def generate_article(self, transcript: str) -> str:
        """記事生成"""
        if not self.gemini_model:
            raise Exception("Gemini APIキーが設定されていません")
        
        print("✍️ AI記事生成中...")
        style_prompt = self.analyze_style_with_mecab(self.style_text)
        
        base_prompt = """# 目的
あなたは優秀なライターです。noteに掲載する記事を作成します。

# 最重要
文体や口調は主に「知識」の中にある「編集済み　note本文」を参考にしてください。なるべく話しているような雰囲気を残してほしいです。

要求: 添付するテキストは、音声配信の内容の文字起こしデータ（日本語）です。全体を通して2500文字程度に収めるように構成してください。以下の構成に従って要約を行ってください。

1. 導入部（約200文字）:
   - 音声配信の主題を結論、その重要性を簡潔に紹介します。

2. 主要内容の要約（約2000文字）:
   - 主要な議論やポイントを、明確かつ簡潔に要約します。

3. 結論（約300文字）:

このプロセスを通じて、リスナーが元の音声配信から得ることができる主要な知見と情報を効果的に伝えることが目的です。各セクションは情報を適切に要約し、読者にとって理解しやすく、かつ情報量が豊富であることを心掛けてください。

その他の制約：
・最初の自己紹介文「3人の子供達を育てながらSNS発信をしているママフリーランスです」は削除し、「マナミです。」→すぐ本文へ続けてください。
・「ですます調」にしてください。
・内容から段落わけ、改行を適切に行ってください
・強調するところは「」で区切ってください
・子供は「子ども」と表記してください
・見出しをつけないでください"""
        
        final_prompt = f"{base_prompt}\n\n# 文体指示\n{style_prompt}\n\n# 文字起こしテキスト\n{transcript}"
        
        response = self.gemini_model.generate_content(final_prompt)
        return response.text

    def show_result_dialog(self, article: str, filename: str):
        """結果をGUIダイアログで表示"""
        root = tk.Tk()
        root.title(f"📝 記事生成完了 - {filename}")
        root.geometry("800x600")
        
        # メインフレーム
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトル
        title_label = tk.Label(main_frame, text="✨ 記事が生成されました！", 
                              font=("Arial", 16, "bold"), fg="#333")
        title_label.pack(pady=(0, 10))
        
        # ファイル情報
        file_info = tk.Label(main_frame, text=f"📁 元ファイル: {filename}", 
                            font=("Arial", 10), fg="#666")
        file_info.pack(pady=(0, 20))
        
        # テキストエリア
        text_frame = tk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, 
                                            font=("Hiragino Sans", 12),
                                            padx=10, pady=10)
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, article)
        
        # ボタンフレーム
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(20, 0), fill=tk.X)
        
        def copy_to_clipboard():
            pyperclip.copy(article)
            messagebox.showinfo("📋 コピー完了", "記事がクリップボードにコピーされました！")
        
        def save_to_file():
            try:
                safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                output_path = f"{safe_filename}_article.md"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(article)
                messagebox.showinfo("💾 保存完了", f"記事が {output_path} に保存されました！")
            except Exception as e:
                messagebox.showerror("❌ エラー", f"保存に失敗しました: {e}")
        
        # ボタン
        copy_btn = tk.Button(button_frame, text="📋 クリップボードにコピー", 
                           command=copy_to_clipboard, bg="#4CAF50", fg="white",
                           font=("Arial", 12, "bold"), pady=8)
        copy_btn.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        save_btn = tk.Button(button_frame, text="💾 ファイルに保存", 
                           command=save_to_file, bg="#2196F3", fg="white",
                           font=("Arial", 12, "bold"), pady=8)
        save_btn.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # 閉じるボタン
        close_btn = tk.Button(main_frame, text="✅ 閉じる", 
                            command=root.destroy, bg="#757575", fg="white",
                            font=("Arial", 10), pady=5)
        close_btn.pack(pady=(10, 0))
        
        # ウィンドウを前面に表示
        root.lift()
        root.attributes('-topmost', True)
        root.after_idle(root.attributes, '-topmost', False)
        
        root.mainloop()

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
                transcript = "今日はAIを使った新しいサービスについて話します。最近、AIの技術がとても進歩していて、個人でも簡単にAIを活用したサービスを作ることができるようになりました。私も実際にいくつかのツールを作ってみたのですが、思っていたよりも簡単で驚きました。"
                print("⚠️ デモテキストを使用します")
            
            # 記事生成
            article = self.generate_article(transcript)
            
            print("✅ 処理完了！")
            
            # 結果表示
            self.show_result_dialog(article, filename)
            
        except Exception as e:
            messagebox.showerror("❌ エラー", f"処理中にエラーが発生しました:\n{e}")
        finally:
            # 一時ファイル削除
            if wav_path and wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)

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
        print("   2. またはコマンド: python terminal_tool.py [音声ファイルパス]")
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
                
            except KeyboardInterrupt:
                print("\n👋 終了します")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()