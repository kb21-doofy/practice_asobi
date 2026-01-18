from abc import ABC, abstractmethod


class ILLMHandler(ABC):
    @abstractmethod
    def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None,
        json_schema: dict | None,
        media_path: str | None = None,
    ) -> str:
        pass
