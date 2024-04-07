from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage,AIMessage
from langchain.callbacks.streaming_stdout_final_only import FinalStreamingStdOutCallbackHandler
import json

import components
from modal.base import *

def chat(query,history,streaming):
    query.replace("{history}",'')
    messages = []
    messages.append(SystemMessage(content="You're a helpful assistant"),)
    for msg in history:
        if msg['type'] == 'AI':
            messages.append(AIMessage(content=msg['content']))
        else :
            messages.append(HumanMessage(content=msg['content']))
    messages.append(HumanMessage(content=query))
    
    chat = components.getChat()
    if streaming:
        complete_answer = ''
        for stream_resp in chat.stream(messages):
            print("stream res:", stream_resp, flush=True)
            if stream_resp:
                complete_answer += stream_resp.content
            answer_result = AnswerResult()
            answer_result.history = history
            answer_result.llm_output = {"answer": stream_resp.content}
            answer_result.prompt = query
            yield answer_result
    else:
        response = chat.invoke(messages)
        answer_result = AnswerResult()
        answer_result.llm_output = {"answer": response.content}
        answer_result.prompt = query
        yield answer_result
        
def complete(query,history,streaming):
    historyMsg = ''
    for msg in history:
        historyMsg += (msg['name'] + ':' + msg['content'] + '\n')
    reqStr = query.replace("{history}", historyMsg)
    llm = components.getllm()
    if streaming:
        complete_answer = ''
        for stream_resp in llm.stream(reqStr):
            print("stream res:", stream_resp, flush=True)
            if stream_resp:
                complete_answer += stream_resp
            answer_result = AnswerResult()
            answer_result.history = history
            answer_result.llm_output = {"answer": stream_resp}
            answer_result.prompt = query
            yield answer_result
    else:
        response = llm.invoke(reqStr)
        answer_result = AnswerResult()
        answer_result.llm_output = {"answer": response}
        answer_result.prompt = query
        yield answer_result

