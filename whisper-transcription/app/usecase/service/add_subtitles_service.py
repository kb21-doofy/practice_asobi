"""
動画に字幕を追加するサービスクラス
"""

import os
import sys
from typing import List, Dict, Optional
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
# 実行時にはappディレクトリがsys.pathに含まれていることを前提とする
from utli.time_utils import time_to_seconds
from config import SubtitleConstants


class AddSubtitlesService:
    """動画に字幕を追加するサービスクラス"""
    
    def __init__(self, 
                 font_size: Optional[int] = None, 
                 font_color: Optional[str] = None, 
                 stroke_color: Optional[str] = None, 
                 stroke_width: Optional[int] = None):
        """
        初期化
        
        Args:
            font_size: フォントサイズ（Noneの場合はSubtitleConstants.SUBTITLE_DEFAULT_FONT_SIZEを使用）
            font_color: フォント色（Noneの場合はSubtitleConstants.SUBTITLE_DEFAULT_FONT_COLORを使用）
            stroke_color: ストローク色（Noneの場合はSubtitleConstants.SUBTITLE_DEFAULT_STROKE_COLORを使用）
            stroke_width: ストロークの太さ（Noneの場合はSubtitleConstants.SUBTITLE_DEFAULT_STROKE_WIDTHを使用）
        """
        # Noneの場合はSubtitleConstantsのデフォルト値を使用
        self.font_size = font_size if font_size is not None else SubtitleConstants.SUBTITLE_DEFAULT_FONT_SIZE
        self.font_color = font_color if font_color is not None else SubtitleConstants.SUBTITLE_DEFAULT_FONT_COLOR
        self.stroke_color = stroke_color if stroke_color is not None else SubtitleConstants.SUBTITLE_DEFAULT_STROKE_COLOR
        self.stroke_width = stroke_width if stroke_width is not None else SubtitleConstants.SUBTITLE_DEFAULT_STROKE_WIDTH
    
    def _get_font_path(self, language: Optional[str]) -> str:
        """
        macOS用のフォントパスを取得

        Args:
            language: 字幕の言語コード

        Returns:
            フォントパス
        """
        if language == "ko":
            korean_font_path = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
            if os.path.exists(korean_font_path):
                return korean_font_path
        japanese_font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
        if not os.path.exists(japanese_font_path):
            japanese_font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
        return japanese_font_path

    @staticmethod
    def _format_subtitle_text(text: str) -> str:
        target = "、"
        count = 0
        for idx, char in enumerate(text):
            if char == target:
                count += 1
                if count == 2:
                    return f"{text[:idx + 1]}\n{text[idx + 1:]}"
        return text

    @staticmethod
    def _normalize_subtitle_entries(
        entries: List[tuple[float, float, str]],
        video_duration: float,
        offset_seconds: float = 0.0,
    ) -> List[tuple[float, float, str]]:
        if not entries:
            return []
        min_start = min(start for start, _, _ in entries)
        max_end = max(end for _, end, _ in entries)
        if max_end - min_start > video_duration + 0.1:
            offset_seconds = min_start

        normalized = []
        for start, end, text in entries:
            start = max(0.0, start - offset_seconds)
            end = min(video_duration, end - offset_seconds)
            if end <= start:
                end = min(video_duration, start + 0.2)
            if end <= start:
                continue
            normalized.append((start, end, text))

        normalized.sort(key=lambda item: (item[0], item[1]))
        for idx in range(len(normalized) - 1):
            start, end, text = normalized[idx]
            next_start = normalized[idx + 1][0]
            if end > next_start:
                end = max(start, next_start)
                normalized[idx] = (start, end, text)

        return [item for item in normalized if item[1] > item[0]]
    
    def add_subtitles_to_video(
        self,
        video_path: str,
        timestamp_list: List[Dict],
        output_path: str,
        language: Optional[str] = None,
    ) -> None:
        """
        動画に字幕を追加する
        
        Args:
            video_path: 入力動画ファイルのパス
            timestamp_list: タイムスタンプ付きテキストのリスト
                各要素は {"start": "00:02:19.000", "end": "00:02:24.000", "text": "テキスト"} の形式
            output_path: 出力動画ファイルのパス
        """
        print("動画に字幕を追加中...", file=sys.stderr)
        
        video = VideoFileClip(video_path)
        
        # 字幕リストを作成（((start, end), text)の形式）
        subtitles = []
        for item in timestamp_list:
            start_seconds = time_to_seconds(item["start"])
            end_seconds = time_to_seconds(item["end"])
            text = self._format_subtitle_text(item["text"])
            subtitles.append(((start_seconds, end_seconds), text))
        
        font_path = self._get_font_path(language)
        max_width = int(video.size[0] * 0.9)
        generator = lambda txt: TextClip(
            text=txt,
            font=font_path,
            font_size=self.font_size,
            color=self.font_color,
            stroke_color=self.stroke_color,
            stroke_width=self.stroke_width,
            method="caption",
            text_align="center",
            size=(max_width, None),
        )
        
        subtitle_clips = SubtitlesClip(
            subtitles,
            make_textclip=generator
        )
        
        # with_positionで位置を指定（set_positionの代替）
        subtitle_clips = subtitle_clips.with_position(("center", "bottom"))
        
        # 動画と字幕を合成
        final_video = CompositeVideoClip(
            [video, subtitle_clips],
            size=video.size
        ).with_duration(video.duration)
        
        # 出力ファイルに書き込み
        final_video.write_videofile(
            output_path,
            fps=video.fps,
            codec='libx264',
            audio_codec='aac',
            logger=None
        )
        
        # リソースを解放
        video.close()
        final_video.close()
        
        print(f"字幕付き動画を '{output_path}' に保存しました。", file=sys.stderr)

    def add_subtitles_to_trimmed_video(
        self,
        video_path: str,
        segments: List[Dict],
        trim_start_seconds: float,
        output_path: str,
        language: Optional[str] = None,
    ) -> None:
        """
        切り抜き後の動画に字幕を追加する

        Args:
            video_path: 切り抜き済み動画ファイルのパス
            segments: LLMのセグメントリスト
                各要素は {"start_time": "00:02:19.000", "end_time": "00:02:24.000", "text": "テキスト"} の形式
            trim_start_seconds: 元動画での切り抜き開始秒
            output_path: 出力動画ファイルのパス
        """
        print("切り抜き動画に字幕を追加中...", file=sys.stderr)

        video = VideoFileClip(video_path)

        subtitles = []
        for item in segments:
            start_time = item.get("start_time")
            end_time = item.get("end_time")
            text = self._format_subtitle_text(item.get("text", ""))
            if not start_time or not end_time or not text:
                continue

            start_seconds = time_to_seconds(start_time) - trim_start_seconds
            end_seconds = time_to_seconds(end_time) - trim_start_seconds

            if end_seconds <= 0:
                continue
            subtitles.append((start_seconds, end_seconds, text))

        normalized = self._normalize_subtitle_entries(subtitles, video.duration)
        if not normalized:
            video.close()
            raise ValueError("字幕用のセグメントが空です。")
        subtitles = [((start, end), text) for start, end, text in normalized]

        font_path = self._get_font_path(language)
        max_width = int(video.size[0] * 0.9)
        generator = lambda txt: TextClip(
            text=txt,
            font=font_path,
            font_size=self.font_size,
            color=self.font_color,
            stroke_color=self.stroke_color,
            stroke_width=self.stroke_width,
            method="caption",
            text_align="center",
            size=(max_width, None),
        )

        subtitle_clips = SubtitlesClip(
            subtitles,
            make_textclip=generator
        )
        subtitle_clips = subtitle_clips.with_position(("center", "bottom"))

        final_video = CompositeVideoClip(
            [video, subtitle_clips],
            size=video.size
        ).with_duration(video.duration)

        final_video.write_videofile(
            output_path,
            fps=video.fps,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )

        video.close()
        final_video.close()
        print(f"字幕付き動画を '{output_path}' に保存しました。", file=sys.stderr)
