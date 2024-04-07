from langchain_core.documents import Document
from typing import List
from BCEmbedding import RerankerModel
from FlagEmbedding import FlagReranker

from config.model_config import *


def rerankDoc(query:str,docs: List[Document]):
    # 此处我们不进行reranking，仅提取所有文档的page_content
    page_contents_list = [doc.page_content for doc in docs]
    # construct sentence pairs
    sentence_pairs = [[query, passage] for passage in page_contents_list]
    # method 0: calculate scores of sentence pairs
    if rerank_type == 'bce':
        scores = bceRerank(sentence_pairs)
    elif rerank_type == 'bge':
        scores = bgeRerank(sentence_pairs)
    for doc,score in zip(docs,scores):
        doc.metadata['score'] = score
    return docs

def bceRerank(sentence_pairs):
    rankermodel = RerankerModel(model_name_or_path=rerank_modal_path )
    return rankermodel.compute_score(sentence_pairs)

def bgeRerank(sentence_pairs):
    reranker = FlagReranker(model_name_or_path=rerank_modal_path, use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation
    return reranker.compute_score(sentence_pairs)