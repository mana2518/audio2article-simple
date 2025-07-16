#!/usr/bin/env python3
"""
自動Note記事生成システム
音声ファイル → 文字起こし → 自動でClaude（無料版）に送信 → 記事生成
"""

import os
import sys
from pathlib import Path
import json
import time

def generate_article_with_claude(transcript, reference_text):
    """文字起こし内容をnote記事に整える"""
    
    # ここで実際のClaude（無料版）の処理をシミュレート
    # 実際の実装では、このClaude（無料版）のAPIを使用
    
    # 以下の形式でnote記事を生成
    prompt = f"""#目的
あなたは優秀なライターです。noteに掲載する記事を作成します。

#最重要
文体や口調は主に「知識」の中にある「編集済み　note本文」を参考にしてください。なるべく話しているような雰囲気を残してほしいです。

## 知識（編集済み　note本文）
```
{reference_text}
```

要求: 添付するテキストは、音声配信の内容の文字起こしデータ（日本語）です。全体を通して2500文字程度に収めるように構成してください。以下の構成に従って要約を行ってください。

## 入力データ
以下は音声配信の文字起こしデータです：
```
{transcript}
```

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
・見出しをつけないでください

それでは記事を作成してください："""
    
    # 実際の実装では、このClaude（無料版）にプロンプトを送信して記事を生成
    # 現在はプロンプトを返すだけ
    return prompt

def main():
    print("🎙️ 自動Note記事生成システム")
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
            print("✅ 文字起こし完了")
            
            # 自動で記事生成プロンプトを作成
            print("🤖 記事生成プロンプトを作成しています...")
            prompt = generate_article_with_claude(transcript, reference_text)
            
            # プロンプトをクリップボードにコピー
            pyperclip.copy(prompt)
            print("📋 記事生成プロンプトをクリップボードにコピーしました！")
            
            print("\n" + "="*60)
            print("🤖 次のステップ（自動化済み）:")
            print("1. ✅ 音声ファイルの処理完了")
            print("2. ✅ 文字起こし完了")
            print("3. ✅ 記事生成プロンプトを作成")
            print("4. ✅ プロンプトをクリップボードにコピー")
            print("5. 🔄 このClaude（無料版）にプロンプトを貼り付けてください")
            print("="*60)
            
            print("\n💡 このClaude（無料版）に上記のプロンプトを貼り付けると、")
            print("   自動で記事が生成されます！")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    print("👋 お疲れさまでした！")

if __name__ == "__main__":
    main()