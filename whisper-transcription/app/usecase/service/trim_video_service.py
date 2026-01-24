"""
動画の尺を調整するサービスクラス
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from moviepy import VideoFileClip
from adapter.llm_factory import LLMFactory
from utli.time_utils import time_to_seconds
from utli.logger import get_logger

logger = get_logger(__name__)


class TrimVideoService:
    """動画から重要箇所を抽出し、尺を調整するサービス"""

    def __init__(self, llm_factory: LLMFactory):
        self.llm_factory = llm_factory

    def extract_key_segments(self, video_path: str) -> Dict[str, Any]:
        """
        動画から重要箇所のtime_stampを抽出する

        Args:
            video_path: 入力動画ファイルのパス

        Returns:
            LLMレスポンス（dict）
        """
        system_prompt = self._load_system_prompt()
        user_prompt = self._load_user_prompt()
        json_schema = self._load_json_schema()

        llm_client = self.llm_factory.create_llm()
        response_content = llm_client.invoke(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            json_schema=json_schema,
            media_path=video_path,
        )
        print("重要箇所のLLMレスポンス:", response_content)
        if not response_content or not response_content.strip():
            raise ValueError("LLMレスポンスが空です。")
        payload = self._parse_llm_response(response_content)
        payload["raw_response"] = response_content
        return payload

    def trim_by_segments(
        self,
        video_path: str,
        payload: Dict[str, Any],
        output_path: str,
    ) -> tuple[float, float]:
        """
        先頭start_timeと末尾end_timeで動画を切り抜く

        Args:
            video_path: 入力動画ファイルのパス
            payload: LLMレスポンス（dict）
            output_path: 出力動画ファイルのパス
        """
        scenes = payload.get("important_scenes", [])
        if not scenes:
            raise ValueError("LLMレスポンスにimportant_scenesが含まれていません。")

        start_seconds, end_seconds = self._resolve_trim_range(scenes)

        video = VideoFileClip(video_path)
        end_seconds = min(end_seconds, video.duration)
        if end_seconds <= start_seconds:
            video.close()
            raise ValueError("切り抜き範囲が不正です。")
        trimmed = self._subclip(video, start_seconds, end_seconds)
        trimmed.write_videofile(
            output_path,
            fps=video.fps,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
        trimmed.close()
        video.close()
        return start_seconds, end_seconds

    def trim_by_range(
        self,
        video_path: str,
        start_seconds: float,
        end_seconds: float,
        output_path: str,
    ) -> tuple[float, float]:
        """
        指定した範囲で動画を切り抜く

        Args:
            video_path: 入力動画ファイルのパス
            start_seconds: 切り抜き開始秒
            end_seconds: 切り抜き終了秒
            output_path: 出力動画ファイルのパス
        """
        video = VideoFileClip(video_path)
        start_seconds = max(0.0, start_seconds)
        end_seconds = min(end_seconds, video.duration)
        if end_seconds <= start_seconds:
            video.close()
            raise ValueError("切り抜き範囲が不正です。")
        trimmed = self._subclip(video, start_seconds, end_seconds)
        trimmed.write_videofile(
            output_path,
            fps=video.fps,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
        trimmed.close()
        video.close()
        return start_seconds, end_seconds

    def _load_system_prompt(self) -> str:
        prompts_base_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_base_dir / "trim_video" / "system_prompt.md"
        if not prompt_file.exists():
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_file}")
        return prompt_file.read_text(encoding="utf-8").strip()

    def _load_user_prompt(self) -> str:
        prompts_base_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_base_dir / "trim_video" / "user_prompt.md"
        if not prompt_file.exists():
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_file}")
        return prompt_file.read_text(encoding="utf-8").strip()

    def _load_json_schema(self) -> Optional[dict]:
        prompts_base_dir = Path(__file__).parent.parent / "prompts"
        schema_file = prompts_base_dir / "trim_video" / "json_schema.json"
        if not schema_file.exists():
            return None
        content = schema_file.read_text(encoding="utf-8").strip()
        if content.startswith("//"):
            return None
        return json.loads(content)

    def _parse_llm_response(self, llm_response: str | Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(llm_response, str):
            stripped = self._strip_code_fences(llm_response).strip()
            if not stripped:
                raise ValueError("LLMレスポンスが空です。")
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                extracted = self._extract_json_block(stripped)
                if extracted:
                    try:
                        return json.loads(extracted)
                    except json.JSONDecodeError:
                        pass
                preview = stripped[:200]
                logger.warning(f"LLMレスポンスのJSON解析に失敗: {preview}")
                raise ValueError("LLMレスポンスがJSONではありません。")
        return llm_response

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            return "\n".join(lines)
        return stripped

    @staticmethod
    def _extract_json_block(text: str) -> str | None:
        match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", text)
        return match.group(0) if match else None

    def _resolve_trim_range(self, scenes: List[Dict[str, Any]]) -> tuple[float, float]:
        times = []
        for item in scenes:
            start_time = item.get("start_time")
            end_time = item.get("end_time")
            if not start_time or not end_time:
                logger.warning(f"trim range skip: missing time (start={start_time}, end={end_time})")
                continue
            start_seconds = time_to_seconds(start_time)
            end_seconds = time_to_seconds(end_time)
            logger.info(
                "trim range item: start_time=%s end_time=%s start_seconds=%.3f end_seconds=%.3f",
                start_time,
                end_time,
                start_seconds,
                end_seconds,
            )
            times.append((start_seconds, end_seconds))

        if not times:
            raise ValueError("start_time/end_timeが見つかりません。")

        start_seconds = min(start for start, _ in times)
        end_seconds = max(end for _, end in times)
        logger.info(
            "trim range summary: start_seconds=%.3f end_seconds=%.3f items=%d",
            start_seconds,
            end_seconds,
            len(times),
        )
        if end_seconds <= start_seconds:
            raise ValueError("切り抜き範囲が不正です。")

        return start_seconds, end_seconds

    def _subclip(self, video: VideoFileClip, start_seconds: float, end_seconds: float) -> VideoFileClip:
        if hasattr(video, "subclip"):
            return video.subclip(start_seconds, end_seconds)
        if hasattr(video, "subclipped"):
            return video.subclipped(start_seconds, end_seconds)
        if hasattr(video, "with_subclip"):
            return video.with_subclip(start_seconds, end_seconds)
        raise AttributeError("VideoFileClipにsubclip相当のメソッドが見つかりません。")
