from adapter.llm_client.i_llm_client import ILLMHandler
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import logging
from config import Settings

logger = logging.getLogger(__name__)


class GeminiHandlerConfig:
    def __init__(self):
        self.model_name = Settings().GEMINI_MODEL_NAME
        self.api_key = Settings().GOOGLE_API_KEY


class GeminiHandler(ILLMHandler):
    def __init__(self, config: GeminiHandlerConfig):
        self._config = config

    def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None,
        json_schema: dict | None,
    ) -> str:
        if not self._config.model_name or not self._config.api_key:
            logger.warning("Gemini設定が不足しているため、プレースホルダーを返します。")
            return "[gemini] 未設定のため実行されませんでした。"

        llm = ChatGoogleGenerativeAI(
            model=self._config.model_name,
            google_api_key=self._config.api_key,
            temperature=temperature,
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        res = llm.invoke(
            input=messages,
        )

        if isinstance(res.content, list):
            return "\n".join([str(item) for item in res.content])
        elif isinstance(res.content, dict):
            return json.dumps(res.content)
        else:
            return res.content
