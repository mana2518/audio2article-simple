#!/usr/bin/env python3
"""
究極シンプルNote記事生成システム
音声ファイル → 文字起こし → このClaude（無料版）で記事作成
"""

import os
from pathlib import Path

def main():
    print("🎙️ 究極シンプルNote記事生成システム")
    print("="*50)
    
    # 必要なライブラリをチェック
    try:
        import whisper
    except ImportError:
        print("❌ whisperがインストールされていません")
        print("インストール: pip3 install --user --break-system-packages openai-whisper")
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
            model = whisper.load_model("base")
            
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
            
            print("\n🤖 次のステップ:")
            print("1. 上記の文字起こし内容をこのClaude（無料版）に貼り付け")
            print("2. 「この文字起こし内容をnote記事に整えてください」と依頼")
            print("3. 生成された記事をコピーして使用")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    print("👋 お疲れさまでした！")

if __name__ == "__main__":
    main()