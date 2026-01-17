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

    def extract_key_segments(
        self,
        mp4_path: str,
        user_prompt_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        重要箇所を抽出する

        Args:
            mp4_path: MP4ファイルのパス

        Returns:
            重要箇所のリスト（text, time_stampを含む）
        """
        logger.info(f"ExtractKeySegmentsService started: mp4_path={mp4_path}")
        segments = []
        system_prompt = self._load_system_prompt()
        user_prompt = self._load_and_format_user_prompt(
            mp4_path,
            segments,
            user_prompt_text=user_prompt_text,
        )
        json_schema = self._load_json_schema()
        logger.debug(
            "Prompt prepared: "
            f"system_len={len(system_prompt)}, user_len={len(user_prompt)}, "
            f"schema_keys={list(json_schema.keys()) if json_schema else 'None'}"
        )

        try:
            llm_client = self.llm_factory.create_llm()
            logger.info("LLM invoke start")
            response_content = llm_client.invoke(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                json_schema=json_schema,
            )
            response_length = len(response_content) if response_content else 0
            logger.info(f"LLM invoke complete: response_length={response_length}")
            logger.debug(f"LLM response content: {response_content}")
            if response_length == 0:
                logger.warning("LLM response is empty")
                return []
            return [{"raw_response": response_content}]
        except Exception as e:
            logger.warning(f"重要箇所抽出に失敗: {str(e)}")
            return []

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
        user_prompt_text: Optional[str] = None,
    ) -> str:
        template = user_prompt_text if user_prompt_text else self._load_user_prompt_template()
        return template.format(
            temp_filename=mp4_path,
            segments=segments,
        )

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
        logger.debug(f"_parse_segments input length={len(content) if content else 0}")
        if not content:
            logger.warning("_parse_segments received empty content")
            return []
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.warning(f"LLM response JSON parse failed: {exc}")
            return []

        results = []
        segments = payload.get("segments", [])
        logger.debug(f"_parse_segments raw segments count={len(segments)}")
        for item in segments:
            if "text" not in item:
                logger.debug(f"_parse_segments skip (missing text): {item}")
                continue
            start_time = item.get("start_time")
            end_time = item.get("end_time")
            if not start_time or not end_time:
                start_time, end_time = self._split_time_stamp(item.get("time_stamp", ""))
            if not start_time or not end_time:
                logger.debug(f"_parse_segments skip (missing time): {item}")
                continue
            results.append({
                "text": item["text"],
                "start_time": self._normalize_time(start_time),
                "end_time": self._normalize_time(end_time),
            })
        logger.debug(f"_parse_segments parsed count={len(results)}")
        return results

    @staticmethod
    def _format_time(seconds: float) -> str:
        """時間をフォーマット (HH:MM:SS.ms)"""
        return str(datetime.utcfromtimestamp(seconds).strftime("%H:%M:%S.%f"))[:-3]

    @staticmethod
    def _split_time_stamp(time_stamp: str) -> tuple[str, str]:
        if " --> " not in time_stamp:
            return "", ""
        parts = time_stamp.split(" --> ", 1)
        return parts[0].strip(), parts[1].strip()

    def _normalize_time(self, value: Any) -> str:
        """HH:MM:SS.mmmに正規化する"""
        if isinstance(value, (int, float)):
            return self._format_time(float(value))
        if isinstance(value, str):
            stripped = value.strip()
            try:
                return self._format_time(float(stripped))
            except ValueError:
                return stripped
        return ""
