
from sanic.response import ResponseStream
from sanic.response import json as sanic_json
from sanic.response import text as sanic_text
from sanic import request
import uuid
import json
import asyncio
import urllib.parse
import re
from datetime import datetime
import os

from utils.general_utils import *
from knowledgebase.kb_excutor import LocalDocQA

__all__ = ["new_knowledge_base", "upload_files", "list_kbs", "list_docs", "delete_knowledge_base", "delete_docs",
           "rename_knowledge_base", "get_total_status", "clean_files_by_status", "upload_weblink", "local_doc_chat",
           "document", "get_prompt", "set_prompt"
]

INVALID_USER_ID = f"fail, Invalid user_id: . user_id 必须只含有字母，数字和下划线且字母开头"

async def new_knowledge_base(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print("new_knowledge_base %s", user_id)
    kb_name = safe_get(req, 'kb_name')
    kb_id = 'KB' + uuid.uuid4().hex
    local_doc_qa.new_knowledge_base(user_id, kb_id, kb_name)
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")
    return sanic_json({"code": 200, "msg": "success create knowledge base {}".format(kb_id),
                       "data": {"kb_id": kb_id, "kb_name": kb_name, "timestamp": timestamp}})


async def upload_weblink(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print("upload_weblink %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    url = safe_get(req, 'url')
    mode = safe_get(req, 'mode', default='soft')  # soft代表不上传同名文件，strong表示强制上传同名文件
    not_exist_kb_ids = local_doc_qa.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        msg = "invalid kb_id: {}, please check...".format(not_exist_kb_ids)
        return sanic_json({"code": 2001, "msg": msg, "data": [{}]})
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")
    exist_files = []
    if mode == 'soft':
        exist_files = local_doc_qa.check_file_exist_by_name(user_id, kb_id, [url])
    if exist_files:
        file_id, file_name, file_size, status = exist_files[0]
        msg = f'warning，当前的mode是soft，无法上传同名文件，如果想强制上传同名文件，请设置mode：strong'
        data = [{"file_id": file_id, "file_name": url, "status": status, "bytes": file_size, "timestamp": timestamp}]
    else:
        file_id, filePath = local_doc_qa.add_file(user_id, kb_id, url,url, timestamp,is_url=True)
        data = [{"file_id": file_id, "file_name": url, "status": "gray", "bytes": 0, "timestamp": timestamp}]
        asyncio.create_task(local_doc_qa.load_files(user_id,[file_id], kb_id, [url]))
        msg = "success，后台正在飞速上传文件，请耐心等待"
    return sanic_json({"code": 200, "msg": msg, "data": data})


async def set_prompt(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print("set_prompt %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    prompt = safe_get(req, 'prompt')
    not_exist_kb_ids = local_doc_qa.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        msg = "invalid kb_id: {}, please check...".format(not_exist_kb_ids)
        return sanic_json({"code": 2001, "msg": msg, "data": [{}]})
    local_doc_qa.set_prompt(user_id, kb_id, prompt)
    return sanic_json({"code": 200, "msg":  "success"})

async def get_prompt(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print("get_prompt %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    not_exist_kb_ids = local_doc_qa.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        msg = "invalid kb_id: {}, please check...".format(not_exist_kb_ids)
        return sanic_json({"code": 2001, "msg": msg, "data": [{}]})
    prompt_info = local_doc_qa.get_prompt(user_id, kb_id)
    return sanic_json({"code": 200, "msg": "success", "data": prompt_info})

async def upload_files(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print("upload_files %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    mode = safe_get(req, 'mode', default='soft')  # soft代表不上传同名文件，strong表示强制上传同名文件
    type = safe_get(req, 'type', default='auto') 
    qa_prompt = safe_get(req, 'qa_prompt', default='') 
    print("mode: %s", mode)
    use_local_file = safe_get(req, 'use_local_file', 'false')
    if use_local_file == 'true':
        files = read_files_with_extensions()
    else:
        files = req.files.getlist('files')

    not_exist_kb_ids = local_doc_qa.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        msg = "invalid kb_id: {}, please check...".format(not_exist_kb_ids)
        return sanic_json({"code": 2001, "msg": msg, "data": [{}]})

    data = []
    local_files = []
    file_names = []
    local_file_ids = []
    for file in files:
        if isinstance(file, str):
            file_name = os.path.basename(file)
        else:
            print('ori name: %s', file.name)
            file_name = urllib.parse.unquote(file.name, encoding='UTF-8')
            print('decode name: %s', file_name)
        # 删除掉全角字符
        file_name = re.sub(r'[\uFF01-\uFF5E\u3000-\u303F]', '', file_name)
        print('cleaned name: %s', file_name)
        file_name = truncate_filename(file_name)
        file_names.append(file_name)

    exist_file_names = []
    if mode == 'soft':
        exist_files = local_doc_qa.check_file_exist_by_name(user_id, kb_id, file_names)
        exist_file_names = [f[1] for f in exist_files]

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")
    for file, file_name in zip(files, file_names):
        if file_name in exist_file_names:
            continue
        file_id, file_path = local_doc_qa.add_file(user_id, kb_id, file,file_name, timestamp)
        print(f"{file_name}, {file_id}, {file_path}")
        # local_doc_qa.update_file_size(file_id, len(local_file.file_content))
        data.append(
            {"file_id": file_id, "file_name": file_name, "status": "gray", "bytes":  os.path.getsize(file_path),
             "timestamp": timestamp})
        local_files.append(file_path)
        local_file_ids.append(file_id)
        
    asyncio.create_task(local_doc_qa.load_files(user_id,local_file_ids, kb_id, local_files,type,qa_prompt))
    if exist_file_names:
        msg = f'warning，当前的mode是soft，无法上传同名文件{exist_file_names}，如果想强制上传同名文件，请设置mode：strong'
    else:
        msg = "success，后台正在飞速上传文件，请耐心等待"
    return sanic_json({"code": 200, "msg": msg, "data": data})


async def list_kbs(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print("list_kbs %s", user_id)
    kb_infos = local_doc_qa.get_knowledge_bases(user_id)
    data = []
    for kb in kb_infos:
        data.append({"kb_id": kb[0], "kb_name": kb[1]})
    print("all kb infos: {}".format(data))
    return sanic_json({"code": 200, "data": data})


async def list_docs(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print("list_docs %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    print("kb_id: {}".format(kb_id))
    data = []
    file_infos = local_doc_qa.get_files(user_id, kb_id)
    status_count = {}
    msg_map = {'gray': "正在上传中，请耐心等待",
               'red': "split或embedding失败，请检查文件类型，仅支持[md,txt,pdf,jpg,png,jpeg,docx,xlsx,pptx,eml,csv]",
               'yellow': "milvus插入失败，请稍后再试", 'green': "上传成功"}
    for file_info in file_infos:
        status = file_info[2]
        if status not in status_count:
            status_count[status] = 1
        else:
            status_count[status] += 1
        data.append({"file_id": file_info[0], "file_name": file_info[1], "status": file_info[2], "bytes": file_info[3],
                     "content_length": file_info[4], "timestamp": file_info[5], "msg": msg_map[file_info[2]]})

    return sanic_json({"code": 200, "msg": "success", "data": {'total': status_count, 'details': data}})


async def delete_knowledge_base(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print("delete_knowledge_base %s", user_id)
    kb_ids = safe_get(req, 'kb_ids')
    not_exist_kb_ids = local_doc_qa.check_kb_exist(user_id, kb_ids)
    if not_exist_kb_ids:
        return sanic_json({"code": 2003, "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids)})

    local_doc_qa.delete_knowledge_base(user_id, kb_ids)
    return sanic_json({"code": 200, "msg": "Knowledge Base {} delete success".format(kb_ids)})


async def rename_knowledge_base(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print("rename_knowledge_base %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    new_kb_name = safe_get(req, 'new_kb_name')
    not_exist_kb_ids = local_doc_qa.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        return sanic_json({"code": 2003, "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids[0])})
    local_doc_qa.rename_knowledge_base(user_id, kb_id, new_kb_name)
    return sanic_json({"code": 200, "msg": "Knowledge Base {} rename success".format(kb_id)})


async def delete_docs(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print("delete_docs %s", user_id)
    kb_id = safe_get(req, 'kb_id')
    file_ids = safe_get(req, "file_ids")
    not_exist_kb_ids = local_doc_qa.check_kb_exist(user_id, [kb_id])
    if not_exist_kb_ids:
        return sanic_json({"code": 2003, "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids[0])})
    valid_file_infos = local_doc_qa.check_file_exist(user_id, kb_id, file_ids)
    if len(valid_file_infos) == 0:
        return sanic_json({"code": 2004, "msg": "fail, files {} not found".format(file_ids)})
    local_doc_qa.delete_files(kb_id,file_ids)
    # 删除数据库中的记录
    return sanic_json({"code": 200, "msg": "documents {} delete success".format(file_ids)})


async def get_total_status(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print('get_total_status %s', user_id)
    if not user_id:
        users = local_doc_qa.get_users()
        users = [user[0] for user in users]
    else:
        users = [user_id]
    res = {}
    for user in users:
        res[user] = {}
        kbs = local_doc_qa.get_knowledge_bases(user)
        for kb_id, kb_name in kbs:
            gray_file_infos = local_doc_qa.get_file_by_status([kb_id], 'gray')
            red_file_infos = local_doc_qa.get_file_by_status([kb_id], 'red')
            yellow_file_infos = local_doc_qa.get_file_by_status([kb_id], 'yellow')
            green_file_infos = local_doc_qa.get_file_by_status([kb_id], 'green')
            res[user][kb_name + kb_id] = {'green': len(green_file_infos), 'yellow': len(yellow_file_infos),
                                          'red': len(red_file_infos),
                                          'gray': len(gray_file_infos)}

    return sanic_json({"code": 200, "status": res})


async def clean_files_by_status(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print('clean_files_by_status %s', user_id)
    status = safe_get(req, 'status', default='gray')
    kb_ids = safe_get(req, 'kb_ids')
    if not kb_ids:
        kbs = local_doc_qa.get_knowledge_bases(user_id)
        kb_ids = [kb[0] for kb in kbs]
    else:
        not_exist_kb_ids = local_doc_qa.check_kb_exist(user_id, kb_ids)
        if not_exist_kb_ids:
            return sanic_json({"code": 2003, "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids)})

    gray_file_infos = local_doc_qa.get_file_by_status(kb_ids, status)
    gray_file_ids = [f[0] for f in gray_file_infos]
    gray_file_names = [f[1] for f in gray_file_infos]
    print(f'{status} files number: {len(gray_file_names)}')
    # 删除milvus中的file
    if gray_file_ids:
        for kb_id in kb_ids:
            local_doc_qa.delete_files(kb_id, gray_file_ids)
    return sanic_json({"code": 200, "msg": f"delete {status} files success", "data": gray_file_names})


async def local_doc_chat(req: request):
    local_doc_qa: LocalDocQA = req.app.ctx.local_doc_qa
    user_id = safe_get(req, 'user_id')
    is_valid = validate_user_id(user_id)
    if not is_valid:
        return sanic_json({"code": 2005, "msg": get_invalid_user_id_msg(user_id=user_id)})
    print('local_doc_chat %s', user_id)
    kb_ids = safe_get(req, 'kb_ids')
    cur_kb_id = safe_get(req, 'cur_kb_id')
    question = safe_get(req, 'question')
    rerank = safe_get(req, 'rerank', default=True)
    print('rerank %s', rerank)
    streaming = safe_get(req, 'streaming', True)
    # streaming = False
    history = safe_get(req, 'history', [])
    print("history: %s ", history)
    print("question: %s", question)
    print("kb_ids: %s", kb_ids)
    print("user_id: %s", user_id)
    print("cur_kb_id: %s", cur_kb_id)

    not_exist_kb_ids = local_doc_qa.check_kb_exist(user_id, kb_ids)
    if not_exist_kb_ids:
        return sanic_json({"code": 2003, "msg": "fail, knowledge Base {} not found".format(not_exist_kb_ids)})

    file_infos = []
    #kb = local_doc_qa.get_knowledge_base_name(user_id, kb_ids)
    for kb_id in kb_ids:
        file_infos.extend(local_doc_qa.get_files(user_id, kb_id))
    valid_files = [fi for fi in file_infos if fi[2] == 'green']
    if len(valid_files) == 0:
        return sanic_json({"code": 200, "msg": "success chat", "question": question,
                           "response": "All knowledge bases {} are empty or haven't green file, please upload files".format(
                               kb_ids), "history": history, "source_documents": [{}]})
    else:
        print("streaming: %s", streaming)
        print("start generate answer")
        async def generate_answer(response):
            print("start generate...")
            for resp, next_history in local_doc_qa.get_knowledge_based_answer(
                    query=question, kb_ids=kb_ids,cur_kb_id=cur_kb_id,user_id = user_id, chat_history=history, streaming=streaming, rerank=rerank
            ):
                chunk_data = resp["result"]
                chunk_str = chunk_data
                if not chunk_str:
                    source_documents = []
                    for inum, doc in enumerate(resp["source_documents"]):
                        source_info = {'file_id': doc.metadata['file_id'],
                                        'file_name': doc.metadata['file_name'],
                                        'content': doc.page_content,
                                        'retrieval_query': doc.metadata['retrieval_query'],
                                        'score': str(doc.metadata['score'])}
                        source_documents.append(source_info)

                    # retrieval_documents = format_source_documents(resp["retrieval_documents"])
                    source_documents = format_source_documents(resp["source_documents"])
                    chat_data = {'user_info': user_id, 'kb_ids': kb_ids, 'query': question, 'history': history,
                                    'result': next_history[-1]['content'],
                                    'source_documents': source_documents}
                    print("chat_data: %s", chat_data)
                    print("response: %s", chat_data['result'])
                    stream_res = {
                        "code": 200,
                        "msg": "success",
                        "question": question,
                        # "response":next_history[-1][1],
                        "response": "",
                        "history": next_history,
                        "source_documents": source_documents,
                    }
                else:
                    
                    delta_answer = chunk_str
                    stream_res = {
                        "code": 200,
                        "msg": "success",
                        "question": "",
                        "response": delta_answer,
                        "history": [],
                        "source_documents": [],
                    }
                await response.write(f"data: {json.dumps(stream_res, ensure_ascii=False)}\n\n")
                if not chunk_str:
                    await response.eof()
                await asyncio.sleep(0.001)

        response_stream = ResponseStream(generate_answer, content_type='text/event-stream')
        return response_stream

        # else:
        #     for resp, history in local_doc_qa.get_knowledge_based_answer(
        #             query=question, kb_ids=kb_ids,cur_kb_id=cur_kb_id, chat_history=history, streaming=False, rerank=rerank
        #     ):
        #         pass
        #     # retrieval_documents = format_source_documents(resp["retrieval_documents"])
        #     source_documents = format_source_documents(resp["source_documents"])
        #     chat_data = {'user_id': user_id, 'kb_ids': kb_ids, 'query': question, 'history': history,
        #                    'result': resp['result'],
        #                  'source_documents': source_documents}
        #     print("chat_data: %s", chat_data)
        #     print("response: %s", chat_data['result'])
        #     return sanic_json({"code": 200, "msg": "success chat", "question": question, "response": resp["result"],
        #                        "history": history, "source_documents": source_documents})


async def document(req: request):
    description = ""
    return sanic_text(description)
