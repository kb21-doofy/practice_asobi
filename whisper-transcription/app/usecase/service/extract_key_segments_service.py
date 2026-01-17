#!/usr/bin/env python3
"""
重要箇所抽出サービス
文字起こしセグメントから重要な箇所を抽出する（抽象的な処理）
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
from adapter.llm_factory import LLMFactory
from utli.logger import get_logger

logger = get_logger(__name__)


class ExtractKeySegmentsService:
    """重要箇所抽出サービスクラス（抽象的な処理）"""

    def __init__(self, llm_factory: LLMFactory):
        """
        初期化

        Args:
            llm_factory: LLMクライアントを生成するファクトリ
        """
        self.llm_factory = llm_factory

    def extract_key_segments(self, mp4_path: str) -> List[Dict[str, Any]]:
        """
        重要箇所を抽出する

        Args:
            mp4_path: MP4ファイルのパス

        Returns:
            重要箇所のリスト（text, time_stampを含む）
        """
        segments = self._build_placeholder_segments()
        system_prompt = self._load_system_prompt()
        user_prompt = self._load_and_format_user_prompt(mp4_path, segments)
        json_schema = self._load_json_schema()

        try:
            llm_client = self.llm_factory.create_llm()
            response_content = llm_client.invoke(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                json_schema=json_schema,
            )
            return self._parse_segments(response_content)
        except Exception as e:
            logger.warning(f"重要箇所抽出に失敗: {str(e)}")
            return self._fallback_segments(segments)

    def _load_system_prompt(self) -> str:
        prompts_base_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_base_dir / "extract_key_segments" / "system_prompt.md"
        if not prompt_file.exists():
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_file}")
        return prompt_file.read_text(encoding="utf-8").strip()

    def _load_user_prompt_template(self) -> str:
        prompts_base_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_base_dir / "extract_key_segments" / "user_prompt.md"
        if not prompt_file.exists():
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_file}")
        return prompt_file.read_text(encoding="utf-8").strip()

    def _load_and_format_user_prompt(
        self,
        mp4_path: str,
        segments: List[Dict[str, Any]],
    ) -> str:
        template = self._load_user_prompt_template()
        return template.format(mp4_path=mp4_path, segments=segments)

    def _load_json_schema(self) -> Optional[dict]:
        prompts_base_dir = Path(__file__).parent.parent / "prompts"
        schema_file = prompts_base_dir / "extract_key_segments" / "json_schema.json"
        if not schema_file.exists():
            return None
        content = schema_file.read_text(encoding="utf-8").strip()
        if content.startswith("//"):
            return None
        return json.loads(content)

    def _parse_segments(self, content: str) -> List[Dict[str, Any]]:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return []

        results = []
        for item in payload.get("segments", []):
            if "text" not in item or "time_stamp" not in item:
                continue
            results.append({
                "text": item["text"],
                "time_stamp": item["time_stamp"],
            })
        return results

    def _fallback_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        selected_segments = segments[:3]
        results = []

        for segment in selected_segments:
            start_formatted = self._format_time(segment["start"])
            end_formatted = self._format_time(segment["end"])
            results.append({
                "text": segment["text"],
                "time_stamp": f"{start_formatted} --> {end_formatted}",
                "start": segment["start"],
                "end": segment["end"],
            })
        return results

    def _build_placeholder_segments(self) -> List[Dict[str, Any]]:
        """MP4入力向けの仮セグメントを作成"""
        return [
            {
                "start": 0.0,
                "end": 1.0,
                "text": "[placeholder] 文字起こしは未実装です。",
            }
        ]

    @staticmethod
    def _format_time(seconds: float) -> str:
        """時間をフォーマット (HH:MM:SS.ms)"""
        return str(datetime.utcfromtimestamp(seconds).strftime("%H:%M:%S.%f"))[:-3]
