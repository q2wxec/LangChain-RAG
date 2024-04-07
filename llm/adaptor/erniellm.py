import erniebot
from typing import Any, List, Mapping, Optional

from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM

class ErnieLLM(LLM):
    erni_token: Optional[str] = None
    model: Optional[str] = None

    @property
    def _llm_type(self) -> str:
        return "ErnieLLM"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        erniebot.api_type = 'aistudio'
        erniebot.access_token = self.erni_token
        response = erniebot.ChatCompletion.create(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return response.get_result()

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {"erni_token": self.erni_token}