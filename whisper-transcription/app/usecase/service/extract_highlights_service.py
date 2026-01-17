#!/usr/bin/env python3
"""
ハイライト抽出サービス
文字起こしテキストから重要なポイントを抽出するUsecase
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from adapter.llm_factory import LLMFactory
from utli.logger import get_logger

logger = get_logger(__name__)

class ExtractHighlightsService:
    """ハイライト抽出サービスクラス
    
    文字起こしテキストから重要なポイントやハイライトを抽出します。
    LLMクライアントのインターフェースに依存することで、プロバイダーに依存しない設計になっています。
    """
    
    def __init__(self, llm_factory: LLMFactory):
        """
        初期化
        
        Args:
            llm_client: LLMクライアント（インターフェースに依存）
        """
        self.llm_factory = llm_factory
    
    def extract_highlights(
        self,
        subtitle_dict: Dict[str, str]) -> Dict[str, Any]:
        
        logger.debug("ハイライト抽出処理を開始")
        
        # LLMクライアントを作成
        logger.debug("LLMクライアントを作成中")
        llm_client = self.llm_factory.create_llm()
        logger.debug("LLMクライアント作成完了")
        
        # プロンプトを読み込む
        logger.debug("プロンプトを読み込み中")
        system_prompt = self._load_system_prompt()
        user_prompt = self._load_and_format_user_prompt(subtitle_dict)
        json_schema = self._load_json_schema()
        logger.debug("プロンプト読み込み完了")
        
        # LLMを呼び出してハイライトを抽出
        try:
            logger.info("LLMを呼び出してハイライトを抽出中")
            response_content = llm_client.invoke(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,  # 一貫性のある結果のため低めの温度
                json_schema=json_schema,
            )
            logger.debug(f"LLMレスポンス受信完了（長さ: {len(response_content)}文字）")
            
            # レスポンスからハイライトを抽出
            logger.debug("レスポンスからハイライトを抽出中")
            result = {
                "highlights": self._parse_highlights(response_content),
                "summary": self._extract_summary(response_content),
                "raw_response": response_content,
            }
            logger.info(f"ハイライト抽出完了（抽出数: {len(result['highlights'])}）")
            return result
        except Exception as e:
            logger.error(f"ハイライト抽出中にエラーが発生: {str(e)}", exc_info=True)
            return {
                "highlights": [],
                "summary": "",
                "error": f"ハイライト抽出中にエラーが発生しました: {str(e)}"
            }
    
    def _load_system_prompt(self) -> str:
        """
        システムプロンプトファイルを読み込む
        
        Returns:
            プロンプトテキスト
        """
        prompts_base_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_base_dir / "extract_highlights" / "system_prompt.md"
        logger.debug(f"システムプロンプトファイルを読み込み: {prompt_file}")
        
        if not prompt_file.exists():
            logger.error(f"プロンプトファイルが見つかりません: {prompt_file}")
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_file}")
        
        with open(prompt_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            logger.debug(f"システムプロンプト読み込み完了（長さ: {len(content)}文字）")
            return content
    
    def _load_user_prompt_template(self) -> str:
        """
        ユーザープロンプトテンプレートファイルを読み込む
        
        Returns:
            プロンプトテンプレートテキスト
        """
        prompts_base_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_base_dir / "extract_highlights" / "user_prompt.md"
        logger.debug(f"ユーザープロンプトテンプレートファイルを読み込み: {prompt_file}")
        
        if not prompt_file.exists():
            logger.error(f"プロンプトファイルが見つかりません: {prompt_file}")
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_file}")
        
        with open(prompt_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            logger.debug(f"ユーザープロンプトテンプレート読み込み完了（長さ: {len(content)}文字）")
            return content
    
    def _load_and_format_user_prompt(self, subtitle_dict: Dict[str, str]) -> str:
        """
        ユーザープロンプトテンプレートを読み込んでフォーマットする
        
        Args:
            subtitle_dict: 字幕データの辞書
        
        Returns:
            フォーマット済みプロンプトテキスト
        """
        template = self._load_user_prompt_template()
        return template.format(subtitle_dict=str(subtitle_dict))
    
    def _load_json_schema(self) -> Optional[dict]:
        """
        JSONスキーマファイルを読み込む
        
        Returns:
            JSONスキーマ辞書（ファイルが存在しない場合はNone）
        """
        prompts_base_dir = Path(__file__).parent.parent / "prompts"
        schema_file = prompts_base_dir / "extract_highlights" / "json_schema.json"
        logger.debug(f"JSONスキーマファイルを読み込み: {schema_file}")
        
        if not schema_file.exists():
            logger.debug("JSONスキーマファイルが存在しないため、Noneを返します")
            return None
        
        with open(schema_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            # コメントがある場合は削除（簡易的な処理）
            if content.startswith("//"):
                logger.debug("JSONスキーマファイルがコメントのみのため、Noneを返します")
                return None
            schema = json.loads(content)
            logger.debug("JSONスキーマ読み込み完了")
            return schema
    
    def _parse_highlights(self, content: str) -> List[str]:
        """
        LLMのレスポンスからハイライトをパース
        
        Args:
            content: LLMのレスポンステキスト
        
        Returns:
            ハイライトのリスト
        """
        # 簡易実装：レスポンスをそのまま返す（後で実装）
        return [content]
    
    def _extract_summary(self, content: str) -> str:
        """
        レスポンスから要約を抽出（簡易実装）
        
        Args:
            content: LLMのレスポンステキスト
        
        Returns:
            要約テキスト
        """
        # 簡易実装：最初の数行を要約として使用
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if lines:
            return lines[0] if len(lines[0]) < 200 else lines[0][:200] + "..."
        return ""
