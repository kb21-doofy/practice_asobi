from domain.entities.llm_provider import LLMProvider
from adapter.llm_client.llm_client import LLMClient
from adapter.handler.openai_handler import OpenAIHandler, OpenAIHandlerConfig

class LLMFactory:
    """LLMクライアントを生成するファクトリクラス"""
    
    def __init__(self, provider: LLMProvider):
        """
        初期化
        
        Args:
            provider: LLMプロバイダー
        """
        self._provider = provider

    def create_llm(self):
        if self._provider == LLMProvider.OPENAI:
            config = OpenAIHandlerConfig()
            handler = OpenAIHandler(config)
            return LLMClient(handler)
        else:
            raise ValueError(f"Unsupported provider: {self._provider}")