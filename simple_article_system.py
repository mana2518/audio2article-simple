#!/usr/bin/env python3
"""
シンプル記事生成システム
音声ファイル → 文字起こし → 記事入力 → クリップボードコピー
"""

import os
from pathlib import Path

def main():
    print("🎙️ シンプル記事生成システム")
    print("="*50)
    
    # 必要なライブラリをチェック
    try:
        import whisper
        import pyperclip
    except ImportError as e:
        print(f"❌ 必要なライブラリがありません: {e}")
        print("インストール: pip install openai-whisper pyperclip")
        return
    
    print("✅ 準備完了")
    
    while True:
        print("\n📁 音声ファイルをドラッグ&ドロップして貼り付けてください (qで終了):")
        audio_input = input("➤ ").strip()
        
        if audio_input.lower() == 'q':
            break
        
        # パスを整理
        audio_input = audio_input.strip('"').strip("'")
        audio_input = audio_input.replace('\\ ', ' ')
        audio_input = os.path.expanduser(audio_input)
        audio_path = Path(audio_input)
        
        if not audio_path.exists():
            print(f"❌ ファイルが見つかりません")
            continue
        
        print(f"🎵 処理中: {audio_path.name}")
        
        try:
            # 文字起こし
            print("📝 文字起こししています...")
            model = whisper.load_model("tiny")  # 高速処理用
            
            import io
            import contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                result = model.transcribe(str(audio_path), language="ja", verbose=False)
            
            transcript = result["text"].strip()
            
            print("✅ 文字起こし完了！")
            print("\n" + "="*60)
            print("📝 文字起こし内容:")
            print("="*60)
            print(transcript)
            print("="*60)
            
            # シンプルな記事入力
            print("\n🖋️ 上記を参考に記事を作成し、下記に貼り付けてください:")
            print("📝 記事を入力してください (複数行の場合は最後に空行でEnter):")
            
            # 複数行入力対応
            article_lines = []
            empty_line_count = 0
            
            while True:
                line = input()
                if line.strip() == "":
                    empty_line_count += 1
                    if empty_line_count >= 2:  # 連続2回空行で終了
                        break
                    article_lines.append("")
                else:
                    empty_line_count = 0
                    article_lines.append(line)
            
            article = "\n".join(article_lines).strip()
            
            if article:
                # 記事をクリップボードにコピー
                pyperclip.copy(article)
                print("\n✅ 記事をクリップボードにコピーしました！")
                
                # 記事を表示
                print("\n" + "="*60)
                print("📖 生成された記事:")
                print("="*60)
                print(article)
                print("="*60)
                print("\n🎉 記事が完成しました！クリップボードから貼り付けできます。")
            else:
                print("❌ 記事が入力されませんでした")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    print("👋 お疲れさまでした！")

if __name__ == "__main__":
    main()