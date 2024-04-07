from langchain_community.vectorstores.milvus import Milvus
from langchain_core.embeddings import Embeddings
from typing import Any,Optional,List,Callable
from concurrent.futures import ThreadPoolExecutor
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility, Partition
from langchain_core.documents import Document
executor = ThreadPoolExecutor(max_workers=10)

class CustomMilvus(Milvus):

    def __init__(
        self,
        embedding_function: Embeddings,
        collection_name: str = "LangChainCollection",
        collection_description: str = "",
        collection_properties: Optional[dict[str, Any]] = None,
        connection_args: Optional[dict[str, Any]] = None,
        consistency_level: str = "Session",
        index_params: Optional[dict] = None,
        search_params: Optional[dict] = None,
        drop_old: Optional[bool] = False,
        *,
        primary_field: str = "pk",
        text_field: str = "text",
        vector_field: str = "vector",
        metadata_field: Optional[str] = None,
        partition_key_field: Optional[str] = None,
        partition_names: Optional[list] = None,
        replica_number: int = 1,
        timeout: Optional[float] = None,
    ):
        super().__init__(embedding_function=embedding_function,
                            collection_name=collection_name,
                            collection_description=collection_description,
                            collection_properties=collection_properties,
                            connection_args=connection_args,
                            consistency_level=consistency_level,
                            index_params=index_params,
                            search_params=search_params,
                            drop_old=drop_old,
                            primary_field=primary_field,
                            text_field=text_field,
                            vector_field=vector_field,
                            metadata_field=metadata_field,
                            partition_key_field=partition_key_field,
                            partition_names=partition_names,
                            replica_number=replica_number,
                            timeout=timeout,)
        
    def query(self,params,output_fields):
        if self.col:
            return self.col.query(expr=params,output_fields=output_fields)
        
    
    def delete_collection(self):
        if self.col:
            self.col.drop()
        
    def delete_by_params(self,expr: str):
        if self.col:
            self.col.delete(expr=expr)
    
    def _select_relevance_score_fn(self) -> Callable[[float], float]:
        return self._euclidean_relevance_score_fn
    
    @staticmethod
    def _euclidean_relevance_score_fn(distance: float) -> float:
        return 1.0 - distance / 2.2
    
    # @property
    # def fields(self):
    #     fields = [
    #         FieldSchema(name='chunk_id', dtype=DataType.VARCHAR, max_length=64, is_primary=True),
    #         FieldSchema(name='file_id', dtype=DataType.VARCHAR, max_length=64),
    #         FieldSchema(name='file_name', dtype=DataType.VARCHAR, max_length=640),
    #         FieldSchema(name='file_path', dtype=DataType.VARCHAR, max_length=640),
    #         FieldSchema(name='timestamp', dtype=DataType.VARCHAR, max_length=64),
    #         FieldSchema(name='content', dtype=DataType.VARCHAR, max_length=64000),  # TODO 减小成1000
    #         FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, dim=768)
    #     ]
    #     return fields