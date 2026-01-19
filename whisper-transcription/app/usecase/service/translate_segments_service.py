"""
文字起こしセグメントの翻訳サービスクラス
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from adapter.llm_factory import LLMFactory


class TranslateSegmentsService:
    """文字起こしセグメントを指定言語へ翻訳するサービス"""

    def __init__(self, llm_factory: LLMFactory):
        self.llm_factory = llm_factory

    def translate(self, segments: List[Dict[str, Any]], target_language: str) -> Dict[str, Any]:
        """
        セグメントのtextを翻訳して返す

        Args:
            segments: 文字起こしセグメント
            target_language: 翻訳先の言語（例: "ja", "en"）
        """
        system_prompt = self._load_system_prompt()
        base_user_prompt = self._load_user_prompt()
        user_prompt = self._build_user_prompt(base_user_prompt, segments, target_language)
        json_schema = self._load_json_schema()

        llm_client = self.llm_factory.create_llm()
        response_content = llm_client.invoke(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            json_schema=json_schema,
        )
        return self._parse_llm_response(response_content)

    def _load_system_prompt(self) -> str:
        prompts_base_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_base_dir / "translate_segments" / "system_prompt.md"
        if not prompt_file.exists():
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_file}")
        return prompt_file.read_text(encoding="utf-8").strip()

    def _load_user_prompt(self) -> str:
        prompts_base_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_base_dir / "translate_segments" / "user_prompt.md"
        if not prompt_file.exists():
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_file}")
        return prompt_file.read_text(encoding="utf-8").strip()

    def _load_json_schema(self) -> Optional[dict]:
        prompts_base_dir = Path(__file__).parent.parent / "prompts"
        schema_file = prompts_base_dir / "translate_segments" / "json_schema.json"
        if not schema_file.exists():
            return None
        content = schema_file.read_text(encoding="utf-8").strip()
        if content.startswith("//"):
            return None
        return json.loads(content)

    @staticmethod
    def _build_user_prompt(
        base_prompt: str,
        segments: List[Dict[str, Any]],
        target_language: str,
    ) -> str:
        segments_json = json.dumps({"segments": segments}, ensure_ascii=False, indent=2)
        return (
            f"{base_prompt}\n"
            f"翻訳先の言語: {target_language}\n"
            "対象セグメント(JSON):\n"
            f"{segments_json}"
        )

    def _parse_llm_response(self, llm_response: str | Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(llm_response, str):
            stripped = self._strip_code_fences(llm_response).strip()
            return self._normalize_payload(json.loads(stripped))
        return self._normalize_payload(llm_response)

    @staticmethod
    def _normalize_payload(payload: Dict[str, Any] | List[Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(payload, list):
            return {"segments": payload}
        return payload

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
