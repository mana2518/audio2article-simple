#!/usr/bin/env python3
"""
無料Note記事生成システム
ドラッグ&ドロップ → 文字起こし → プロンプト生成 → Claude（無料）で記事作成
"""

import os
from pathlib import Path

def main():
    print("🎙️ 無料Note記事生成システム")
    print("="*50)
    
    # 必要なライブラリをチェック
    try:
        import whisper
        import pyperclip
    except ImportError as e:
        print(f"❌ 必要なライブラリがありません: {e}")
        print("インストール: pip3 install --user --break-system-packages openai-whisper pyperclip")
        return
    
    # 参考文体を読み込み
    reference_text = """マナミです。

今日は、私が最近感じていることについてお話ししたいと思います。

フリーランスとして働いていると、日々色々な発見があります。特に最近は、効率的な働き方について考えることが多くなりました。

子どもたちとの時間も大切にしたいですし、仕事も充実させたい。そのバランスを取るのは簡単ではありませんが、少しずつ自分なりの方法を見つけています。

皆さんも、きっと同じような悩みを抱えているのではないでしょうか。

今後も、こうした日常の気づきや学びを、皆さんと共有していきたいと思っています。"""
    
    reference_file = Path("/Users/manami/(N)note本文.md")
    if reference_file.exists():
        try:
            with open(reference_file, 'r', encoding='utf-8') as f:
                reference_text = f.read()[:3000]
        except:
            pass
    
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
            
            print("🤖 記事を生成しています...")
            print("文字起こし内容をnote記事に整えます。しばらくお待ちください...")
            
            # ここでユーザーが文字起こし内容を手動で記事に変換する
            print("\n" + "="*60)
            print("📝 文字起こし内容:")
            print("="*60)
            print(transcript)
            print("="*60)
            
            print("\n🤖 上記の文字起こし内容を以下の形式でnote記事に整えてください:")
            print("="*60)
            print("#目的")
            print("あなたは優秀なライターです。noteに掲載する記事を作成します。")
            print("")
            print("#最重要")
            print("文体や口調は主に「知識」の中にある「編集済み　note本文」を参考にしてください。なるべく話しているような雰囲気を残してほしいです。")
            print("")
            print("## 知識（編集済み　note本文）")
            print("```")
            print(reference_text)
            print("```")
            print("")
            print("要求: 添付するテキストは、音声配信の内容の文字起こしデータ（日本語）です。全体を通して2500文字程度に収めるように構成してください。以下の構成に従って要約を行ってください。")
            print("")
            print("## 入力データ")
            print("以下は音声配信の文字起こしデータです：")
            print("```")
            print(transcript)
            print("```")
            print("")
            print("1. 導入部（約200文字）:")
            print("   - 音声配信の主題を結論、その重要性を簡潔に紹介します。")
            print("")
            print("2. 主要内容の要約（約2000文字）:")
            print("   - 主要な議論やポイントを、明確かつ簡潔に要約します。")
            print("")
            print("3. 結論（約300文字）:")
            print("")
            print("このプロセスを通じて、リスナーが元の音声配信から得ることができる主要な知見と情報を効果的に伝えることが目的です。各セクションは情報を適切に要約し、読者にとって理解しやすく、かつ情報量が豊富であることを心掛けてください。")
            print("")
            print("その他の制約：")
            print("・最初の自己紹介文「3人の子供達を育てながらSNS発信をしているママフリーランスです」は削除し、「マナミです。」→すぐ本文へ続けてください。")
            print("・「ですます調」にしてください。")
            print("・内容から段落わけ、改行を適切に行ってください")
            print("・強調するところは「」で区切ってください")
            print("・子供は「子ども」と表記してください")
            print("・見出しをつけないでください")
            print("")
            print("それでは記事を作成してください：")
            print("="*60)
            
            print("\n📋 生成された記事を以下に貼り付けてください:")
            article = input("➤ ")
            
            if article.strip():
                # 記事をクリップボードにコピー
                pyperclip.copy(article)
                print("✅ 記事をクリップボードにコピーしました！")
                
                # 記事を表示
                print("\n" + "="*60)
                print("📖 生成された記事:")
                print("="*60)
                print(article)
                print("="*60)
            else:
                print("❌ 記事が入力されませんでした")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    print("👋 お疲れさまでした！")

if __name__ == "__main__":
    main()