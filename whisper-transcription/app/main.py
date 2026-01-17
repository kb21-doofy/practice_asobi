#!/usr/bin/env python3
"""
文字起こしWebアプリ（Streamlit使用）
"""

import os
import time
import tempfile
import streamlit as st
from datetime import datetime
from usecase.service.transcription_service import TranscriptionService
# TODO: ハイライト抽出機能を追加する場合は、以下のコメントを解除する。
# from usecase.service.extract_highlights_service import ExtractHighlightsService
# from adapter.openai_client import OpenAIClient

# ページ設定
st.set_page_config(
    page_title="文字起こしツール",
    page_icon="🎤",
    layout="wide"
)

# キャッシュ設定（サービスインスタンスを再作成しないようにする）
@st.cache_resource
def _get_transcription_service(model_name: str):
    """TranscriptionServiceインスタンスを取得する（キャッシュ使用）"""
    return TranscriptionService(model_name=model_name)

def _check_ffmpeg():
    """FFmpegがインストールされているか確認"""
    if not TranscriptionService.check_ffmpeg():
        st.error("⚠️ FFmpegがインストールされていません。https://ffmpeg.org/download.html からダウンロードしてください。")
        st.stop()

def _get_available_models():
    """利用可能な処理モードの一覧を返す"""
    return TranscriptionService.get_available_models()

def main():
    """メイン関数"""
    st.title("🎤 文字起こしツール")
    st.markdown("""
    音声ファイルからテキストへの文字起こしを行います。
    """)
    
    # FFmpegの確認
    _check_ffmpeg()
    
    # サイドバー設定
    st.sidebar.title("設定")
    
    # モデル選択
    model_option = st.sidebar.selectbox(
        "モデルサイズを選択",
        options=_get_available_models(),
        index=1,  # baseをデフォルトに
        help="大きいモデルほど精度が上がりますが、処理時間も増加します。"
    )
    
    # 言語選択
    language_option = st.sidebar.selectbox(
        "言語を選択（自動検出する場合は空欄）",
        options=["", "en", "ja", "zh", "de", "fr", "es", "ko", "ru"],
        index=0,
        format_func=lambda x: {
            "": "自動検出", "en": "英語", "ja": "日本語", "zh": "中国語",
            "de": "ドイツ語", "fr": "フランス語", "es": "スペイン語",
            "ko": "韓国語", "ru": "ロシア語"
        }.get(x, x),
        help="音声の言語を指定します。自動検出も可能です。"
    )
    
    # サイドバーにGitHubリンク
    st.sidebar.markdown("---")
    st.sidebar.markdown("[GitHubリポジトリ](https://github.com/yourusername/whisper-transcription)")
    
    # ファイルアップロード
    uploaded_file = st.file_uploader(
        "動画ファイルをアップロード",
        type=None,
        help="対応フォーマット: MP4"
    )
    
    if uploaded_file is not None:
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext != ".mp4":
            st.error("⚠️ MP4形式のみ対応しています。別のファイル形式が選択されています。")
            st.stop()
        # ファイル情報表示
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.info(f"ファイル: {uploaded_file.name} ({file_size_mb:.2f} MB)")
        
        # 音声再生機能
        st.audio(uploaded_file, format=f"audio/{uploaded_file.name.split('.')[-1]}")
        
        # 文字起こし実行ボタン
        transcribe_button = st.button("文字起こし開始", type="primary")
        
        if transcribe_button:
            # 処理開始
            with st.spinner("文字起こし処理中..."):
                # 一時ファイルとして保存
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_filename = tmp_file.name
                
                try:
                    # サービスの取得（キャッシュから）
                    load_start = time.time()
                    progress_text = st.empty()
                    progress_text.text("モデルをロード中...")
                    transcription_service = _get_transcription_service(model_option)
                    transcription_service.load_model()  # 初期化（初回のみ）
                    load_end = time.time()
                    progress_text.text(f"モデルロード完了（{load_end - load_start:.2f}秒）")
                    
                    # 文字起こし処理
                    progress_text.text("文字起こし処理中...")
                    transcribe_start = time.time()
                    
                    # 文字起こし実行
                    result = transcription_service.transcribe(
                        temp_filename,
                        language=language_option if language_option else None
                    )
                    
                    transcribe_end = time.time()
                    progress_text.empty()
                    
                    # 処理時間計算
                    transcribe_time = transcribe_end - transcribe_start
                    total_time = transcribe_end - load_start
                    
                    # 結果表示
                    st.markdown("### 文字起こし結果")
                    st.success(f"処理完了（文字起こし: {transcribe_time:.2f}秒、合計: {total_time:.2f}秒）")
                    
                    # テキスト結果表示
                    st.markdown("#### テキスト")
                    st.text_area("", value=result["text"], height=200)
                    
                    # ダウンロードボタン
                    st.download_button(
                        label="テキストをダウンロード",
                        data=result["text"],
                        file_name=f"{os.path.splitext(uploaded_file.name)[0]}_transcript.txt",
                        mime="text/plain"
                    )
                    
                    # タイムスタンプ付きの詳細結果
                    with st.expander("詳細（タイムスタンプ付き）"):
                        # テーブル表示用のデータ準備
                        table_data = []
                        timestamp_text = ""
                        
                        for segment in result["segments"]:
                            start_time = segment["start"]
                            end_time = segment["end"]
                            text = segment["text"]
                            
                            # 時間をフォーマット (HH:MM:SS.ms)
                            start_formatted = str(datetime.utcfromtimestamp(start_time).strftime('%H:%M:%S.%f'))[:-3]
                            end_formatted = str(datetime.utcfromtimestamp(end_time).strftime('%H:%M:%S.%f'))[:-3]
                            
                            table_data.append({
                                "開始": start_formatted,
                                "終了": end_formatted,
                                "テキスト": text
                            })
                            
                            timestamp_text += f"[{start_formatted} --> {end_formatted}] {text}\n"
                        
                        # テーブル表示
                        st.table(table_data)
                        
                        # タイムスタンプ付きテキストのダウンロードボタン
                        st.download_button(
                            label="タイムスタンプ付きテキストをダウンロード",
                            data=timestamp_text,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_transcript_timestamps.txt",
                            mime="text/plain"
                        )
                
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")
                
                finally:
                    # 一時ファイルの削除
                    if os.path.exists(temp_filename):
                        os.unlink(temp_filename)
    
    else:
        # ファイルがアップロードされていない場合の表示
        st.info("👆 音声ファイルをアップロードしてください")
        
        # サンプル説明
        with st.expander("使い方"):
            st.markdown("""
            1. サイドバーでモデルサイズと言語を選択
            2. 音声ファイルをアップロード
            3. 「文字起こし開始」ボタンをクリック
            4. 結果を確認し、必要に応じてダウンロード
            
            **処理モードについて:**
            - light: 最小・最速（低精度）
            - standard: バランス型（推奨）
            - accurate: 高精度（処理時間が長い）
            """)

if __name__ == "__main__":
    main()
