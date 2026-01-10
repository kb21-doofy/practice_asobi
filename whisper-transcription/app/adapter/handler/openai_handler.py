from be_llm.application.i_llm_handler import ILLMHandler
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
import json
import logging
from config import Settings

logger = logging.getLogger(__name__)

class OpenAIHandlerConfig:
    def __init__(self):
        self.model_name = Settings().OPENAI_MODEL_NAME
        self.azure_endpoint = Settings().OPENAI_AZURE_ENDPOINT #TODO 不要かもしれない
        self.api_version = Settings().OPENAI_API_VERSION
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
    ) -> str:

        llm = AzureChatOpenAI(
            model=self._config.model_name,
            azure_endpoint=self._config.azure_endpoint,
            api_version=self._config.api_version,
            api_key=self._config.api_key,
            temperature=temperature,
            model_kwargs={
                **({"response_format": json_schema} if json_schema is not None else {})
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