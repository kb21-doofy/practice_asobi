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
from moviepy import VideoFileClip
from usecase.service.trim_video_service import TrimVideoService
from usecase.service.add_subtitles_service import AddSubtitlesService
from usecase.service.transcribe_video_service import TranscribeVideoService
from usecase.service.translate_segments_service import TranslateSegmentsService
from adapter.llm_factory import LLMFactory
from domain.entities.llm_provider import LLMProvider
from config import SubtitleConstants
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

def _format_time(seconds: float) -> str:
    total_seconds = max(0.0, seconds)
    whole = int(total_seconds)
    millis = int(round((total_seconds - whole) * 1000))
    hours = whole // 3600
    minutes = (whole % 3600) // 60
    secs = whole % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

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
    
    translate_language_option = st.sidebar.selectbox(
        "翻訳先言語を選択（翻訳しない場合は空欄）",
        options=["", "en", "ja", "ko"],
        index=0,
        format_func=lambda x: {
            "": "翻訳しない", "en": "英語", "ja": "日本語", "ko": "韓国語"
        }.get(x, x),
        help="文字起こし結果を指定言語に翻訳します。"
    )

    # プロバイダー選択
    provider_option = st.sidebar.selectbox(
        "プロバイダーを選択",
        options=["openai", "gemini"],
        index=1,
        help="重要箇所抽出に使用するLLMプロバイダーを選択します。"
    )

    st.sidebar.markdown("### 字幕スタイル")
    font_size = st.sidebar.number_input(
        "フォントサイズ",
        min_value=8,
        max_value=120,
        value=SubtitleConstants.SUBTITLE_DEFAULT_FONT_SIZE,
        step=1,
        help="字幕のフォントサイズを指定します。"
    )
    color_options = [
        "white", "black", "yellow", "red", "blue", "green", "cyan", "magenta", "custom"
    ]
    default_font_color_index = (
        color_options.index(SubtitleConstants.SUBTITLE_DEFAULT_FONT_COLOR)
        if SubtitleConstants.SUBTITLE_DEFAULT_FONT_COLOR in color_options
        else color_options.index("custom")
    )
    font_color_choice = st.sidebar.selectbox(
        "フォント色",
        options=color_options,
        index=default_font_color_index,
        help="CSSカラー名または16進数カラー（例: #ffffff）を指定できます。"
    )
    font_color_custom = ""
    if font_color_choice == "custom":
        font_color_custom = st.sidebar.text_input(
            "フォント色（カスタム）",
            value=SubtitleConstants.SUBTITLE_DEFAULT_FONT_COLOR,
            help="例: #ffffff, #ffcc00, white"
        )
    if font_color_choice == "custom":
        font_color = font_color_custom.strip() or SubtitleConstants.SUBTITLE_DEFAULT_FONT_COLOR
    else:
        font_color = font_color_choice

    default_stroke_color_index = (
        color_options.index(SubtitleConstants.SUBTITLE_DEFAULT_STROKE_COLOR)
        if SubtitleConstants.SUBTITLE_DEFAULT_STROKE_COLOR in color_options
        else color_options.index("custom")
    )
    stroke_color_choice = st.sidebar.selectbox(
        "ストローク色",
        options=color_options,
        index=default_stroke_color_index,
        help="縁取りの色を指定します。"
    )
    stroke_color_custom = ""
    if stroke_color_choice == "custom":
        stroke_color_custom = st.sidebar.text_input(
            "ストローク色（カスタム）",
            value=SubtitleConstants.SUBTITLE_DEFAULT_STROKE_COLOR,
            help="例: #000000, black"
        )
    if stroke_color_choice == "custom":
        stroke_color = stroke_color_custom.strip() or SubtitleConstants.SUBTITLE_DEFAULT_STROKE_COLOR
    else:
        stroke_color = stroke_color_choice

    stroke_width = st.sidebar.number_input(
        "ストローク幅",
        min_value=0,
        max_value=12,
        value=SubtitleConstants.SUBTITLE_DEFAULT_STROKE_WIDTH,
        step=1,
        help="字幕の縁取りの太さを指定します。"
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
        previous_temp_path = st.session_state.get("uploaded_temp_path")
        previous_name = st.session_state.get("uploaded_name")
        previous_size = st.session_state.get("uploaded_size")
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext != ".mp4":
            st.error("⚠️ MP4形式のみ対応しています。別のファイル形式が選択されています。")
            st.stop()
        if (
            not previous_temp_path
            or previous_name != uploaded_file.name
            or previous_size != uploaded_file.size
        ):
            if previous_temp_path and os.path.exists(previous_temp_path):
                os.unlink(previous_temp_path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                st.session_state["uploaded_temp_path"] = tmp_file.name
                st.session_state["uploaded_name"] = uploaded_file.name
                st.session_state["uploaded_size"] = uploaded_file.size

        temp_filename = st.session_state.get("uploaded_temp_path")
        duration_seconds = None
        if temp_filename and os.path.exists(temp_filename):
            try:
                video_for_duration = VideoFileClip(temp_filename)
                duration_seconds = video_for_duration.duration
                video_for_duration.close()
            except Exception as e:
                st.warning(f"動画の長さ取得に失敗しました: {str(e)}")

        # ファイル情報表示
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.info(f"ファイル: {uploaded_file.name} ({file_size_mb:.2f} MB)")
        if duration_seconds is not None:
            st.info(f"動画の長さ: {_format_time(duration_seconds)}")
        
        # 音声再生機能
        st.audio(uploaded_file, format=f"audio/{uploaded_file.name.split('.')[-1]}")
        
        manual_trim = st.sidebar.checkbox(
            "尺を手動で決める",
            value=False,
            help="ONの場合は指定した開始/終了時間で切り抜きます。OFFの場合はLLMで重要箇所を抽出します。",
        )
        manual_trim_range = None
        if manual_trim:
            if duration_seconds is None:
                st.sidebar.warning("動画の長さが取得できないため、手動指定できません。")
            else:
                manual_trim_range = st.sidebar.slider(
                    "切り抜き範囲（秒）",
                    min_value=0.0,
                    max_value=float(duration_seconds),
                    value=(0.0, float(duration_seconds)),
                    step=0.1,
                )
                st.sidebar.caption(
                    f"選択範囲: {_format_time(manual_trim_range[0])} - {_format_time(manual_trim_range[1])}"
                )

        # 文字起こし実行ボタン
        transcribe_button = st.button("動画処理開始", type="primary")
        
        if transcribe_button:
            # 処理開始
            with st.spinner("動画処理中..."):
                try:
                    if not temp_filename or not os.path.exists(temp_filename):
                        raise FileNotFoundError("アップロード動画の一時ファイルが見つかりません。")

                    trim_payload = None
                    raw_response = None
                    load_start = time.time()
                    progress_text = st.empty()
                    provider_map = {
                        "openai": LLMProvider.OPENAI,
                        "gemini": LLMProvider.GEMINI,
                    }
                    llm_factory = LLMFactory(provider_map[provider_option])
                    trim_service = TrimVideoService(llm_factory)

                    if manual_trim:
                        if manual_trim_range is None:
                            st.error("手動の切り抜き範囲が取得できません。")
                            st.stop()
                        trim_start, trim_end = manual_trim_range
                        progress_text.text("手動指定の切り抜きを実行中...")
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as out_file:
                            output_video_path = out_file.name
                        logger.info(f"trim flow: output_video_path={output_video_path}")
                        trim_start, trim_end = trim_service.trim_by_range(
                            temp_filename,
                            trim_start,
                            trim_end,
                            output_video_path,
                        )
                        st.success("手動の切り抜きが完了しました。")
                    else:
                        # 重要箇所の抽出（抽象的な処理）
                        progress_text.text("重要シーンを抽出中...")
                        payload = trim_service.extract_key_segments(temp_filename)
                        logger.info(f"trim payload keys: {list(payload.keys())}")
                        st.success("トリミング範囲の抽出が完了しました。")

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
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as out_file:
                                output_video_path = out_file.name
                            logger.info(f"trim flow: output_video_path={output_video_path}")
                            trim_start, trim_end = trim_service.trim_by_segments(
                                temp_filename,
                                trim_payload,
                                output_video_path,
                            )
                        else:
                            logger.warning("trim ranges is empty or missing")
                            st.info("重要箇所が抽出されませんでした。")
                            st.stop()

                    load_end = time.time()
                    progress_text.empty()

                    # 処理時間計算
                    total_time = load_end - load_start

                    # 結果表示
                    st.markdown("### トリミング範囲")
                    st.success(f"処理完了（合計: {total_time:.2f}秒）")

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
                    translated = None
                    if translate_language_option:
                        progress_text.text("翻訳処理を開始中...")
                        translate_factory = LLMFactory(LLMProvider.GEMINI)
                        translate_service = TranslateSegmentsService(translate_factory)
                        translated = translate_service.translate(
                            segments,
                            target_language=translate_language_option,
                        )
                        segments = translated.get("segments", segments)
                        progress_text.text("翻訳処理が完了しました。")
                    logger.info(f"subtitle flow: segments_count={len(segments)}")
                    subtitle_service = AddSubtitlesService(
                        font_size=int(font_size),
                        font_color=font_color,
                        stroke_color=stroke_color,
                        stroke_width=int(stroke_width),
                    )
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as subtitle_file:
                        subtitle_output_path = subtitle_file.name
                    logger.info(f"subtitle flow: subtitle_output_path={subtitle_output_path}")
                    subtitle_language = translate_language_option or None
                    subtitle_service.add_subtitles_to_trimmed_video(
                        output_video_path,
                        segments,
                        0.0,
                        subtitle_output_path,
                        language=subtitle_language,
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
                    if trim_payload:
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
                    if translated:
                        st.text_area(
                            "翻訳レスポンス",
                            value=json.dumps(translated, ensure_ascii=False, indent=2),
                            height=240,
                        )
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")
    
    else:
        # ファイルがアップロードされていない場合の表示
        st.info("👆 音声ファイルをアップロードしてください")
        
        # サンプル説明
        with st.expander("使い方"):
            st.markdown("""
            1. 動画ファイルをアップロード
            2. 必要ならサイドバーで切り抜き範囲を指定
            3. 「動画処理開始」ボタンをクリック
            4. 結果を確認し、必要に応じてダウンロード
            """)

if __name__ == "__main__":
    main()
