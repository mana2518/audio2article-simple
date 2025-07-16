#!/usr/bin/env python3
"""
Whisper + Claude Code 音声記事化システム
APIコストゼロ・ローカル文字起こし対応
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

class WhisperTranscriber:
    def __init__(self):
        # Whisperモデルの初期化
        self.model = None
        self.model_name = "tiny"  # 超高速処理用tinyモデルを使用
        
        # 文体学習用ファイルパス
        self.style_file_path = "/Users/manami/(N)note本文.md"
        
        # 文体サンプルを読み込み
        self.style_text = self.load_style_sample()
        
        # 処理ファイルの管理
        self.current_audio_name = None

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
        """文体サンプルファイルを読み込み（note記事用に最適化）"""
        try:
            if os.path.exists(self.style_file_path):
                with open(self.style_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # note記事の文体特徴を抽出
                    lines = content.split('\n')
                    style_samples = []
                    current_article = []
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        # 日付や括弧で始まる行は除外
                        if line.startswith('(') or line.startswith('2025/') or line.startswith('202'):
                            # 記事の区切りとして処理
                            if current_article:
                                article_text = '\n'.join(current_article)
                                if len(article_text) > 100:  # 十分な長さがある記事のみ
                                    style_samples.append(article_text)
                                current_article = []
                            continue
                        
                        # 記事内容を蓄積
                        current_article.append(line)
                        
                        # 十分なサンプルが集まったら終了
                        if len(style_samples) >= 3:
                            break
                    
                    # 最後の記事も処理
                    if current_article:
                        article_text = '\n'.join(current_article)
                        if len(article_text) > 100:
                            style_samples.append(article_text)
                    
                    # 文体学習用サンプルを結合
                    if style_samples:
                        return '\n\n---\n\n'.join(style_samples[:3])  # 最大3記事
                    
            # フォールバック用デフォルト文体
            return """マナミです。

今回は「エラーに強くなった」という話をしたいと思います。

最近、プログラミングをしていてエラーが出ることに慣れてきたなと感じています。以前はエラーが出ると「うわー、どうしよう」と焦っていたのですが、今は「あ、またエラーね」という感じで落ち着いて対処できるようになりました。

これって実はすごく大切なスキルだと思うんです。エラーは問題ではなく、「ここを直してね」というメッセージなんですよね。そう考えると、エラーって実は親切な存在なんです。

皆さんも何か新しいことを始める時、最初はうまくいかないことが多いと思います。でも、それは当たり前のことで、失敗から学ぶことがとても大切です。"""
        except Exception as e:
            print(f"❌ 文体ファイル読み込みエラー: {e}")
            return "マナミです。\n\n今回は音声配信の内容について話します。"

    def cleanup_previous_files(self):
        """前回の処理ファイルを完全クリアする"""
        try:
            current_dir = Path.cwd()
            cleanup_count = 0
            
            # 前回の文字起こし・記事ファイルを削除
            for file_path in current_dir.glob('*'):
                if file_path.is_file():
                    # 処理ファイルのパターンをチェック
                    if any(pattern in file_path.name for pattern in [
                        '_transcript.txt', '_article.txt', 
                        'temp', 'tmp', '.whisper', '.cache'
                    ]) and file_path.suffix in ['.txt', '.wav', '.mp3', '.cache']:
                        file_path.unlink()
                        cleanup_count += 1
            
            # メモリ上のデータをクリア
            if hasattr(self, 'model') and self.model:
                # Whisperモデルのキャッシュをクリア（メモリ節約）
                pass  # Whisperモデル自体は保持して再利用する
            
            if cleanup_count > 0:
                print(f"🧹 前回の処理ファイル {cleanup_count}個をクリアしました")
            
        except Exception as e:
            print(f"⚠️ ファイルクリア中にエラー: {e}")

    def print_banner(self):
        """バナー表示"""
        print("🎙️" + "="*60)
        print("    Whisper + Claude Code 音声記事化システム")
        print("    💰 APIコストゼロ・ローカル処理対応")
        print("="*62)
        
        # 文体学習状況を表示
        if os.path.exists(self.style_file_path):
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

    def transcribe_with_whisper(self, audio_path: str) -> str:
        """Whisperによる音声文字起こし"""
        try:
            self.load_whisper_model()
            
            # 音声ファイルの長さを取得（概算）
            try:
                import librosa
                duration = librosa.get_duration(path=audio_path)
                estimated_time = duration / 4  # 大まかな推定時間
                print(f"\n🎵 音声長: {duration/60:.1f}分 (推定処理時間: {estimated_time/60:.1f}分)")
            except:
                print(f"\n🎵 音声ファイルを処理中...")
            
            print("🗣️ Whisperで文字起こし中...")
            result = self.model.transcribe(audio_path, language="ja")
            transcript = result["text"]
            
            print(f"✅ 文字起こし完了 ({len(transcript)}文字)")
            return transcript
            
        except Exception as e:
            print(f"❌ Whisper文字起こしエラー: {e}")
            return None

    def clean_transcript(self, transcript: str) -> str:
        """文字起こしテキストの徹底的修正"""
        text = transcript.strip()
        
        # 段階1: 重複表現・冗長表現の徹底削除
        redundant_patterns = [
            r'はい、?', r'えー、?', r'あの、?', r'えっと、?', r'うーん、?', 
            r'まぁ、?', r'そうですね、?', r'なんか、?', r'ね、?', r'と、',
            r'って、?', r'っていう', r'みたいな感じ', r'っていうこと',
            r'という風に', r'という', r'のとか', r'など', r'、、', r'。。',
            r'ちょっと、?', r'まあ、?', r'うん、?', r'そう、?', r'、まあ',
            r'、ちょっと', r'、なんか', r'、でも', r'、そう', r'、うん'
        ]
        
        for pattern in redundant_patterns:
            text = re.sub(pattern, '', text)
        
        # 過度な読点を削除
        text = re.sub(r'、+', '、', text)
        text = re.sub(r'、([、。])', r'\1', text)  # 読点の後に読点や句点
        text = re.sub(r'([あいうえお])、([あいうえお])', r'\1\2', text)  # 不要な読点
        
        # 段階2: 明らかな誤認識の修正と漢字化
        corrections = {
            # ユーザー報告の具体的エラー
            '日山波です': 'マナミです',
            '日山波': 'マナミ',
            'サニーの子ども': '3人の子ども', 
            'サニー': '3人',
            '一斉にス発進': 'SNS発信',
            '一斉に素発進': 'SNS発信',
            'コンテンセサコ': 'コンテンツ作成',
            
            # 基本的な誤認識
            'ののかぎゅうび': '',
            'のかぎゅうび': '',
            'かぎゅうび': '',
            'まん波': 'マナミ',
            '学み': 'マナミ',
            'ままふりなす': 'ママフリーランス',
            'フリランス': 'フリーランス',
            'フリーナース': 'フリーランス',
            'SNS 卒業社や': 'SNS発信や',
            'コンテンツ作成にお仕事をして': 'コンテンツ作成の仕事をしている',
            'コンテンチェーサーコーチューシン': 'コンテンツ作成',
            'バイブコーディング': 'ライブコーディング',
            'サニティ': 'Sanity',
            'ワードブレス': 'WordPress',
            'おやむけ': '短冊',
            'ポートフリオ': 'ポートフォリオ',
            
            # v2.0からの包括的修正パターン
            'とという': 'という',
            'ととという': 'という', 
            'とと': 'と',
            'ということという': 'ということ',
            'やとぱり': 'やっぱり',
            'どとか': 'どこか',
            'やとて': 'やって',
            '作とて': '作って',
            'とて': 'って',
            'せとかく': 'せっかく',
            'やとている': 'やっている',
            'やとています': 'やっています',
            '持とて': '持って',
            'かぶとた': 'かぶった',
            
            # 語尾の誤認識
            '思今す': '思います',
            '思今した': '思いました',
            'ござ今した': 'ございました',
            '今す': 'います',
            '今した': 'ました',
            'なりたいな': 'なりたいなあ',
            'いいかな': 'いいかなあ',
            
            # よくある誤認識パターン
            'やおります': 'やっています',
            'やいる': 'やっている',
            'やもいい': 'やってもいい',
            'やろー': 'やろう',
            'あれる': 'できる',
            'いけば': 'いけば',
            'おとも': '今日も',
            
            # 文法的修正
            'だったま': 'だから',
            'いうは': 'というのは',
            'ふうに': 'という風に',
            'のとか': 'など',
            '探索書いて': '短冊に書いて',
            '商演': '仕事で',
            '単座コミニ効果な': '',
            '頼ばた風': '七夕飾り',
            '不管して': '俯瞰して',
            '静つも': '正体も',
            '静だな': '正体だな',
            'シオー': 'しよう',
            'あもいい': 'あってもいい',
            'うめこめる': '埋め込める',
            'やたほうな': 'やった方の',
            'あちょっと': 'あと、ちょっと',
            '周囲気': '収益',
            '入くる': '入ってくる',
            'になて': 'になって',
            '微々たん': '微々たる',
            'いかつい': 'いかにも',
            'あこりゃ': 'あ、これは',
            '成球所': '名刺',
            'なんてとという': 'なんていう',
            'ベレーボー': 'ベレー帽',
            'カブッダ': 'かぶった',
            '使使': '使う',
            'わがない': 'わからない',
            'お進め': 'おすすめ',
            '作いく': '作っていく',
            '頑張いき': '頑張っていき',
            
            # ひらがなの漢字化
            'いう': 'という',
            'とた': 'った',
            'やとた': 'やった',
            'あとた': 'あった',
            'だとた': 'だった',
            'しとた': 'した',
            'きとた': 'きた',
            'いとた': 'いた',
            'ちょと': 'ちょっと',
            'やとぱり': 'やっぱり',
            'なとた': 'なった',
            'できる': 'できる',
            'やって': 'やって',
            'もう': 'もう',
            'とき': '時',
            'ひと': '人',
            'いま': '今',
            'じぶん': '自分',
            'かぞく': '家族',
            'こども': '子供',
            'しごと': '仕事',
            'つくる': '作る',
            'かんがえる': '考える',
            'おもう': '思う',
            
            # 動詞系の修正
            'やおります': 'やっています',
            'やいる': 'やっている',
            'やもいい': 'やってもいい',
            'やろー': 'やろう',
            'やっとい': 'やってみよう',
            'やってお': 'やっていこう',
            'やっとく': 'やっていく',
            'あれる': 'できる',
            'おとも': '今日も',
            'やます': 'やります',
            'やいこう': 'やっていこう',
            'や作い': 'を作って',
            
            # 語尾・助詞の修正
            'っと': 'と',
            'だったま': 'だから',
            'いうは': 'というのは',
            'みんなを': 'みんなで',
            'ちょと': 'ちょっと',
            '野豪が': '屋号が',
            '野豪': '屋号',
            'パベート': 'プライベート',
            'いけばさん': 'いけはやさん',
            'いけやや': 'いけはや',
            'PRアンケン': 'PR案件',
            '商品レベル': '商品レビュー',
            '海洋サポート': '介護サポート',
            '大正配信': '音声配信',
            '内容の音にやます': '内容も入ります',
            'どぐち': '窓口',
            'アフィリエット': 'アフィリエイト',
            'ノビタン': '伸びたん',
            'ビビタン': '微々たん',
            'すすーせ': '数千円',
            'A使': 'AI',
            '重要ある': '需要がある',
            'いっか': '一つ',
            '片をあら': '片手間で',
            'チョコチョコと作ます': 'ちょこちょこと作る',
            'もしくして': 'もしかして',
            '有量': '有料',
            '可能性もまる': '可能性もある',
            '頼おろし': '棚卸し',
            'やきた': 'やってきた',
            'あれる': 'できる',
            'みんなです': 'みんなを見る',
            'ダツ': '',
            'やみよう': 'やってみよう',
            'じろー': 'しよう',
            '最途構築': 'サイト構築',
            '触みて': '触ってみて',
            'ほどの': 'ほとんど',
            'いけやや': 'いけはや',
            '張りまく': '貼りまくって',
            '実践器': '実績を',
            '貴重からは': '基調カラーは',
            'コントカット': 'コンタクト',
            '薬ピンク': '濃いピンク',
            '成球所': '名刺',
            'いかきぎ': 'いかつい',
            'ベレーボー': 'ベレー帽',
            'カブッダ': 'かぶった',
            'バババババ': '',
            '勝手手間': '片手間',
            'やいこう': 'やっていこう',
            'パワファラ': 'パワハラ',
            'なきて': 'なって',
            'やみよう': 'やってみよう',
            '持いけ': '持っていけ',
            'やいこう': 'やっていこう',
        }
        
        # 修正を適用
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        # 段階3: 文章構造の整理
        text = re.sub(r'、+', '、', text)  # 連続する読点
        text = re.sub(r'。+', '。', text)  # 連続する句点
        text = re.sub(r'\s+', ' ', text)  # 余分な空白
        text = re.sub(r'、\s*、', '、', text)  # 空白を挟んだ読点
        text = re.sub(r'。\s*。', '。', text)  # 空白を挟んだ句点
        text = re.sub(r'^、', '', text)  # 文頭の読点
        
        # 段階4: 意味のない断片を削除
        meaningless_fragments = [
            'ね', 'と', 'で', 'が', 'を', 'に', 'の', 'は', 'も', 'から', 'まで',
            'より', 'こう', 'そう', 'どう', 'いう', 'する', 'ある', 'なる', 'いる'
        ]
        
        sentences = text.split('。')
        cleaned_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:
                # 意味のない短い断片を除外
                if not (len(sentence) <= 6 and sentence in meaningless_fragments):
                    # 文頭の余分な記号を削除
                    sentence = re.sub(r'^[、。\s]+', '', sentence)
                    if sentence:
                        cleaned_sentences.append(sentence)
        
        result = '。'.join(cleaned_sentences)
        if cleaned_sentences:
            result += '。'
        
        # 段階5: 読点の適正化
        result = self.optimize_punctuation(result)
        
        # 段階6: 漢字変換
        result = self.convert_to_kanji(result)
        
        # 最終段階: 文章の流れを自然にする
        result = self.improve_sentence_flow(result)
        
        return result
    
    def improve_sentence_flow(self, text: str) -> str:
        """文章の流れを自然にする"""
        # 文の接続を改善と読点削減
        flow_improvements = {
            '。で、': '。\n\n',
            '。そして、': '。\n\n',  
            '。また、': '。\n\n',
            '。あと、': '。\n\nあと',
            '。それから、': '。\n\nそれから',
            '。だから、': '。\n\nだから',
            '。つまり、': '。\n\nつまり',
            '。ということで、': '。\n\nということで',
            '。というわけで、': '。\n\nというわけで',
            # 不自然な表現を修正
            'いう': 'という',
            'っ': 'と',
            'とた': 'った',
            'やとた': 'やった',
            'あとた': 'あった',
            'だとた': 'だった',
            'なとた': 'なった',
            'しとた': 'した',
            'きとた': 'きた',
            'いとた': 'いた',
            'やとぱり': 'やっぱり',
            'ちょと': 'ちょっと',
            'どとか': 'どこか',
            'なんてとという': 'なんていう',
            'かぶとた': 'かぶった',
            'やとている': 'やっている',
            'やとて': 'やって',
            '作とて': '作って',
            'とて': 'って',
            'せとかく': 'せっかく',
            'やとています': 'やっています',
            '持とて': '持って',
            'なとた': 'なった',
        }
        
        for old, new in flow_improvements.items():
            text = text.replace(old, new)
        
        # 重複表現を削除
        text = re.sub(r'(という){2,}', 'という', text)
        text = re.sub(r'(やって){2,}', 'やって', text)
        text = re.sub(r'(それ){2,}', 'それ', text)
        
        # 最終的な読点大幅削減
        text = re.sub(r'、([でもでからからのにをはがと]{1,2})([^、]{5,})', r'\1\2', text)
        text = re.sub(r'([私今]{1,2})、', r'\1は', text)
        
        return text

    def optimize_punctuation(self, text: str) -> str:
        """読点の最適化"""
        # 過度な読点を削除
        text = re.sub(r'、+', '、', text)
        text = re.sub(r'。+', '。', text)
        
        # 不要な読点パターンを削除
        text = re.sub(r'([私今])、', r'\1は', text)  # 「私、」→「私は」
        text = re.sub(r'、([でもだからそして])([^、]{5,})', r'\1\2', text)  # 接続詞前の読点削除
        text = re.sub(r'([^、]{15,})、([^、]{1,5})。', r'\1\2。', text)  # 短い語句前の読点削除
        
        # より積極的な読点削除
        text = re.sub(r'([です|ます])、', r'\1', text)  # 語尾後の読点削除
        text = re.sub(r'([と|で|に|を|が|は])、', r'\1', text)  # 助詞後の読点削除
        text = re.sub(r'、([とか|など|みたいな])', r'\1', text)  # 特定語句前の読点削除
        
        # 文頭の不要な記号削除
        text = re.sub(r'^[、。\s]+', '', text)
        text = re.sub(r'\n[、。\s]+', '\n', text)
        
        return text
    
    def convert_to_kanji(self, text: str) -> str:
        """適切な漢字変換"""
        kanji_conversions = {
            'いう': 'という',
            'とき': '時',
            'ひと': '人', 
            'いま': '今',
            'しごと': '仕事',
            'つくる': '作る',
            'かんがえる': '考える',
            'おもう': '思う',
            'つかう': '使う',
            'みる': '見る',
            'きく': '聞く',
            'はなす': '話す',
            'かく': '書く',
        }
        
        for hiragana, kanji in kanji_conversions.items():
            text = re.sub(rf'\b{hiragana}\b', kanji, text)
        
        return text

    def adjust_to_note_style(self, sentence: str) -> str:
        """note文体の特徴を活かした表現調整"""
        # 強調表現を「」で囲む
        emphasis_words = ["エラー", "コーディング", "プログラミング", "ライブコーディング"]
        for word in emphasis_words:
            if word in sentence and f"「{word}」" not in sentence:
                sentence = sentence.replace(word, f"「{word}」")
        
        # note文体特有の表現に調整
        adjustments = {
            "と思います": "と思うんです",
            "ということです": "ということなんです", 
            "感じします": "感じがします",
            "大切についてきた": "慣れてきた",
            "つまりどういうことかというと": "つまり",
            "そんな感じでございますが": "そんな感じで",
            "みたいな感じで": "という感じで",
            "ってのずっと": "をずっと",
            "つなに": "いつも",
            "かなり大切についてきた": "かなり慣れてきた"
        }
        
        for old, new in adjustments.items():
            sentence = sentence.replace(old, new)
        
        # 話し言葉的な表現を残す（note文体の特徴）
        if not sentence.endswith("…") and any(word in sentence for word in ["でも", "なんか", "やっぱり"]):
            # 語尾に少し柔らかさを加える
            sentence = sentence.replace("です。", "なんです。")
            sentence = sentence.replace("ます。", "ますよね。")
        
        return sentence

    def minimal_style_adjustment(self, sentence: str) -> str:
        """最小限の文体調整（音声内容を忠実に保持）"""
        # 話し言葉の自然な流れを保持しつつ、軽微な修正のみ
        simple_fixes = {
            'って言う': 'という',
            'みたいな感じで': 'という感じで',
            'なんていうか': '',
            'そういう感じで': 'という感じで',
            'ていう': 'という',
            'ってる': 'ている',
            '、、': '、',
            '。。': '。'
        }
        
        for old, new in simple_fixes.items():
            sentence = sentence.replace(old, new)
        
        # 自然な間を「･･･」で表現（元の音声の特徴を保持）
        if any(pause in sentence for pause in ['えー', 'うーん', 'そうですね']):
            sentence = re.sub(r'(えー|うーん|そうですね)', '･･･', sentence)
        
        return sentence.strip()

    def apply_note_style(self, sentence: str) -> str:
        """note記事らしい文体に調整"""
        # 基本的な語尾調整のみ
        style_adjustments = {
            'と思います': 'と思うんです',
            'ということです': 'ということなんです', 
            'でしょう': 'でしょうね',
            'ですね': 'なんですよね',
        }
        
        # 控えめに調整
        for old, new in style_adjustments.items():
            if sentence.endswith(old):
                sentence = sentence.replace(old, new)
        
        return sentence

    def polish_sentence(self, sentence: str) -> str:
        """文を記事らしく仕上げる"""
        # 読点の大幅削減と文章整理
        polishing = {
            # 基本的な表現修正
            'というふうに': 'という風に',
            'いうことです': 'ということです',
            'いうのは': 'というのは',
            'いうところ': 'というところ',
            'いうもの': 'というもの',
            'いう感じ': 'という感じ',
            'いうような': 'というような',
            'まあ、': '',
            'ちょっと、': '',
            'なんか、': '',
            'そうそう': '',
            'うんうん': '',
            'という、': 'という',
            'です、': 'です',
            'ます、': 'ます',
            'から、': 'から',
            'ので、': 'ので',
            'けど、': 'けど',
            'って、': 'って',
            'とか、': 'とか',
            'など、': 'など',
            # 読点削減パターン
            '、と、': 'と',
            '、で、': 'で',
            '、が、': 'が',
            '、を、': 'を',
            '、に、': 'に',
            '、は、': 'は',
            '、も、': 'も',
            '、の、': 'の',
            # 過度な読点を削減
            '私、': '私は',
            '今、': '今',
            'でも、': 'でも',
            'そして、': 'そして',
            'また、': 'また',
            'あと、': 'あと',
            'それから、': 'それから',
            'だから、': 'だから',
            'つまり、': 'つまり',
        }
        
        for old, new in polishing.items():
            sentence = sentence.replace(old, new)
        
        # 最終的な読点整理
        sentence = re.sub(r'([^、]{10,})、([^、]{1,5})。', r'\1\2。', sentence)  # 短い語句の前の読点削除
        sentence = re.sub(r'、([は|が|を|に|で|と|も|の])([^、]{1,10})', r'\1\2', sentence)  # 助詞前の読点削除
        
        return sentence.strip()

    def polish_paragraph(self, paragraph: str) -> str:
        """段落全体を仕上げる"""
        # 読みやすい長さに調整
        sentences = paragraph.split('。')
        polished_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # 文の開始を大文字に（必要に応じて）
                sentence = self.polish_sentence(sentence)
                polished_sentences.append(sentence)
        
        result = '。'.join(polished_sentences)
        if polished_sentences:
            result += '。'
        
        return result

    def generate_note_article(self, transcript: str) -> str:
        """文字起こしから直接記事を入力してもらう"""
        try:
            print("📝 文字起こし内容を参考にnote記事を生成してください")
            
            # 文字起こし内容を表示
            print("\n" + "="*60)
            print("📝 文字起こし内容:")
            print("="*60)
            print(transcript)
            print("="*60)
            
            # ユーザーに生成された記事を入力してもらう
            print("\n📝 上記を参考に記事を作成し、以下に貼り付けてください:")
            print("（複数行の場合は、最後に空行を入力してEnterを押してください）")
            
            lines = []
            empty_line_count = 0
            
            while True:
                try:
                    line = input()
                    if line.strip() == "":
                        empty_line_count += 1
                        if empty_line_count >= 2:  # 2回連続で空行が入力されたら終了
                            break
                        lines.append(line)
                    else:
                        empty_line_count = 0
                        lines.append(line)
                except EOFError:
                    break
            
            article = '\n'.join(lines).strip()
            
            if article:
                print(f"✅ note記事生成完了 ({len(article)}文字)")
                return article
            else:
                print("❌ 記事が入力されませんでした")
                return None
            
        except Exception as e:
            print(f"❌ 記事生成エラー: {e}")
            return None
    
    def add_section_breaks(self, article: str) -> str:
        """note記事らしい区切り線を追加"""
        paragraphs = article.split('\n\n')
        if len(paragraphs) > 3:  # 3段落以上の場合のみ区切り線を追加
            # 中間あたりに区切り線を追加
            mid_point = len(paragraphs) // 2
            paragraphs.insert(mid_point, "---------------")
        
        return '\n\n'.join(paragraphs)

    def save_results(self, transcript: str, article: str, filename: str):
        """結果をファイルに保存"""
        timestamp = Path(filename).stem
        
        # 文字起こし結果を保存
        transcript_file = f"{timestamp}_transcript.txt"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        # 整理済み記事を保存
        article_file = f"{timestamp}_article.txt"
        with open(article_file, 'w', encoding='utf-8') as f:
            f.write(article)
        
        return transcript_file, article_file

    def display_results(self, transcript: str, article: str, filename: str):
        """結果を表示"""
        print("\n" + "="*80)
        print("✨ 記事作成完了！")
        print("="*80)
        print(f"📁 元ファイル: {filename}")
        print(f"📝 文字起こし文字数: {len(transcript)}文字")
        if article:
            print(f"📰 完成記事文字数: {len(article)}文字")
        print("="*80)
        
        if article:
            # 記事を直接表示
            print("\n" + "="*80)
            print("📰 生成された記事:")
            print("="*80)
            print(article)
            print("="*80)
            
            # クリップボードにコピー
            try:
                pyperclip.copy(article)
                print("\n✅ 記事をクリップボードにコピーしました！")
            except Exception as e:
                print(f"⚠️ クリップボードコピーに失敗: {e}")
        else:
            print("\n📄 文字起こし結果:")
            print("-" * 40)
            print(transcript)
        
        # ファイル保存のオプション
        save_option = input("\n💾 結果をファイルに保存しますか？ (y/N): ").lower().strip()
        if save_option in ['y', 'yes']:
            try:
                if article:
                    transcript_file, article_file = self.save_results(transcript, article, filename)
                    print(f"✅ 文字起こし: {transcript_file}")
                    print(f"✅ 完成記事: {article_file}")
                else:
                    timestamp = Path(filename).stem
                    transcript_file = f"{timestamp}_transcript.txt"
                    with open(transcript_file, 'w', encoding='utf-8') as f:
                        f.write(transcript)
                    print(f"✅ 文字起こし: {transcript_file}")
            except Exception as e:
                print(f"❌ 保存に失敗しました: {e}")

    def show_progress(self, step: int, total_steps: int, message: str):
        """進行状況をパーセンテージで表示"""
        percentage = (step / total_steps) * 100
        bar_length = 30
        filled_length = int(bar_length * step / total_steps)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"\r[{bar}] {percentage:.1f}% - {message}", end='', flush=True)
        if step == total_steps:
            print()  # 改行

    def process_audio_file(self, audio_path: str):
        """音声ファイルの処理メイン"""
        try:
            filename = Path(audio_path).name
            total_steps = 6  # 総ステップ数
            
            # ステップ1: 初期化
            self.show_progress(1, total_steps, "初期化中...")
            
            # 新しい音声ファイルの処理開始時に前回のファイルをクリア
            if self.current_audio_name != filename:
                print(f"\n🆕 新しい音声ファイルを検出: {filename}")
                self.cleanup_previous_files()
                self.current_audio_name = filename
            
            print(f"🎵 処理開始: {filename}")
            
            # ステップ2: 音声ファイル変換
            self.show_progress(2, total_steps, "音声ファイル変換中...")
            wav_path = None
            file_ext = Path(audio_path).suffix.lower()
            
            if file_ext != '.wav':
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    wav_path = temp_wav.name
                
                if not self.convert_audio_format(audio_path, wav_path):
                    print("\n⚠️ 音声変換に失敗しました。元ファイルで試行します。")
                    wav_path = audio_path
            else:
                wav_path = audio_path
            
            # ステップ3: Whisperモデル読み込み
            self.show_progress(3, total_steps, "Whisperモデル読み込み中...")
            
            # ステップ4: 文字起こし
            self.show_progress(4, total_steps, "音声文字起こし中...")
            transcript = self.transcribe_with_whisper(wav_path)
            
            if not transcript:
                print("\n❌ 文字起こしに失敗しました")
                return
            
            # ステップ5: 記事生成
            self.show_progress(5, total_steps, "記事生成中...")
            article = self.generate_note_article(transcript)
            
            # ステップ6: 完了
            self.show_progress(6, total_steps, "処理完了")
            
            # 結果表示
            self.display_results(transcript, article, filename)
            
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
            article = None

def main():
    transcriber = WhisperTranscriber()
    transcriber.print_banner()
    
    parser = argparse.ArgumentParser(description="Whisper音声文字起こし + Claude Code記事生成")
    parser.add_argument("audio_file", nargs="?", help="音声ファイルのパス")
    parser.add_argument("--model", default="tiny", choices=["tiny", "base", "small", "medium", "large"],
                       help="使用するWhisperモデル (default: tiny)")
    
    args = parser.parse_args()
    
    if args.model:
        transcriber.model_name = args.model
    
    if args.audio_file:
        # コマンドライン引数から
        if not os.path.exists(args.audio_file):
            print("❌ ファイルが見つかりません:", args.audio_file)
            return
        
        transcriber.process_audio_file(args.audio_file)
    else:
        # インタラクティブモード
        print("💡 使用方法:")
        print("   1. 📁 音声ファイルをターミナルにドラッグ&ドロップしてEnter")
        print("   2. 📝 ファイルパスを直接入力")
        print("   3. ⚙️ オプション: --model [tiny/base/small/medium/large]")
        print()
        
        while True:
            try:
                print("🎯 音声ファイルをここにドラッグ&ドロップするか、パスを入力してください")
                file_path = input("🎙️ ファイル: ").strip()
                
                if file_path.lower() in ['q', 'quit', 'exit', '終了']:
                    print("👋 システムを終了します")
                    break
                
                # ドラッグ&ドロップ時の引用符・エスケープ文字を削除
                file_path = file_path.strip('"').strip("'").strip()
                
                # macOSのドラッグ&ドロップエスケープ処理
                file_path = file_path.replace('\\ ', ' ')
                file_path = file_path.replace('\\~', '~')
                file_path = file_path.replace('\\(', '(')
                file_path = file_path.replace('\\)', ')')
                file_path = file_path.replace('\\&', '&')
                file_path = file_path.replace('\\\'', "'")
                file_path = file_path.replace('\\"', '"')
                
                # 日本語の文字化け対策
                try:
                    # UTF-8でエンコードされた場合の修正
                    if 'ã' in file_path or 'â' in file_path:
                        file_path = file_path.encode('latin1').decode('utf-8')
                except:
                    pass
                
                # パスの正規化
                file_path = os.path.expanduser(file_path)
                file_path = os.path.abspath(file_path)
                
                print(f"🔍 処理中のパス: {file_path}")
                
                if not file_path:
                    print("⚠️ ファイルパスを入力してください")
                    continue
                
                if not os.path.exists(file_path):
                    print("❌ ファイルが見つかりません:", file_path)
                    print("💡 ファイルを直接ドラッグ&ドロップしてみてください")
                    continue
                
                transcriber.process_audio_file(file_path)
                
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