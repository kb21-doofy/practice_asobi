#!/usr/bin/env python3
"""
文字起こしWebアプリ（Streamlit使用）
"""

import os
import time
import json
from datetime import datetime
import tempfile
import streamlit as st
from usecase.service.trim_video_service import TrimVideoService
from usecase.service.add_subtitles_service import AddSubtitlesService
from usecase.service.transcribe_video_service import TranscribeVideoService
from adapter.llm_factory import LLMFactory
from domain.entities.llm_provider import LLMProvider
from utli.logger import get_logger

logger = get_logger(__name__)

# ページ設定
st.set_page_config(
    page_title="文字起こしツール",
    page_icon="🎤",
    layout="wide"
)

# キャッシュ設定（サービスインスタンスを再作成しないようにする）
def _check_ffmpeg():
    """FFmpegがインストールされているか確認"""
    if os.system("ffmpeg -version > /dev/null 2>&1") != 0:
        st.error("⚠️ FFmpegがインストールされていません。https://ffmpeg.org/download.html からダウンロードしてください。")
        st.stop()

def main():
    """メイン関数"""
    st.title("🎤 文字起こしツール")
    st.markdown("""
    MP4ファイルから重要な箇所だけを抽出して文字起こしします。
    """)
    
    # FFmpegの確認
    _check_ffmpeg()
    
    # サイドバー設定
    st.sidebar.title("設定")
    
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

    # プロバイダー選択
    provider_option = st.sidebar.selectbox(
        "プロバイダーを選択",
        options=["openai", "gemini"],
        index=1,
        help="重要箇所抽出に使用するLLMプロバイダーを選択します。"
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
        transcribe_button = st.button("動画処理開始", type="primary")
        
        if transcribe_button:
            # 処理開始
            with st.spinner("動画処理中..."):
                temp_filename = None
                # 一時ファイルとして保存
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_filename = tmp_file.name
                
                try:
                    # 重要箇所の抽出（抽象的な処理）
                    load_start = time.time()
                    progress_text = st.empty()
                    progress_text.text("重要シーンを抽出中...")
                    provider_map = {
                        "openai": LLMProvider.OPENAI,
                        "gemini": LLMProvider.GEMINI,
                    }
                    llm_factory = LLMFactory(provider_map[provider_option])
                    trim_service = TrimVideoService(llm_factory)
                    payload = trim_service.extract_key_segments(temp_filename)
                    logger.info(f"trim payload keys: {list(payload.keys())}")
                    st.success("トリミング範囲の抽出が完了しました。")
                    load_end = time.time()
                    progress_text.empty()
                    
                    # 処理時間計算
                    total_time = load_end - load_start
                    
                    # 結果表示
                    st.markdown("### トリミング範囲")
                    st.success(f"処理完了（合計: {total_time:.2f}秒）")

                    raw_response = payload.get("raw_response")
                    trim_payload = {k: v for k, v in payload.items() if k != "raw_response"}
                    logger.info(f"important_scenes count: {len(trim_payload.get('important_scenes', []))}")
                    if raw_response:
                        st.text_area(
                            "重要シーン抽出の生レスポンス",
                            value=raw_response,
                            height=200,
                        )

                    if trim_payload.get("important_scenes"):
                        logger.info("trim flow: important_scenes found")
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as out_file:
                                output_video_path = out_file.name
                            logger.info(f"trim flow: output_video_path={output_video_path}")
                            trim_start, trim_end = trim_service.trim_by_segments(
                                temp_filename,
                                trim_payload,
                                output_video_path,
                            )
                            logger.info(f"trim flow: trim_start={trim_start}, trim_end={trim_end}")
                            start_formatted = str(datetime.utcfromtimestamp(trim_start).strftime("%H:%M:%S.%f"))[:-3]
                            end_formatted = str(datetime.utcfromtimestamp(trim_end).strftime("%H:%M:%S.%f"))[:-3]
                            st.info(f"start_time: {start_formatted} / end_time: {end_formatted}")
                            progress_text.text("文字起こし処理を開始中...")
                            logger.info("transcribe_video start")
                            transcribe_factory = LLMFactory(LLMProvider.GEMINI)
                            transcribe_service = TranscribeVideoService(transcribe_factory)
                            transcribed = transcribe_service.transcribe(output_video_path)
                            logger.info("transcribe_video complete")
                            progress_text.text("文字起こし処理が完了しました。")
                            segments = transcribed.get("segments", [])
                            logger.info(f"subtitle flow: segments_count={len(segments)}")
                            subtitle_service = AddSubtitlesService()
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as subtitle_file:
                                subtitle_output_path = subtitle_file.name
                            logger.info(f"subtitle flow: subtitle_output_path={subtitle_output_path}")
                            subtitle_service.add_subtitles_to_trimmed_video(
                                output_video_path,
                                segments,
                                0.0,
                                subtitle_output_path,
                            )
                            logger.info("subtitle flow: add_subtitles_to_trimmed_video complete")
                            st.markdown("### 字幕付き切り抜き動画")
                            st.video(subtitle_output_path)
                            with open(subtitle_output_path, "rb") as f:
                                st.download_button(
                                    label="字幕付き切り抜き動画をダウンロード",
                                    data=f,
                                    file_name="trimmed_subtitled.mp4",
                                    mime="video/mp4",
                                )
                            st.text_area(
                                "重要シーン抽出レスポンス",
                                value=json.dumps(trim_payload, ensure_ascii=False, indent=2),
                                height=200,
                            )
                            st.text_area(
                                "文字起こしレスポンス",
                                value=json.dumps(transcribed, ensure_ascii=False, indent=2),
                                height=240,
                            )
                        except Exception as e:
                            st.error(f"切り抜き処理でエラーが発生しました: {str(e)}")
                    else:
                        logger.warning("trim ranges is empty or missing")
                        st.info("重要箇所が抽出されませんでした。")
                
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")
                
                finally:
                    # 一時ファイルの削除
                    if temp_filename and os.path.exists(temp_filename):
                        os.unlink(temp_filename)
    
    else:
        # ファイルがアップロードされていない場合の表示
        st.info("👆 音声ファイルをアップロードしてください")
        
        # サンプル説明
        with st.expander("使い方"):
            st.markdown("""
            1. サイドバーで言語を選択
            2. 動画ファイルをアップロード
            3. 「文字起こし開始」ボタンをクリック
            4. 結果を確認し、必要に応じてダウンロード
            """)

if __name__ == "__main__":
    main()
