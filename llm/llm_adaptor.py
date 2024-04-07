from langchain_openai import OpenAI,ChatOpenAI
from langchain_community.chat_models import QianfanChatEndpoint 
from langchain_community.llms.tongyi import Tongyi
from langchain_community.llms.baidu_qianfan_endpoint import QianfanLLMEndpoint
from langchain_community.chat_models import QianfanChatEndpoint,ChatTongyi
from langchain_google_genai import GoogleGenerativeAI,ChatGoogleGenerativeAI
from langchain.llms.base import LLM
from langchain_core.language_models.chat_models import BaseChatModel

from llm.adaptor.erniellm import ErnieLLM
from llm.adaptor.sparkllm import SparkLLM
from llm.adaptor.sense_nova import SenseNovaLLM
from llm.adaptor.chat2llm import Chat2LLM
import os
import configparser
from config.model_config import api_key,api_url,qf_ak,qf_sk,erni_token,xh_app_id,xh_api_secret,xh_api_key,google_api_key,ty_llm_api_key,st_ak,st_sk

config = configparser.ConfigParser()

BASE_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))

config.read(os.path.join(BASE_DIR,'config.ini'))


# 大模型定义


def getLLM(type,model,token = '0')->LLM:
    if type == "openai":
        #return OpenAI(model_name=model,openai_api_key=api_key,openai_api_base=api_url,temperature=0.0)
        return Chat2LLM(chat = getChat(type,model,token))
    elif type == "qianfan":
        return QianfanLLMEndpoint(qianfan_ak=qf_ak,qianfan_sk=qf_sk,model=model)
    elif type == "erniebot":
        return ErnieLLM(erni_token=token,model=model)
    elif type == "spark":
        return SparkLLM(appid=xh_app_id,api_secret=xh_api_secret,api_key=xh_api_key,model=model)
    elif type == "tongyi":
        return Tongyi(dashscope_api_key = ty_llm_api_key,model_name=model)
    elif type == "genai":
        return GoogleGenerativeAI(model=model, google_api_key=google_api_key)
    elif type == 'sense':
        return SenseNovaLLM(st_ak=st_ak,st_sk=st_sk,model=model)   
def getChat(type,model,token = '0')->BaseChatModel:
    if type == "openai":
        return ChatOpenAI(model_name=model,openai_api_key=api_key,openai_api_base=api_url,temperature=0.0)
    elif type == "qianfan":
        return QianfanChatEndpoint(qianfan_ak=qf_ak,qianfan_sk=qf_sk,model=model)
    elif type == "tongyi":
        return ChatTongyi(dashscope_api_key = ty_llm_api_key,model_name=model)
    elif type == "genai":
        return ChatGoogleGenerativeAI(model=model, google_api_key=google_api_key, convert_system_message_to_human=True)
