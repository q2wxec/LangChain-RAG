import os
import configparser
import ast

config = configparser.ConfigParser()


BASE_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
UPLOAD_ROOT_PATH=os.path.join(BASE_DIR, "temp/upload")
DB_FILE_PATH=os.path.join(BASE_DIR, "temp/db/sqlite.db")
EVAL_DB_FILE_PATH=os.path.join(BASE_DIR, "temp\eval\sqlite.db")

config.read(os.path.join(BASE_DIR,'config.ini'))

ty_api_key = config.get('embedding','ty_api_key',fallback=None)

st_ak = config.get('llm','st_ak',fallback=None)

st_sk = config.get('llm','st_sk',fallback=None)

llm_type =  config.get('server','llm_type')

llm_model= config.get('server','llm_model')

vector_type =  config.get('server','vector_type')

rerank_type =  config.get('server','rerank_type')

rerank_modal_path = config.get('server',rerank_type+'_'+'rerank_modal_path')

emmbedding_modal_path = config.get('server','emmbedding_modal_path')

embedding_type = config.get('embedding','embedding_type')


trulens_eval_on = ast.literal_eval(config.get('eval','trulens_eval_on'))

retrive_fusion_on = ast.literal_eval(config.get('retrive','retrive_fusion_on'))

api_key = config.get('llm','api_key',fallback=None)

api_url = config.get('llm','api_url',fallback=None)

qf_ak = config.get('llm','qf_ak',fallback=None)

qf_sk = config.get('llm','qf_sk',fallback=None)

erni_token = config.get('llm','erni_token',fallback=None)

xh_app_id = config.get('llm','xh_app_id',fallback=None)

xh_api_secret = config.get('llm','xh_api_secret',fallback=None)

xh_api_key = config.get('llm','xh_api_key',fallback=None)

google_api_key = config.get('llm','google_api_key',fallback=None)

ty_llm_api_key = config.get('llm','ty_api_key',fallback=None)

st_ak = config.get('llm','st_ak',fallback=None)

st_sk = config.get('llm','st_sk',fallback=None)


# 知识库默认存储路径
KB_ROOT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp/knowledge_base")


with open(BASE_DIR+'/prompt/default.prompt', 'r',encoding='utf-8') as f:
    ANSWER_PROMPT = f.read()

with open(BASE_DIR+'/prompt/nocontext.prompt', 'r',encoding='utf-8') as f:
    NO_CONTEXT_ANSWER_PROMPT = f.read()
    
with open(BASE_DIR+'/prompt/context.prompt', 'r',encoding='utf-8') as f:
    CONTEXT_ANSWER_PROMPT = f.read()
    
with open(BASE_DIR+'/prompt/condense_question.prompt', 'r',encoding='utf-8') as f:
    CONDENSE_QUESTION_PROMPT = f.read()
    
with open(BASE_DIR+'/prompt/qa-chunk.prompt', 'r',encoding='utf-8') as f:
    QA_CHUNK_PROMPT = f.read()

# 文本分句长度
SENTENCE_SIZE = 30

# 匹配后单段上下文长度
CHUNK_SIZE = 100

# 传入LLM的历史记录长度
LLM_HISTORY_LEN = 3

# 知识库检索时返回的匹配内容条数
VECTOR_SEARCH_TOP_K = 10

# 知识检索内容相关度 Score, 如果为0，则不生效
VECTOR_SEARCH_SCORE_THRESHOLD = 0.5



# 是否开启中文标题加强，以及标题增强的相关配置
# 通过增加标题判断，判断哪些文本为标题，并在metadata中进行标记；
# 然后将文本与往上一级的标题进行拼合，实现文本信息的增强。
ZH_TITLE_ENHANCE = False

DB_TYPE=config.get('db','type')
# 数据库
MYSQL_DATABASE='kbm'
MYSQL_HOST_LOCAL='47.242.249.82'
MYSQL_HOST_ONLINE=''
MYSQL_PASSWORD='test@123'
MYSQL_PORT='3306'
MYSQL_USER='root'