import os
import shutil
import uuid
import json
import MeCab
import markdown
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from google.cloud import speech
import subprocess
import tempfile
from pathlib import Path

# --- セットアップと初期化 ---
load_dotenv()

app = FastAPI(title="音声から記事化ツール")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ジョブの状態管理
jobs = {}

def clear_job_history():
    """ジョブ履歴をクリア"""
    global jobs
    jobs.clear()
    print("🗑️ ジョブ履歴をクリアしました")

# Google Gemini設定
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    print("警告: GOOGLE_API_KEYが設定されていません")
    gemini_model = None
else:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# Google Cloud Speech-to-Text設定
speech_client = None
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    try:
        speech_client = speech.SpeechClient()
    except Exception as e:
        print(f"Speech-to-Text初期化エラー: {e}")

# MeCab設定
try:
    mecab_tagger = MeCab.Tagger()
except Exception as e:
    print(f"MeCab初期化エラー: {e}")
    mecab_tagger = None

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

def analyze_style_with_mecab(text: str) -> str:
    """MeCabで文体分析"""
    if not mecab_tagger:
        return "・文体は「ですます調」を基本とします。"
    
    try:
        node = mecab_tagger.parseToNode(text)
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
        print(f"MeCab解析エラー: {e}")
        return "・文体は「ですます調」を基本とします。"

def convert_audio_format(input_path: str, output_path: str) -> bool:
    """音声ファイルをWAVに変換"""
    try:
        # ffmpegを使用してWAVに変換
        cmd = [
            'ffmpeg', '-i', input_path, '-acodec', 'pcm_s16le', 
            '-ar', '16000', '-ac', '1', output_path, '-y'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"音声変換エラー: {e}")
        return False

def transcribe_with_gemini(audio_path: str) -> str:
    """Gemini APIを使用した音声文字起こし"""
    try:
        if not gemini_model:
            return None
        
        # 音声ファイルをアップロード
        with open(audio_path, "rb") as audio_file:
            audio_file_obj = genai.upload_file(audio_file, mime_type="audio/wav")
        
        # Geminiで文字起こし
        prompt = "この音声ファイルの内容を日本語で文字起こししてください。正確に、自然な文章として出力してください。"
        response = gemini_model.generate_content([audio_file_obj, prompt])
        
        # ファイルを即座に削除
        genai.delete_file(audio_file_obj.name)
        
        return response.text
    except Exception as e:
        print(f"Gemini文字起こしエラー: {e}")
        return None

def process_audio_to_article(job_id: str, audio_path: str):
    """音声から記事生成処理"""
    try:
        # Step 1: 音声文字起こし
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "音声ファイルを処理しています..."
        
        # 音声ファイルの変換
        wav_path = None
        transcript = None
        
        # 元のファイル拡張子を確認
        file_ext = Path(audio_path).suffix.lower()
        
        # WAVでない場合は変換
        if file_ext != '.wav':
            jobs[job_id]["message"] = "音声ファイルを変換しています..."
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                wav_path = temp_wav.name
            
            if not convert_audio_format(audio_path, wav_path):
                # 変換に失敗した場合は元のファイルを使用
                wav_path = audio_path
        else:
            wav_path = audio_path
        
        jobs[job_id]["message"] = "音声ファイルを文字起こししています..."
        
        # まずGemini APIで試行
        transcript = transcribe_with_gemini(wav_path)
        
        # Geminiが利用できない場合はGoogle Cloud Speech-to-Textを試行
        if not transcript and speech_client:
            try:
                with open(wav_path, "rb") as audio_file:
                    content = audio_file.read()
                
                audio = speech.RecognitionAudio(content=content)
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="ja-JP",
                )
                response = speech_client.recognize(config=config, audio=audio)
                transcript = " ".join([result.alternatives[0].transcript for result in response.results])
            except Exception as e:
                print(f"Google Cloud Speech-to-Text エラー: {e}")
        
        # どちらも失敗した場合はエラーを返す
        if not transcript:
            raise Exception("音声の文字起こしに失敗しました。音声ファイルを確認してください。")
        
        if not transcript:
            raise Exception("文字起こしに失敗しました")
        
        # Step 2: 文体分析
        jobs[job_id]["message"] = "文体を分析しています..."
        style_prompt = analyze_style_with_mecab(FIXED_STYLE_TEXT)
        
        # Step 3: 記事生成
        jobs[job_id]["message"] = "AIが記事を生成しています..."
        
        if not gemini_model:
            raise Exception("Gemini APIキーが設定されていません")
        
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
        
        ai_response = gemini_model.generate_content(final_prompt)
        markdown_result = ai_response.text
        html_result = markdown.markdown(markdown_result)
        
        jobs[job_id].update({
            "status": "completed",
            "message": "記事の生成が完了しました！",
            "markdown": markdown_result,
            "html": html_result
        })
        
    except Exception as e:
        print(f"[{job_id}] エラー: {e}")
        jobs[job_id].update({
            "status": "failed", 
            "error": str(e)
        })
    finally:
        # 一時ファイルの完全削除
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
            if wav_path and wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception as e:
            print(f"⚠️ 一時ファイル削除エラー: {e}")
        
        # メモリ上のデータをクリア
        transcript = None
        wav_path = None

# --- APIエンドポイント ---

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """フロントエンドページ"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>static/index.htmlが見つかりません</h1>", status_code=404)

@app.post("/generate-article/")
async def start_generation(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...)
):
    """音声ファイルから記事生成開始"""
    job_id = str(uuid.uuid4())
    
    # 一時ディレクトリ作成
    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    audio_path = os.path.join(temp_dir, f"{job_id}_{audio_file.filename}")
    
    # ファイル保存
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
    
    # ジョブ開始
    jobs[job_id] = {"status": "queued", "message": "処理待機中..."}
    background_tasks.add_task(process_audio_to_article, job_id, audio_path)
    
    return {"job_id": job_id, "message": "記事生成を開始しました"}

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """ジョブ状態確認"""
    job = jobs.get(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "ジョブが見つかりません"})
    return JSONResponse(content=job)

@app.post("/clear-history/")
async def clear_history():
    """ジョブ履歴とデータをクリア"""
    clear_job_history()
    return JSONResponse(content={"message": "履歴がクリアされました"})

@app.get("/health/")
async def health_check():
    """システム状態確認"""
    return JSONResponse(content={
        "status": "healthy",
        "active_jobs": len(jobs),
        "gemini_available": gemini_model is not None,
        "speech_api_available": speech_client is not None
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)