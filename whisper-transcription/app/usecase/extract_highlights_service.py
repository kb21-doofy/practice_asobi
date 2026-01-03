# ここには各usecaseをimportして共通して使うクラスを作成する。
# TODO: 以下は例

# # Usecase層ではインターフェースに依存
# from domain.interface.llm_client import LLMClient

# def some_usecase(client: LLMClient):  # インターフェースに依存
#     result = client.chat_completion([...])  # プロバイダーに依存しない

# # 実際の使用
# openai_client = OpenAIClient()  # OpenAI実装
# anthropic_client = AnthropicClient()  # Anthropic実装

# # どちらも同じインターフェースで使用可能
# some_usecase(openai_client)
# some_usecase(anthropic_client)