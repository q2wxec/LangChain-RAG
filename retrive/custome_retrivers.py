from typing import Any,  List, Dict
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from itertools import groupby
import traceback
import tiktoken
import copy
from langdetect import detect


import components
from config.model_config import *
from config.log import logger
from rerank import rerank_excutor
from vector import vector_operator
from chain.qa_chain import get_retrieve_chain

token_window: int = 4096
max_token: int = 512
offcut_token: int = 50
truncate_len: int = 50



class ContextExpandRetriver(BaseRetriever):
    """`Milvus API` retriever."""
    rerank: bool
    chat_history: Any
    kb_ids:List[str]
    
    @classmethod
    def from_kb_ids(cls, kb_ids:List[str],chat_history=None,rerank: bool = False) -> "ContextExpandRetriver":
        """Create a new `ContextExpandRetriver` from a list of `kb_ids`."""
        return cls(kb_ids = kb_ids,chat_history = chat_history,rerank = rerank)
    
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        **kwargs: Any,
    ) -> List[Document]:
        retriev_chain = get_retrieve_chain(llm = components.getllm(),retriver = self)
        
        result = retriev_chain.invoke({"question": query,"chat_history":self.chat_history})
        
        return result['expand_docs']

    def retrive_by_kbs(self, query):
        source_documents = []
        
        for kb_id in self.kb_ids:
            query_docs = vector_operator.similarity_search_with_relevance_scores(kb_id,query,k=VECTOR_SEARCH_TOP_K)
            for doc_with_score in query_docs:
                doc = doc_with_score[0]
                score = doc_with_score[1]
                if(score>=VECTOR_SEARCH_SCORE_THRESHOLD):
                    doc.metadata['retrieval_query'] = query  # 添加查询到文档的元数据中
                    doc.metadata['score'] = score
                    doc.metadata['kb_id'] = kb_id
                    source_documents.append(doc)
        return source_documents
    
    def expand_and_merge_docs(self,query:str,source_documents:List[Document]) -> List[Document]:
        expanded_docs = []
        cand_docs = sorted(source_documents, key=lambda x: x.metadata['file_id'])
        # 按照file_id进行分组
        m_grouped = [list(group) for key, group in groupby(cand_docs, key=lambda x: x.metadata['file_id'])]
        # 对每个分组按照chunk_id进行排序
        for group in m_grouped:
            if not group:
                continue
            expanded_docs.extend(process_group(group))
        
        # 去重
        deduplicated_docs = deduplicate_documents(expanded_docs)
        retrieval_documents = sorted(deduplicated_docs, key=lambda x: x.metadata['score'],reverse=True)
        if self.rerank and len(retrieval_documents) > 1:
            print(f"use rerank, rerank docs num: {len(retrieval_documents)}")
            retrieval_documents = rerank_documents_for_local(query, retrieval_documents)
        
        source_documents = reprocess_source_documents(query=query,
                                                            source_docs=retrieval_documents,
                                                            history=self.chat_history,
                                                            prompt_template=ANSWER_PROMPT)
        return source_documents
    async def aadd_documents(self,file_id,docs):
        # 这里给每个docs片段的metadata里注入file_id
        chunk_id_counter = 0
        for doc in docs:
            doc.metadata["chunk_id"] = f'{file_id}_{chunk_id_counter}'  # 添加chunk_id到metadata
            chunk_id_counter += 1
        for kb_id in self.kb_ids:
            await vector_operator.aadd_documents(kb_id,docs)
        
def rerank_documents_for_local( query, source_documents):
    if len(query) > 300:  # tokens数量超过300时不使用local rerank
        return source_documents
    try:
        source_documents = rerank_excutor.rerankDoc(query, source_documents)
        source_documents = sorted(source_documents, key=lambda x: x.metadata['score'],reverse=True)
    except Exception as e:
        logger.error("rerank error: %s", traceback.format_exc())
        logger.warning("rerank error, use origin retrieval docs")
    return source_documents
def deduplicate_documents( source_docs):
    unique_docs = set()
    deduplicated_docs = []
    for doc in source_docs:
        if doc.page_content not in unique_docs:
            unique_docs.add(doc.page_content)
            deduplicated_docs.append(doc)
    return deduplicated_docs

def reprocess_source_documents( query: str,
                                source_docs: List[Document],
                                history: List[str],
                                prompt_template: str) -> List[Document]:
    # 组装prompt,根据max_token
    query_token_num = num_tokens_from_messages([query])
    history_token_num = num_tokens_from_messages([x for sublist in history for x in sublist])
    template_token_num = num_tokens_from_messages([prompt_template])
    limited_token_nums = token_window - max_token - offcut_token - query_token_num - history_token_num - template_token_num
    new_source_docs = []
    total_token_num = 0
    for doc in source_docs:
        doc_token_num = num_tokens_from_docs([doc])
        if total_token_num + doc_token_num <= limited_token_nums:
            new_source_docs.append(doc)
            total_token_num += doc_token_num
        else:
            remaining_token_num = limited_token_nums - total_token_num
            doc_content = doc.page_content
            doc_content_token_num = num_tokens_from_messages([doc_content])
            while doc_content_token_num > remaining_token_num:
                # Truncate the doc content to fit the remaining tokens
                if len(doc_content) > 2 * truncate_len:
                    doc_content = doc_content[truncate_len: -truncate_len]
                else:  # 如果最后不够truncate_len长度的2倍，说明不够切了，直接赋值为空
                    doc_content = ""
                    break
                doc_content_token_num = num_tokens_from_messages([doc_content])
            doc.page_content = doc_content
            new_source_docs.append(doc)
            break

    logger.info(f"limited token nums: {limited_token_nums}")
    logger.info(f"template token nums: {template_token_num}")
    logger.info(f"query token nums: {query_token_num}")
    logger.info(f"history token nums: {history_token_num}")
    logger.info(f"new_source_docs token nums: {num_tokens_from_docs(new_source_docs)}")
    return new_source_docs

def num_tokens_from_messages(message_texts,model='gpt-3.5-turbo'):
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in message_texts:
        num_tokens += len(encoding.encode(message, disallowed_special=()))
    return num_tokens

def num_tokens_from_docs(docs,model='gpt-3.5-turbo'):
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for doc in docs:
        num_tokens += len(encoding.encode(doc.page_content, disallowed_special=()))
    return num_tokens

def process_group(group):
    chunk_size=CHUNK_SIZE
    # detected_lang = detect(group[0].page_content)
    # if detected_lang != "zh" and detected_lang != "zh-cn":
    #     chunk_size=chunk_size*5
    new_cands = []
    group.sort(key=lambda x: int(x.metadata['chunk_id'].split('_')[-1]))
    id_set = set()
    file_id = group[0].metadata['file_id']
    file_name = group[0].metadata['file_name']
    retrieval_query = group[0].metadata['retrieval_query']
    kb_id = group[0].metadata['kb_id']
    
    group_scores_map = {}
    # 先找出该文件所有需要搜索的chunk_id
    cand_chunks = []
    for cand_doc in group:
        current_chunk_id = int(cand_doc.metadata['chunk_id'].split('_')[-1])
        group_scores_map[current_chunk_id] = cand_doc.metadata['score']
        for i in range(current_chunk_id - 20, current_chunk_id + 20):
            if i>= 0 :
                need_search_id = file_id + '_' + str(i)
                if need_search_id not in cand_chunks:
                    cand_chunks.append(need_search_id)
                    
    group_relative_chunks = vector_operator.get_docs_by_chunkids(kb_id,cand_chunks)
    
    group_chunk_map = {int(item.metadata['chunk_id'].split('_')[-1]): item.page_content for item in group_relative_chunks}
    group_file_chunk_num = list(group_chunk_map.keys())
    for cand_doc in group:
        current_chunk_id = int(cand_doc.metadata['chunk_id'].split('_')[-1])
        doc = copy.deepcopy(cand_doc)
        id_set.add(current_chunk_id)
        docs_len = num_tokens_from_messages([doc.page_content])
        for k in range(1, 20):
            break_flag = False
            for expand_index in [current_chunk_id + k, current_chunk_id - k]:
                if expand_index in group_file_chunk_num:
                    merge_content = group_chunk_map[expand_index]
                    if docs_len + num_tokens_from_messages([merge_content]) > chunk_size:
                        break_flag = True
                        break
                    else:
                        docs_len += num_tokens_from_messages([merge_content])
                        id_set.add(expand_index)
            if break_flag:
                break

    id_list = sorted(list(id_set))
    id_lists = seperate_list(id_list)
    for id_seq in id_lists:
        for id in id_seq:
            if id == id_seq[0]:
                doc = Document(page_content=group_chunk_map[id],
                                metadata={"score": 0, "file_id": file_id,
                                             "file_name": file_name,"retrieval_query":retrieval_query})
            else:
                doc.page_content += " " + group_chunk_map[id]
        doc_score = min([group_scores_map[id] for id in id_seq if id in group_scores_map])
        doc.metadata["score"] = doc_score
        doc.metadata["kernel"] = '|'.join([group_chunk_map[id] for id in id_seq if id in group_scores_map])
        new_cands.append(doc)
    return new_cands

def seperate_list(ls: List[int]) -> List[List[int]]:
    lists = []
    ls1 = [ls[0]]
    for i in range(1, len(ls)):
        if ls[i - 1] + 1 == ls[i]:
            ls1.append(ls[i])
        else:
            lists.append(ls1)
            ls1 = [ls[i]]
    lists.append(ls1)
    return lists

