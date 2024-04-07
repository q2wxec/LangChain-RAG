from langchain_core.runnables import Runnable
from operator import itemgetter
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import format_document
from langchain_core.runnables import  RunnablePassthrough,RunnableBranch,RunnableLambda
from langchain.llms.base import LLM
from langchain_core.retrievers import BaseRetriever
import json

from config.model_config import ANSWER_PROMPT,NO_CONTEXT_ANSWER_PROMPT,CONDENSE_QUESTION_PROMPT,CONTEXT_ANSWER_PROMPT,QA_CHUNK_PROMPT,retrive_fusion_on


def create_custom_qa_chain(llm:LLM,retriever:BaseRetriever,prompt) -> Runnable:
    with_context_prompt = PromptTemplate.from_template(prompt+"\n"+CONTEXT_ANSWER_PROMPT)
    no_context_prompt = PromptTemplate.from_template(prompt+"\n"+NO_CONTEXT_ANSWER_PROMPT)
    condense_question_prompt = PromptTemplate.from_template(CONDENSE_QUESTION_PROMPT)
    
    # chain入口，传入参数
    loaded_msg = RunnablePassthrough()
    
    # Now we retrieve the documents
    retrieved_documents = {
        "docs": itemgetter("question") | retriever,
        "question": lambda x: x["question"],
        "chat_history": itemgetter("chat_history"),
    }
    
    # Now we construct the inputs for the final prompt
    final_inputs = {
        "context": lambda x: _combine_documents(x["docs"]),
        "question": itemgetter("question"),
        "history": itemgetter("chat_history"),
    }
    # 根据上下文是否存在配置路由到不同链路
    answer_with_context = {
        "answer": final_inputs | with_context_prompt | llm,
        "docs": itemgetter("docs"),
    }
    
    answer_without_context = {
        "answer": final_inputs | no_context_prompt | llm,
        "docs": itemgetter("docs"),
    }
    
    branch = RunnableBranch(
        (lambda x: len(x["docs"])>0, answer_with_context),
        answer_without_context
    )
    
    # And now we put it all together!
    final_chain = loaded_msg | retrieved_documents | branch
    return final_chain

DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")
def _combine_documents(
    docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
):
    if len(docs) > 0:
        doc_strings = [format_document(doc, document_prompt) for doc in docs]
        return document_separator.join(doc_strings)
    else:
        # 当 docs 为空时，不设置 context 或返回 None、空字符串等默认值
        return None
    
def create_custom_chunk_chain(llm:LLM,qa_prompt:str):
    if not qa_prompt:
    # 组装prompt,根据max_token
        qa_prompt = QA_CHUNK_PROMPT
    add_chunk = '''
    文本内容如下:
    {chunk}
    '''
    qa_prompt = qa_prompt + add_chunk
    qa_prompt_template = PromptTemplate.from_template(qa_prompt)
    output_parser = StrOutputParser()

    chain = {"chunk": RunnablePassthrough()} | qa_prompt_template | llm | output_parser
    
    return chain

def get_retrieve_chain(llm:LLM,retriver):
    # chain入口，传入参数
    loaded_msg = RunnablePassthrough()
    
    expand_documents = {"expand_docs": lambda x: retriver.expand_and_merge_docs(x["question"],x["docs"])}
    if retrive_fusion_on:
        condense_question_prompt = PromptTemplate.from_template(CONDENSE_QUESTION_PROMPT)
        
        # 接聊天记录使用llm改写问题
        standalone_question = {
            "standalone_question": {
                "question": lambda x: x["question"],
                "chat_history": lambda x: x["chat_history"],
            }
            | condense_question_prompt
            | llm
            | StrOutputParser()
            | RunnableLambda(_to_list),
            "question": lambda x: x["question"]
        }
        
        retrieved_documents = {
            "docs":lambda x: _merge_documents(x["standalone_question"]+[x["question"]],retriver),
            "question": lambda x: x["question"],
        }
        
        retriev_chain = loaded_msg|standalone_question|retrieved_documents|expand_documents
    else :
        retrieved_documents = {
            "docs":lambda x: _merge_documents([x["question"]],retriver),
            "question": lambda x: x["question"],
        }
        retriev_chain = loaded_msg|retrieved_documents|expand_documents
    return retriev_chain

def _merge_documents(query_list,retriver):
    chain = RunnableLambda(retriver.retrive_by_kbs)
    results = chain.batch(query_list)
    ary = []
    for result in results:
        if result:
            ary.extend(result)
    return ary
    

def _to_list(ary_str):
    ary = []
    start_index = ary_str.find('[')
    end_index = ary_str.rfind(']')
    if start_index == -1 or end_index == -1 or end_index < start_index:
        return ary
    ary_str = ary_str[start_index:end_index + 1]
    return json.loads(ary_str)
