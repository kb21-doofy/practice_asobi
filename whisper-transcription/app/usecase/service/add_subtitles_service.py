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
    
    def _get_japanese_font_path(self) -> str:
        """
        macOS用の日本語フォントパスを取得
        
        Returns:
            フォントパス
        """
        japanese_font_path = '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc'
        if not os.path.exists(japanese_font_path):
            # フォールバック: 他のHiraginoフォントを試す
            japanese_font_path = '/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc'
        return japanese_font_path
    
    def add_subtitles_to_video(self, video_path: str, timestamp_list: List[Dict], output_path: str) -> None:
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
            text = item["text"]
            subtitles.append(((start_seconds, end_seconds), text))
        
        # 字幕クリップを作成（日本語対応フォントを使用）
        japanese_font_path = self._get_japanese_font_path()
        
        generator = lambda txt: TextClip(
            text=txt,
            font=japanese_font_path,
            font_size=self.font_size,
            color=self.font_color,
            stroke_color=self.stroke_color,
            stroke_width=self.stroke_width
        )
        
        subtitle_clips = SubtitlesClip(
            subtitles,
            make_textclip=generator
        )
        
        # with_positionで位置を指定（set_positionの代替）
        subtitle_clips = subtitle_clips.with_position(('center', 'bottom'))
        
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
            text = item.get("text", "")
            if not start_time or not end_time or not text:
                continue

            start_seconds = time_to_seconds(start_time) - trim_start_seconds
            end_seconds = time_to_seconds(end_time) - trim_start_seconds

            if end_seconds <= 0:
                continue

            start_seconds = max(0.0, start_seconds)
            end_seconds = min(video.duration, end_seconds)
            if end_seconds <= start_seconds:
                continue

            subtitles.append(((start_seconds, end_seconds), text))

        if not subtitles:
            video.close()
            raise ValueError("字幕用のセグメントが空です。")

        japanese_font_path = self._get_japanese_font_path()
        generator = lambda txt: TextClip(
            text=txt,
            font=japanese_font_path,
            font_size=self.font_size,
            color=self.font_color,
            stroke_color=self.stroke_color,
            stroke_width=self.stroke_width
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
