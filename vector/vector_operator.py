from typing import (
    Any,
    Dict,
    List,
    Optional,
)
from langchain_core.documents import Document
from langchain_community.vectorstores.chroma import Chroma

import components
from vector.adaptor.milvus_adaptor import CustomMilvus


def get_docs_by_chunkids(kb_id:str,chunk_ids):
    vector = components.getVector(kb_id)
    if isinstance(vector, Chroma):
        where = {"chunk_id": {"$in": chunk_ids}}
        result = vector.get(where=where)
        docs = result['documents']
        metadatas = result['metadatas']
        new_docs = []
        # 遍历文档内容及其对应的元数据
        for doc, metadata in zip(docs, metadatas):
            new_doc = Document(page_content=doc,metadata=metadata)
            new_docs.append(new_doc)
        return new_docs
    if isinstance(vector, CustomMilvus):
        params = "chunk_id in " + str(chunk_ids)
        result = vector.query(params,output_fields=["chunk_id","file_id", "content"])
        docs = []
        for item in result:
            doc = Document(page_content=item['content'],
                                metadata={"file_id": item['file_id'],"chunk_id":item['chunk_id']})
            docs.append(doc)
        return docs
    

def delete_files(kb_id:str,file_ids: Optional[List[str]] = None):
    vector = components.getVector(kb_id)
    if isinstance(vector, Chroma):
        where = {"file_id": {"$in": file_ids}}
        result = vector.get(where=where)
        ids = result['ids']
        if ids:
            vector.delete(ids)
    if isinstance(vector, CustomMilvus):
        params = "file_id in " + str(file_ids)
        vector.delete_by_params(params)    

async def aadd_documents(kb_id:str,documents: List[Document]) -> List[str]:
    vector = components.getVector(kb_id)
    return await vector.aadd_documents(documents)

def delete_collection(kb_id:str):
    vector = components.getVector(kb_id)
    return vector.delete_collection()

def similarity_search_with_relevance_scores(kb_id:str,query,k):
    vector = components.getVector(kb_id)
    return vector.similarity_search_with_relevance_scores(query,k)