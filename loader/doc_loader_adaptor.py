import os
import re

from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_community.document_loaders import UnstructuredEmailLoader
from langchain_community.document_loaders import UnstructuredPowerPointLoader
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_community.document_loaders import CSVLoader
from langchain_core.documents import Document
import os
import easyocr

from utils.general_utils import *
from config.model_config import *
from utils.loader.my_recursive_url_loader import MyRecursiveUrlLoader
from utils.splitter import ChineseTextSplitter
from utils.loader import UnstructuredPaddleImageLoader, UnstructuredPaddlePDFLoader
from utils.splitter import zh_title_enhance
from config.log import logger
from chain import qa_chain
import components

def getLoaderByUrl(url) :
     # 获取文件路径的基本名称和扩展名
    base_name, file_extension = os.path.splitext(url)
    
    # 去除可能存在的点，并将目标扩展名转换为小写以进行标准化比较
    file_extension = file_extension[1:].lower()
    if is_valid_url(url):
        return WebBaseLoader(
                web_paths=(url,),
            )
    elif file_extension == "txt":
        return TextLoader(url,autodetect_encoding = True)
    elif file_extension == "md":
        return TextLoader(url,autodetect_encoding = True)
    else:
        return None
    
def is_valid_url(url):
    # 一个基本的URL正则表达式匹配规则
    url_pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// 或 https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))

def get_ocr_result(image_path):
    reader = easyocr.Reader(['ch_sim','en']) # this needs to run only once to load the model into memory
    result = reader.readtext(image_path, detail = 0)
    return result

def split_file_to_docs(file_id,filePath,type,qa_prompt, sentence_size=SENTENCE_SIZE,
                        using_zh_title_enhance=ZH_TITLE_ENHANCE):
    if is_valid_url(filePath):
        print("load url: {}".format(filePath))
        loader = MyRecursiveUrlLoader(url=filePath)
        textsplitter = ChineseTextSplitter(pdf=False, sentence_size=sentence_size)
        docs = loader.load_and_split(text_splitter=textsplitter)
    elif filePath.lower().endswith(".md"):
        loader = UnstructuredMarkdownLoader(filePath, autodetect_encoding=True)
        texts_splitter = ChineseTextSplitter(pdf=False, sentence_size=sentence_size)
        docs = loader.load_and_split(texts_splitter)
    elif filePath.lower().endswith(".txt"):
        loader = TextLoader(filePath, autodetect_encoding=True)
        texts_splitter = ChineseTextSplitter(pdf=False, sentence_size=sentence_size)
        docs = loader.load_and_split(texts_splitter)
    elif filePath.lower().endswith(".pdf"):
        loader = UnstructuredPaddlePDFLoader(filePath, get_ocr_result)
        texts_splitter = ChineseTextSplitter(pdf=True, sentence_size=sentence_size)
        docs = loader.load_and_split(texts_splitter)
    elif filePath.lower().endswith(".jpg") or filePath.lower().endswith(
            ".png") or filePath.lower().endswith(".jpeg"):
        loader = UnstructuredPaddleImageLoader(filePath, get_ocr_result, mode="elements")
        texts_splitter = ChineseTextSplitter(pdf=False, sentence_size=sentence_size)
        docs = loader.load_and_split(text_splitter=texts_splitter)
    elif filePath.lower().endswith(".docx"):
        loader = UnstructuredWordDocumentLoader(filePath, mode="elements")
        texts_splitter = ChineseTextSplitter(pdf=False, sentence_size=sentence_size)
        docs = loader.load_and_split(texts_splitter)
    elif filePath.lower().endswith(".xlsx"):
        loader = UnstructuredExcelLoader(filePath, mode="elements")
        docs = loader.load()
    elif filePath.lower().endswith(".pptx"):
        loader = UnstructuredPowerPointLoader(filePath, mode="elements")
        docs = loader.load()
    elif filePath.lower().endswith(".eml"):
        loader = UnstructuredEmailLoader(filePath, mode="elements")
        docs = loader.load()
    elif filePath.lower().endswith(".csv"):
        loader = CSVLoader(filePath,autodetect_encoding=True)
        docs = loader.load()
    else:
        raise TypeError("文件类型不支持，目前仅支持：[md,txt,pdf,jpg,png,jpeg,docx,xlsx,pptx,eml,csv]")
    if using_zh_title_enhance:
        logger.info("using_zh_title_enhance %s", using_zh_title_enhance)
        docs = zh_title_enhance(docs)
        
    if type == 'qa':
        if filePath.lower().endswith(".csv"):
            docs = merge_docs(docs)
        # 将原文内容基于qa提示词进行内容转换
        transfer_doc_by_qa_prompt(docs,qa_prompt)

    # 这里给每个docs片段的metadata里注入file_id
    for doc in docs:
        doc.metadata["file_id"] = file_id
        doc.metadata["file_name"] = filePath if is_valid_url(filePath) else os.path.split(filePath)[-1]
        for key,value in doc.metadata.items():
            if not isinstance(value, (str, int, float, bool)):
                doc.metadata[key] = str(value)
    if not is_valid_url(filePath):
        write_check_file(filePath, docs)
    if docs:
        logger.info('langchain analysis content head: %s', docs[0].page_content[:100])
    else:
        logger.info('langchain analysis docs is empty!')
    return docs

def merge_docs(docs, group_size=100):
    # 按照每100个文档进行分组
    grouped_docs = [docs[i:i + group_size] for i in range(0, len(docs), group_size)]
    
    merged_docs = []
    
    for group in grouped_docs:
        # 合并每个分组内所有文档的page_content
        merged_page_content = "\n".join([doc.page_content for doc in group])
        # 创建一个新的文档对象（这里假设有一个构造函数来创建文档）
        # 注意：这里的构造函数取决于原始docs中doc的具体类型和结构
        new_doc = Document(page_content=merged_page_content)
        
        merged_docs.append(new_doc)
    
    return merged_docs

def transfer_doc_by_qa_prompt(docs,qa_prompt):
    chain = qa_chain.create_custom_chunk_chain(llm=components.getllm(),qa_prompt=qa_prompt)
    for doc in docs:
        chunk = doc.page_content
        qa = chain.invoke(chunk)
        doc.page_content = qa
        # doc.metadata["original"] = chunk
    return docs