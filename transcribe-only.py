#!/usr/bin/env python3
"""
音声文字起こし専用ツール
音声ファイル → 文字起こしテキスト保存
"""

import os
import sys
import argparse
from pathlib import Path
import whisper
import re
from datetime import datetime
import pyperclip

class AudioTranscriber:
    def __init__(self):
        self.model = None
        self.model_name = "base"  # 高速処理（推奨設定）

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

    def transcribe_audio(self, audio_path: str) -> str:
        """音声文字起こし"""
        try:
            self.load_whisper_model()
            print("🎵 音声を文字起こし中...")
            
            # 最高精度設定で文字起こし
            result = self.model.transcribe(
                audio_path,
                language="ja",
                temperature=0.0,                    # 最も安定した結果
                beam_size=5,                        # ビームサーチで精度向上
                best_of=5,                          # 複数候補から最良を選択
                patience=1.0,                       # より忍耐強く処理
                condition_on_previous_text=True,    # 前の文脈を考慮
                compression_ratio_threshold=2.4,    # 圧縮率閾値を調整
                logprob_threshold=-1.0,             # 対数確率閾値を調整
                no_speech_threshold=0.6,            # 無音部分の閾値を調整
                initial_prompt="マナミです。3人の子どもを育てながらママフリーランスとして働いています。SNS発信やコンテンツ作成を中心にお仕事をしています。以下は日本語の音声配信です。正確に文字起こしをしてください。"  # より具体的なコンテキスト
            )
            transcript = result["text"]
            
            print(f"✅ 文字起こし完了: {len(transcript)}文字")
            return transcript
            
        except Exception as e:
            print(f"❌ 文字起こしエラー: {e}")
            return None

    def copy_to_clipboard(self, text: str):
        """クリップボードにコピー"""
        try:
            pyperclip.copy(text)
            print("📋 文字起こしをクリップボードにコピーしました！")
        except Exception as e:
            print(f"⚠️ クリップボードコピー失敗: {e}")

    def save_transcript(self, transcript: str, audio_path: str) -> str:
        """文字起こし結果を保存"""
        # 保存ファイル名を生成
        audio_name = Path(audio_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        transcript_filename = f"transcript_{audio_name}_{timestamp}.txt"
        transcript_path = Path("/Users/manami/audio_to_article_new") / transcript_filename
        
        try:
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            print(f"📝 文字起こし保存完了: {transcript_filename}")
            return str(transcript_path)
            
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            return None

    def process_audio(self, audio_path: str):
        """音声処理メイン"""
        print(f"🔍 処理開始: {Path(audio_path).name}")
        
        # ファイル存在確認
        if not os.path.exists(audio_path):
            print(f"❌ ファイルが見つかりません: {audio_path}")
            return None
        
        # 文字起こし
        transcript = self.transcribe_audio(audio_path)
        if not transcript:
            return None
        
        # クリップボードにコピー
        self.copy_to_clipboard(transcript)
        
        # 保存
        saved_path = self.save_transcript(transcript, audio_path)
        if saved_path:
            print(f"\n✅ 処理完了")
            print(f"📄 保存場所: {saved_path}")
            print("\n次のステップ:")
            print(f"./generate \"{saved_path}\"")
        
        return saved_path

def main():
    parser = argparse.ArgumentParser(description='音声文字起こし専用ツール')
    parser.add_argument('audio_file', nargs='?', help='音声ファイルのパス')
    parser.add_argument('--model', choices=['tiny', 'base', 'small', 'medium', 'large'], 
                      default='base', help='Whisperモデルを指定 (デフォルト: 高速base)')
    
    args = parser.parse_args()
    
    transcriber = AudioTranscriber()
    if args.model:
        transcriber.model_name = args.model
    
    print("🎙️" + "=" * 50)
    print("   音声文字起こし専用ツール")
    print("   Step 1: 音声 → 文字起こし（最高精度版）")
    print("=" * 52)
    print(f"📊 使用モデル: {transcriber.model_name} 🚀 高速処理")
    print("🚀 従量課金なし・ローカル処理")
    print("💡 モデル比較:")
    print("   tiny   : 最高速（精度低）")
    print("   base   : 🚀 高速（標準精度）← デフォルト") 
    print("   small  : 高精度（やや時間がかかる）")
    print("   medium : ⚖️ 精度と速度のバランス")
    print("   large  : 最高精度（時間がかかるが最高品質）")
    print()
    print("⚠️  初回は大容量モデルのダウンロードに時間がかかります")
    
    # コマンドライン引数で音声ファイルが指定されている場合
    if args.audio_file:
        # 同じパス処理ロジックを適用
        audio_path = args.audio_file.strip().strip('\n\r\t ')
        
        # クオート文字を削除
        quote_chars = ['"', "'", '`']
        for quote in quote_chars:
            if audio_path.startswith(quote) and audio_path.endswith(quote) and len(audio_path) > 1:
                audio_path = audio_path[1:-1]
                break
        
        # エスケープ文字処理（簡略版）
        escape_mappings = {
            '\\ ': ' ', '\\&': '&', '\\(': '(', '\\)': ')', '\\[': '[', '\\]': ']',
            '\\{': '{', '\\}': '}', '\\"': '"', "\\'": "'", '\\\\': '\\'
        }
        for escaped, unescaped in escape_mappings.items():
            audio_path = audio_path.replace(escaped, unescaped)
        
        if audio_path.startswith('file://'):
            audio_path = audio_path[7:]
            
        audio_path = os.path.expanduser(audio_path)
        audio_path = os.path.abspath(audio_path)
        
        print(f"🔍 解析されたパス: {audio_path}")
        
        if os.path.exists(audio_path):
            transcriber.process_audio(audio_path)
        else:
            print(f"❌ ファイルが見つかりません: {audio_path}")
        return
    
    # インタラクティブモード
    while True:
        print("🎯 音声ファイルをドラッグ&ドロップするか、パスを入力してください")
        print("   📁 対応形式: mp3, wav, m4a, aac, flac, ogg, wma, mp4, mov等")
        print("   📋 ドラッグ&ドロップ: Finderから直接ファイルをドラッグしてください")
        print("   ⌨️  手入力: ファイルパスを直接入力")
        print("   🚪 終了: 'q' を入力")
        audio_input = input("\n🎙️ ファイル: ").strip()
        
        if audio_input.lower() in ['q', 'quit', 'exit']:
            break
        
        if not audio_input:
            continue
        
        # パスの整理（強化されたドラッグ&ドロップ対応）
        audio_path = audio_input.strip()
        
        # 先頭末尾の空白や改行を除去
        audio_path = audio_path.strip('\n\r\t ')
        
        # クオート文字を削除（シングル・ダブル・バッククオート対応）
        quote_chars = ['"', "'", '`']
        for quote in quote_chars:
            if audio_path.startswith(quote) and audio_path.endswith(quote) and len(audio_path) > 1:
                audio_path = audio_path[1:-1]
                break
        
        # macOSドラッグ&ドロップ特有のエスケープ文字を処理
        escape_mappings = {
            '\\ ': ' ',           # エスケープされたスペース
            '\\&': '&',           # アンパサンド
            '\\(': '(',           # 左括弧
            '\\)': ')',           # 右括弧
            '\\[': '[',           # 左角括弧
            '\\]': ']',           # 右角括弧
            '\\{': '{',           # 左波括弧
            '\\}': '}',           # 右波括弧
            '\\"': '"',           # エスケープされたダブルクオート
            "\\'": "'",           # エスケープされたシングルクオート
            '\\!': '!',           # 感嘆符
            '\\#': '#',           # ハッシュ
            '\\$': '$',           # ドル記号
            '\\%': '%',           # パーセント
            '\\;': ';',           # セミコロン
            '\\<': '<',           # 小なり
            '\\>': '>',           # 大なり
            '\\?': '?',           # クエスチョン
            '\\@': '@',           # アットマーク
            '\\^': '^',           # ハット
            '\\`': '`',           # バッククオート
            '\\|': '|',           # パイプ
            '\\~': '~',           # チルダ
            '\\\\': '\\',         # バックスラッシュ
        }
        
        for escaped, unescaped in escape_mappings.items():
            audio_path = audio_path.replace(escaped, unescaped)
        
        # ファイルプロトコルを除去（file://で始まる場合）
        if audio_path.startswith('file://'):
            audio_path = audio_path[7:]
        
        # チルダ展開
        audio_path = os.path.expanduser(audio_path)
        
        # 絶対パスに変換
        audio_path = os.path.abspath(audio_path)
        
        print(f"🔍 解析されたパス: {audio_path}")
        
        # ファイル存在確認
        if not os.path.exists(audio_path):
            print("❌ ファイルが見つかりません")
            print(f"   パス: {audio_path}")
            continue
        
        # 音声ファイル形式確認
        audio_extensions = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.wma', '.mp4', '.mov', '.avi', '.mkv']
        file_extension = os.path.splitext(audio_path.lower())[1]
        
        if file_extension not in audio_extensions:
            print(f"⚠️ 音声ファイルではない可能性があります: {file_extension}")
            print("   対応形式: mp3, wav, m4a, aac, flac, ogg, wma, mp4, mov, avi, mkv")
            confirm = input("   それでも処理しますか？ (y/N): ").lower().strip()
            if confirm not in ['y', 'yes']:
                continue
        
        # ファイルサイズ確認
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            print("❌ ファイルサイズが0バイトです")
            continue
        elif file_size > 500 * 1024 * 1024:  # 500MB
            print(f"⚠️ 大きなファイルです: {file_size / (1024*1024):.1f}MB")
            print("   処理に時間がかかる可能性があります")
        
        print(f"✅ ファイル確認完了: {file_size / (1024*1024):.1f}MB")
        transcriber.process_audio(audio_path)
        
        # 次の処理を確認
        print("\n" + "=" * 50)
        next_action = input("🔄 別の音声ファイルを処理しますか？ (y/N): ").lower().strip()
        if next_action not in ['y', 'yes']:
            break
    
    print("👋 お疲れさまでした！")

if __name__ == "__main__":
    main()