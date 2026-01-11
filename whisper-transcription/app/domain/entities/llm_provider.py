from enum import Enum


class LLMProvider(Enum):
    """LLMプロバイダーの列挙型"""
    OPENAI = "openai"
    