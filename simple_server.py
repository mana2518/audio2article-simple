#!/usr/bin/env python3
"""
シンプルな音声から記事化ツール
依存関係を最小限にした版
"""

import http.server
import socketserver
import json
import os
import uuid
import cgi
import html
from urllib.parse import urlparse, parse_qs

# 固定文体サンプル
FIXED_STYLE_TEXT = """マナミです。

今回は「SNS運用で疲れた時の対処法」についてお話しします。

SNSを始めたばかりの頃は、毎日投稿することや「いいね」の数を気にしてしまいがちです。でも、そんな風に頑張りすぎていると、だんだん疲れてきてしまうんですよね。

私も最初の頃は、毎日何かを投稿しなければいけないと思っていました。でも、それってすごく大変なことなんです。毎日ネタを考えて、写真を撮って、文章を書いて...。気がつくと、SNSのことばかり考えている自分がいました。

そんな時に大切なのは「無理をしないこと」です。投稿の頻度を下げても大丈夫ですし、たまには休んでも構いません。フォロワーの方々は、あなたが無理をしていることよりも、自然体でいることを望んでいるはずです。

具体的な対処法をいくつかご紹介しますね。

まず、投稿スケジュールを見直すことです。毎日投稿していた方は、週に3回程度に減らしてみてください。その分、一つ一つの投稿により時間をかけることができます。

次に、完璧主義をやめることです。写真が少し暗くても、文章が短くても、それで十分です。大切なのは、あなたの気持ちが伝わることなんです。

最後に、SNSから離れる時間を作ることです。スマートフォンを見ない時間を意識的に作って、リアルな生活を楽しんでください。

SNS運用で疲れた時は、一度立ち止まって考えてみてください。何のためにSNSを始めたのか、本当に楽しめているのか。答えが見つからない時は、思い切って休むことも大切です。

あなたのペースで、あなたらしく続けていくことが一番大切ですから。"""

# ジョブ管理
jobs = {}

def generate_article_from_text(transcript):
    """文字起こしテキストから記事を生成（デモ版）"""
    try:
        # Gemini APIが使える場合の処理をここに書く
        # 今はデモ用の固定レスポンス
        
        demo_article = f"""マナミです。

今回は「{transcript[:50]}...」について詳しくお話ししたいと思います。

## はじめに

音声配信でお話しした内容を、改めて文章でまとめてみました。このテーマについては、多くの方からご質問をいただいていたので、詳しく解説していこうと思います。

## 主な内容

{transcript}

この内容について、さらに詳しく見ていきましょう。

まず重要なのは、一つ一つのステップを丁寧に進めていくことです。急がず、自分のペースで取り組むことが大切です。

また、失敗を恐れずにチャレンジすることも大切です。最初はうまくいかないこともあるかもしれませんが、続けていくうちに必ず上達していきます。

## まとめ

今日お話しした内容が、皆さんのお役に立てれば嬉しいです。

何か質問がありましたら、いつでもコメントで教えてくださいね。次回は、この話の続きについてお話しする予定です。

最後まで読んでいただき、ありがとうございました。"""
        
        return demo_article
        
    except Exception as e:
        return f"記事生成中にエラーが発生しました: {str(e)}"

class AudioToArticleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_html()
        elif parsed_path.path.startswith('/status/'):
            job_id = parsed_path.path.split('/')[-1]
            self.serve_status(job_id)
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/generate-article/':
            self.handle_upload()
        else:
            self.send_error(404)
    
    def serve_html(self):
        html_content = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>音声から記事化ツール（デモ版）</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .upload-area { border: 2px dashed #ccc; padding: 30px; text-align: center; border-radius: 10px; margin: 20px 0; }
        .upload-area:hover { border-color: #007acc; background: #f8f9ff; }
        input[type="file"] { margin: 10px 0; }
        button { background: #007acc; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #005a99; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .status { padding: 15px; margin: 20px 0; border-radius: 5px; display: none; }
        .status.show { display: block; }
        .status.info { background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }
        .status.success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .status.error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .result { margin-top: 20px; display: none; }
        .result.show { display: block; }
        textarea { width: 100%; height: 300px; border: 1px solid #ddd; border-radius: 5px; padding: 10px; font-family: monospace; }
        .copy-btn { background: #28a745; margin-top: 10px; }
        .copy-btn:hover { background: #218838; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ 音声から記事化ツール（デモ版）</h1>
        <p style="text-align: center; color: #666;">音声ファイルをアップロードして記事を自動生成します</p>
        
        <form id="upload-form">
            <div class="upload-area">
                <h3>📁 音声ファイルをアップロード</h3>
                <input type="file" id="audio-file" accept="audio/*" required>
                <br><br>
                <button type="submit" id="submit-btn">✨ 記事を生成する</button>
            </div>
        </form>
        
        <div id="status" class="status">
            <p id="status-text"></p>
        </div>
        
        <div id="result" class="result">
            <h3>📝 生成された記事</h3>
            <textarea id="article-text" readonly></textarea>
            <br>
            <button class="copy-btn" onclick="copyToClipboard()">📋 コピー</button>
        </div>
    </div>
    
    <script>
        let pollingInterval;
        
        document.getElementById('upload-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const fileInput = document.getElementById('audio-file');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('ファイルを選択してください');
                return;
            }
            
            const formData = new FormData();
            formData.append('audio_file', file);
            
            showStatus('アップロード中...', 'info');
            document.getElementById('submit-btn').disabled = true;
            document.getElementById('result').classList.remove('show');
            
            try {
                const response = await fetch('/generate-article/', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    pollStatus(result.job_id);
                } else {
                    showStatus('エラー: ' + result.error, 'error');
                    document.getElementById('submit-btn').disabled = false;
                }
            } catch (error) {
                showStatus('エラー: ' + error.message, 'error');
                document.getElementById('submit-btn').disabled = false;
            }
        });
        
        function pollStatus(jobId) {
            pollingInterval = setInterval(async () => {
                try {
                    const response = await fetch('/status/' + jobId);
                    const data = await response.json();
                    
                    showStatus(data.message, 'info');
                    
                    if (data.status === 'completed') {
                        clearInterval(pollingInterval);
                        document.getElementById('article-text').value = data.article;
                        document.getElementById('result').classList.add('show');
                        showStatus('記事生成完了！', 'success');
                        document.getElementById('submit-btn').disabled = false;
                    } else if (data.status === 'failed') {
                        clearInterval(pollingInterval);
                        showStatus('エラー: ' + data.error, 'error');
                        document.getElementById('submit-btn').disabled = false;
                    }
                } catch (error) {
                    clearInterval(pollingInterval);
                    showStatus('ポーリングエラー: ' + error.message, 'error');
                    document.getElementById('submit-btn').disabled = false;
                }
            }, 2000);
        }
        
        function showStatus(message, type) {
            const status = document.getElementById('status');
            const statusText = document.getElementById('status-text');
            statusText.textContent = message;
            status.className = 'status show ' + type;
        }
        
        function copyToClipboard() {
            const textarea = document.getElementById('article-text');
            textarea.select();
            document.execCommand('copy');
            alert('コピーしました！');
        }
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def handle_upload(self):
        try:
            # ファイルアップロード処理（簡略化）
            job_id = str(uuid.uuid4())
            
            # デモ用の文字起こしテキスト
            demo_transcript = "今日はAIを使った新しいサービスについて話します。最近、AIの技術がとても進歩していて、個人でも簡単にAIを活用したサービスを作ることができるようになりました。私も実際にいくつかのツールを作ってみたのですが、思っていたよりも簡単で驚きました。特に、音声認識や自然言語処理の技術は、以前と比べて格段に使いやすくなっています。"
            
            # ジョブ開始
            jobs[job_id] = {
                'status': 'processing',
                'message': 'デモ記事を生成中...'
            }
            
            # 記事生成（デモ版）
            article = generate_article_from_text(demo_transcript)
            
            jobs[job_id] = {
                'status': 'completed',
                'message': '記事生成完了',
                'article': article
            }
            
            response = {'job_id': job_id, 'message': '記事生成を開始しました'}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            error_response = {'error': str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def serve_status(self, job_id):
        job = jobs.get(job_id, {'status': 'not_found', 'error': 'ジョブが見つかりません'})
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(job, ensure_ascii=False).encode('utf-8'))

def run_server(port=8000):
    handler = AudioToArticleHandler
    
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"🚀 サーバーが起動しました: http://127.0.0.1:{port}")
        print("Ctrl+C で停止します")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 サーバーを停止しました")

if __name__ == "__main__":
    run_server()