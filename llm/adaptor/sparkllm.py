from llm.adaptor import SparkApi
from typing import Any, List, Mapping, Optional

from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM

#用于配置大模型版本，默认“general/generalv2”
# domain = "general"   # v1.5版本
#domain = "generalv2"    # v2.0版本
#domain = "generalv3"    # v3.0版本
#云端环境的服务地址
# Spark_url = "ws://spark-api.xf-yun.com/v1.1/chat"  # v1.5环境的地址
#Spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"  # v2.0环境的地址
#Spark_url = "ws://spark-api.xf-yun.com/v3.1/chat"  # v3.0环境的地址
modal_dict={"general":"ws://spark-api.xf-yun.com/v1.1/chat",
            "generalv2":"ws://spark-api.xf-yun.com/v2.1/chat",
            "generalv3":"ws://spark-api.xf-yun.com/v3.1/chat"
            }


def getText(role,content):
    text =[]
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    text.append(jsoncon)
    return text

class SparkLLM(LLM):
    appid: Optional[str] = None
    api_secret: Optional[str] = None
    api_key: Optional[str] = None
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
        Spark_url = modal_dict[self.model]
        domain = self.model
        question = getText("user",prompt)
        SparkApi.answer = ""
        SparkApi.main(self.appid,self.api_key,self.api_secret,Spark_url,domain,question)
        return SparkApi.answer

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {"appid": self.appid}