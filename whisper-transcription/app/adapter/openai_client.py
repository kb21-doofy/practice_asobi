#!/usr/bin/env python3
"""
OpenAI LLMクライアント実装
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI
from domain.interface.llm_client import LLMClient
from config import Settings, Constants


class OpenAIClient(LLMClient):
    """OpenAI APIを使用したLLMクライアント実装"""
    
    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None, settings: Optional[Settings] = None):
        """
        初期化
        
        Args:
            api_key: OpenAI APIキー（Noneの場合はSettingsから取得）
            default_model: デフォルトモデル名（Noneの場合はConstants.OPENAI_DEFAULT_MODELを使用）
            settings: Settingsインスタンス（Noneの場合は新規作成）
        """
        settings = settings or Settings()
        api_key = api_key or settings.openai_api_key
        
        if not api_key:
            raise ValueError("OpenAI APIキーが設定されていません。環境変数OPENAI_API_KEYを設定するか、Settingsクラスで設定してください。")
        
        self.client = OpenAI(api_key=api_key)
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        チャット補完を実行する
        
        Args:
            messages: メッセージのリスト（roleとcontentを含む）
            model: 使用するモデル名（Noneの場合はデフォルトモデル）
            temperature: 温度パラメータ（0.0-2.0）
            max_tokens: 最大トークン数
            **kwargs: OpenAI固有の追加オプション
        
        Returns:
            レスポンス辞書（content, usage等を含む）
        """
        return self._create_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def _create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        チャット補完を実行する
        
        Args:
            messages: メッセージのリスト（roleとcontentを含む）
            model: 使用するモデル名（Noneの場合はデフォルトモデル）
            temperature: 温度パラメータ（0.0-2.0）
            max_tokens: 最大トークン数
            **kwargs: OpenAI固有の追加オプション
        
        Returns:
            レスポンス辞書（content, usage等を含む）
        """
        model = model or self.default_model
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return {
            "content": response.choices[0].message.content,
            "role": response.choices[0].message.role,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "model": response.model,
        }
 
    def get_available_models(self) -> List[str]:
        """
        利用可能なモデルの一覧を取得
        
        Returns:
            モデル名のリスト
        """
        return Constants.OPENAI_AVAILABLE_MODELS.copy()
    
    def get_default_model(self) -> str:
        """
        デフォルトモデル名を取得
        
        Returns:
            デフォルトモデル名
        """
        return Constants.OPENAI_DEFAULT_MODEL

