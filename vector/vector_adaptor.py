from langchain_community.vectorstores.chroma import Chroma
from langchain_community.vectorstores.dashvector import DashVector
from langchain_community.vectorstores.milvus import Milvus
import dashvector
from langchain_core.embeddings import Embeddings

from vector.adaptor.milvus_adaptor import CustomMilvus

def getVector(type:str,embeddings:Embeddings,collection_name:str,url):
    if type == "chroma":
        return Chroma(collection_name = collection_name, 
                      embedding_function=embeddings,
                      persist_directory=url,
                      collection_metadata={'hnsw:space':'cosine'})
    if type == "dashvector":
        client = dashvector.Client(api_key="***")
        client.create(collection_name, dimension=1024)
        collection = client.get(collection_name)
        return DashVector(collection, embeddings.embed_query)
    if type == "milvus":
        return CustomMilvus(
            embeddings,
            connection_args={"host": "127.0.0.1", "port": "19530"},
            collection_name=collection_name,
            text_field = "content",)