#!/usr/bin/env python3
"""
LLMクライアントのインターフェース定義
複数のLLMプロバイダー（OpenAI、Anthropic、Google等）に対応するための抽象クラス
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class LLMClient(ABC):
    """LLMクライアントのインターフェース"""
    
    @abstractmethod
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
            **kwargs: プロバイダー固有の追加オプション
        
        Returns:
            レスポンス辞書（content, usage等を含む）
        """
        pass
    
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        利用可能なモデルの一覧を取得
        
        Returns:
            モデル名のリスト
        """
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """
        デフォルトモデル名を取得
        
        Returns:
            デフォルトモデル名
        """
        pass

