from langchain_community.embeddings import DashScopeEmbeddings
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

from config.model_config import *
from embedding.adaptor.nova_embedding import NovaEmbeddings

def getEmbedding(type,model)->Embeddings:
    if type == "tongyi":
        return DashScopeEmbeddings(model=model, dashscope_api_key=ty_api_key)
    elif type == "huggingface":
        return HuggingFaceEmbeddings(model_name=model)
    elif type == "st":
        return NovaEmbeddings(st_ak=st_ak,st_sk=st_sk)




