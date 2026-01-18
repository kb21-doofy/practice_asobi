from adapter.llm_client.i_llm_client import ILLMHandler
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
import logging
from config import Settings

logger = logging.getLogger(__name__)

class OpenAIHandlerConfig:
    def __init__(self):
        self.model_name = Settings().OPENAI_MODEL_NAME
        self.api_key = Settings().OPENAI_API_KEY

class OpenAIHandler(ILLMHandler):
    def __init__(self, config: OpenAIHandlerConfig):
        self._config = config

    def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None,
        json_schema: dict | None,
        media_path: str | None = None,
    ) -> str:
        
        # response_formatを適切な形式に変換
        response_format = None
        if json_schema is not None:
            # OpenAI APIのresponse_format形式に変換
            # {"type": "json_schema", "json_schema": {"name": "...", "schema": {...}, "strict": True}}
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response_schema",
                    "schema": json_schema,
                    "strict": True
                }
            }
        
        llm = ChatOpenAI(
            model=self._config.model_name,
            api_key=self._config.api_key,
            temperature=temperature,
            model_kwargs={
                **({"response_format": response_format} if response_format is not None else {})
            },
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
