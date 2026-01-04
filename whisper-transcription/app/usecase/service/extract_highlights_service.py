#!/usr/bin/env python3
"""
ハイライト抽出サービス
文字起こしテキストから重要なポイントを抽出するUsecase
"""

from typing import List, Dict, Any, Optional
from domain.interface.llm_client import LLMClient


class ExtractHighlightsService:
    """ハイライト抽出サービスクラス
    
    文字起こしテキストから重要なポイントやハイライトを抽出します。
    LLMクライアントのインターフェースに依存することで、プロバイダーに依存しない設計になっています。
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        初期化
        
        Args:
            llm_client: LLMクライアント（インターフェースに依存）
        """
        self.llm_client = llm_client
    
    def extract_highlights(
        self,
        transcription_text: str,
        max_highlights: int = 5,
        language: str = "ja"
    ) -> Dict[str, Any]:
        """
        文字起こしテキストからハイライトを抽出する
        
        Args:
            transcription_text: 文字起こしテキスト
            max_highlights: 抽出するハイライトの最大数（デフォルト: 5）
            language: 言語（デフォルト: "ja"）
        
        Returns:
            ハイライト抽出結果の辞書
        """
        if not transcription_text or not transcription_text.strip():
            return {
                "highlights": [],
                "summary": "",
                "error": "テキストが空です"
            }
        
        # プロンプトの作成
        prompt = self._create_prompt(transcription_text, max_highlights, language)
        
        # LLMクライアントを使用してハイライトを抽出
        messages = [
            {"role": "system", "content": "あなたは文字起こしテキストから重要なポイントを抽出する専門家です。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm_client.chat_completion(
                messages=messages,
                temperature=0.3,  # 一貫性のある結果のため低めの温度
                max_tokens=1000
            )
            
            # レスポンスからハイライトを抽出
            content = response.get("content", "")
            
            return {
                "highlights": self._parse_highlights(content),
                "summary": self._extract_summary(content),
                "raw_response": content,
                "usage": response.get("usage", {})
            }
        except Exception as e:
            return {
                "highlights": [],
                "summary": "",
                "error": f"ハイライト抽出中にエラーが発生しました: {str(e)}"
            }
    
    def _create_prompt(self, text: str, max_highlights: int, language: str) -> str:
        """
        ハイライト抽出用のプロンプトを作成
        
        Args:
            text: 文字起こしテキスト
            max_highlights: 抽出するハイライトの最大数
            language: 言語
        
        Returns:
            プロンプトテキスト
        """
        lang_instruction = "日本語で" if language == "ja" else "in English"
        
        prompt = f"""以下の文字起こしテキストから、重要なポイントを{max_highlights}個抽出してください。
{lang_instruction}で回答してください。

【文字起こしテキスト】
{text}

【出力形式】
- 各ハイライトを箇条書きで記載
- 簡潔で明確な表現を使用
- 重要な情報を優先的に抽出

【出力例】
1. [ハイライト1]
2. [ハイライト2]
...
"""
        return prompt
    
    def _parse_highlights(self, content: str) -> List[str]:
        """
        LLMのレスポンスからハイライトをパース
        
        Args:
            content: LLMのレスポンステキスト
        
        Returns:
            ハイライトのリスト
        """
        highlights = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 番号付きリストや箇条書きを抽出
            # "1. ", "- ", "・" などの形式に対応
            if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                highlight = line.split('.', 1)[1].strip() if '.' in line else line
                if highlight:
                    highlights.append(highlight)
            elif line.startswith(('- ', '・', '* ')):
                highlight = line[2:].strip() if len(line) > 2 else line[1:].strip()
                if highlight:
                    highlights.append(highlight)
            elif line and not line.startswith('【') and not line.startswith('['):
                # その他の行もハイライトとして追加（簡易的な処理）
                highlights.append(line)
        
        return highlights[:10]  # 最大10個まで
    
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
