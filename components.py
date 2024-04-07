from llm import llm_adaptor
from embedding import embedding_adaptor
from vector import vector_adaptor
from config.model_config import *
from retrive.custome_retrivers import ContextExpandRetriver

from langchain.llms.base import LLM
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_core.retrievers import BaseRetriever
from typing import  List


def getllm()->LLM:
    return llm_adaptor.getLLM(type= llm_type,model=llm_model)

def getChat()->BaseChatModel:
    return llm_adaptor.getChat(type= llm_type,model=llm_model)

def getEmbedding()->Embeddings:
    return embedding_adaptor.getEmbedding(type= embedding_type,model=emmbedding_modal_path)

def getVector(kb_id)->VectorStore:
    return vector_adaptor.getVector(type= vector_type,embeddings=getEmbedding(),collection_name=kb_id,url=KB_ROOT_PATH)

def getRetriever(kb_ids:List[str],chat_history=None,rerank: bool = False)->BaseRetriever:
    return ContextExpandRetriver.from_kb_ids(kb_ids=kb_ids,chat_history=chat_history,rerank=rerank)