import os
import uuid
import traceback
from langchain_core.prompts import PromptTemplate
from langchain.schema import format_document

from loader import doc_loader_adaptor
from db.mysql_client import KnowledgeBaseManager as MyKbm
from db.db_client import KnowledgeBaseManager as SqlliteKbm
from config.model_config import UPLOAD_ROOT_PATH,DB_FILE_PATH,trulens_eval_on,DB_TYPE,ANSWER_PROMPT
from config.log import logger
from vector import vector_operator
import components
from chain.qa_chain import create_custom_qa_chain
from eval.trurag import tru_recorder


class LocalDocQA:
    def __init__(self):
        if DB_TYPE == 'mysql':
            self.kbm: MyKbm = MyKbm('local',logger)
        elif DB_TYPE == 'sqlite':
            self.kbm: SqlliteKbm = SqlliteKbm(DB_FILE_PATH,logger)
    def new_knowledge_base(self,user_id, kb_id, kb_name):
        self.kbm.new_vector_base(kb_id, user_id, kb_name)

    def check_kb_exist(self,user_id, kb_ids):
        return self.kbm.check_kb_exist(user_id, kb_ids)

    def check_file_exist_by_name(self,user_id, kb_id, urls):
        return self.kbm.check_file_exist_by_name(user_id, kb_id, urls)

    def add_file(self,user_id, kb_id, file,file_name, timestamp,is_url=False):
        file_id = uuid.uuid4().hex
        # 写到本地目录
        if is_url:
            file_path=file
            file_content=b''
        else:
            if isinstance(file, str):
                file_path = file
                with open(file, 'rb') as f:
                    file_content = f.read()
            else :    
                upload_path = os.path.join(UPLOAD_ROOT_PATH, user_id)
                file_dir = os.path.join(upload_path, file_id)
                os.makedirs(file_dir, exist_ok=True)
                file_path = os.path.join(file_dir, file_name)
                file_content = file.body
            with open(file_path, "wb+") as f:
                f.write(file_content)
        self.kbm.add_file(file_id, user_id, kb_id, file_name, timestamp)
        self.kbm.update_file_size(file_id, len(file_content))
        return  file_id , file_path

    def get_knowledge_bases(self,user_id):
        return  self.kbm.get_knowledge_bases(user_id)

    def get_knowledge_base_name(self,user_id,kb_ids):
        return self.kbm.get_knowledge_base_name(kb_ids)
    def get_files(self,user_id, kb_id):
        return self.kbm.get_files(user_id, kb_id)

    def delete_knowledge_base(self,user_id, kb_ids):
        # 删除vector
        for kb_id in kb_ids:
            vector_operator.delete_collection(kb_id)
        # 删除数据库记录
        self.kbm.delete_knowledge_base(user_id, kb_ids)

    def rename_knowledge_base(self,user_id, kb_id, new_kb_name):
        return self.kbm.rename_knowledge_base(user_id, kb_id, new_kb_name)

    def check_file_exist(self,user_id, kb_id, file_ids):
        return self.kbm.check_file_exist(user_id, kb_id, file_ids)

    def delete_files(self,kb_id,file_ids):
        
        vector_operator.delete_files(kb_id,file_ids)
        # 删除数据库记录
        self.kbm.delete_files(kb_id, file_ids)

    def get_users(self):
        return self.kbm.get_users()

    def get_file_by_status(self,kb_ids, status):
        return self.kbm.get_file_by_status(kb_ids, status)
    
    def get_knowledge_based_answer(self, query, kb_ids, cur_kb_id, user_id, chat_history=None, streaming: bool = False,
                                   rerank: bool = False):
        role = ''
        kb_Names = self.kbm.get_knowledge_base_name([cur_kb_id])
        prompt = self.get_prompt(user_id, cur_kb_id)
        if len(kb_Names) == 1 :
            role = kb_Names[0][2]
        if chat_history is None:
            chat_history = []
        
        retriever = components.getRetriever(kb_ids=kb_ids,chat_history=chat_history,rerank=rerank)
        #retriever = components.getVector(cur_kb_id).as_retriever()
        llm = components.getllm()
        final_chain = create_custom_qa_chain(llm=llm,retriever=retriever,prompt=prompt)
        
        # prepare inputs
        inputs = {"question": query,"chat_history":self.formate_history(chat_history=chat_history)}
        
        # prepare resp
        history = chat_history
        history.append({'type':'HUMAN','name':'user','content':query})
        final_answer = ""
        source_documents=[]
        
        if streaming and not trulens_eval_on:
            for answer_result in final_chain.stream(inputs):
                if not 'answer' in answer_result:
                    source_documents = answer_result['docs']
                    continue
                resp = answer_result['answer']
                final_answer += resp
                #prompt = answer_result.prompt
                if not resp:
                    history.append({'type':'AI','name':role,'content':final_answer})
                response = {"query": query,
                            "result": resp,
                            "source_documents": source_documents}
                yield response,history
        else:
            if trulens_eval_on:
                record = tru_recorder(final_chain,llm)
                with record as recording:
                    llm_resp = final_chain.invoke(inputs)
            else:
                llm_resp = final_chain.invoke(inputs)
            for answer_result in [llm_resp,{'answer':''}] :
                resp = answer_result['answer']
                if resp:
                    source_documents = answer_result['docs']
                    history.append({'type':'AI','name':role,'content':final_answer})
                response = {"query": query,
                                "result": resp,
                                "source_documents": source_documents}
                yield response,history
            
    def formate_history(self,chat_history):
        historyMsg = ''
        for msg in chat_history:
            historyMsg += (msg['name'] + ':' + msg['content'] + '\n')
        return historyMsg
    def generate_prompt(self, query, source_docs,role, prompt_template):
        context = "\n".join([doc.page_content for doc in source_docs])
        prompt = prompt_template.replace("{question}", query).replace("{context}", context).replace("{role}", role)
        return prompt
    
    def set_prompt(self,user_id, kb_id, prompt):
        if self.kbm.get_prompt(user_id, kb_id):
            return self.kbm.update_prompt(user_id, kb_id, prompt)
        else:
            return self.kbm.add_prompt(user_id, kb_id, prompt)
    
    def get_prompt(self,user_id, kb_id):
        prompt_info = self.kbm.get_prompt(user_id, kb_id)
        if prompt_info:
            return prompt_info[0][0]
        else:
            return ANSWER_PROMPT
    
    async def load_files(self,user_id,file_ids,kb_id, filePaths,type,qa_prompt):
        success_list = []
        failed_list = []
        for file_id,filePath in zip(file_ids,filePaths):
            try:
                docs = doc_loader_adaptor.split_file_to_docs(file_id,filePath,type,qa_prompt)
                content_length = sum([len(doc.page_content) for doc in docs])
                retriever = components.getRetriever(kb_ids=[kb_id])
                await retriever.aadd_documents(file_id,docs)
                self.kbm.update_file_status(file_id, status='green')
                success_list.append(file_id)
            except Exception as e:
                error_info = f'split error: {traceback.format_exc()}'
                logger.error(error_info)
                self.kbm.update_file_status(file_id, status='red')
                failed_list.append(file_id)
                continue
            self.kbm.update_content_length(file_id, content_length)
            
        logger.info(
            f"insert_to_vc: success num: {len(success_list)}, failed num: {len(failed_list)}")
        




