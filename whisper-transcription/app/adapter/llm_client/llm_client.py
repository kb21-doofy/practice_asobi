from adapter.llm_client.i_llm_client import ILLMHandler
from utli.logger import get_logger
import time


class LLMClient(ILLMHandler):
    def __init__(self, llm_handler: ILLMHandler):        
        
        self._llm_handler = llm_handler
        self._logger = get_logger(__name__)
        

    def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        json_schema: dict | None = None,
    ) -> str:
        start_time = time.time()

        try:
            response = self._llm_handler.invoke(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                json_schema=json_schema,
            )

            duration = time.time() - start_time
            self._logger.info(
                f"LLM_CALL_COMPLETE: duration={duration:.3f}s\n"
                f"=== SYSTEM PROMPT ===\n{system_prompt}\n"
                f"=== USER PROMPT ===\n{user_prompt}\n"
                f"=== JSON schema ===\n{json_schema if json_schema else 'None'}\n"
                f"=== RESPONSE ===\n{response}\n"
                f"=== END LLM CALL ==="
            )
            return response

        except Exception as e:
            duration = time.time() - start_time

            error_details = (
                f"LLM_CALL_FAILED (duration={duration:.3f}s)\n"
                f"=== SYSTEM PROMPT ===\n{system_prompt}\n"
                f"=== USER PROMPT ===\n{user_prompt}\n"
                f"=== JSON schema ===\n{json_schema if json_schema else 'None'}\n"
            )

            if isinstance(e, (ConnectionError, TimeoutError)):
                raise ConnectionError(error_details) from e
            elif isinstance(e, ValueError):
                raise ValueError(error_details) from e
            else:
                raise RuntimeError(error_details) from e
    