from domain.entities.llm_provider import LLMProvider
from adapter.llm_client.llm_client import LLMClient
from adapter.handler.openai_handler import OpenAIHandler, OpenAIHandlerConfig
from adapter.handler.gemini_handler import GeminiHandler, GeminiHandlerConfig

class LLMFactory:
    """LLMクライアントを生成するファクトリクラス"""
    
    def __init__(self, provider: LLMProvider):
        """
        初期化
        
        Args:
            provider: LLMプロバイダー
        """
        self._provider = provider

    def create_llm(self, provider: LLMProvider | None = None) -> LLMClient:
        resolved_provider = provider if provider else self._provider

        if resolved_provider == LLMProvider.OPENAI:
            config = OpenAIHandlerConfig()
            handler = OpenAIHandler(config)
            return LLMClient(handler)
        if resolved_provider == LLMProvider.GEMINI:
            config = GeminiHandlerConfig()
            handler = GeminiHandler(config)
            return LLMClient(handler)

        raise ValueError(f"Unsupported provider: {resolved_provider}")
