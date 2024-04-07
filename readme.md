* **下载向量和rerank模型**

```
# 下载安装git-fls https://github.com/git-lfs/git-lfs/releases
git lfs install

mkdir -p modal
cd modal

git clone https://www.modelscope.cn/quietnight/bge-reranker-large.git
git clone https://www.modelscope.cn/AI-ModelScope/bge-large-zh-v1.5.git
```

- **配置llm，复制config-exp.ini**

```
cp config-exp.ini config.ini 
```

- **配置核心字段（最简版，除标注须替换的字段外，其他字段不动）**

```
[llm]
# https://dashscope.console.aliyun.com/apiKey
# 通义千问 api key 配置你的api_key
ty_api_key = 

[embedding]
embedding_type = huggingface

[server]

llm_type = tongyi

llm_model= qwen-max
# rerank类型
rerank_type = bge

# bge,rerank模型路径,需要修改为你的下载全路径
bge_rerank_modal_path = modal/bge-reranker-large

# emmbedding模型路径,需要修改为你的下载全路径
emmbedding_modal_path = modal/bge-large-zh-v1.5
# chroma
vector_type = chroma

[retrive]
retrive_fusion_on = False

[eval]

trulens_eval_on = False

[db]
type = sqlite
```

* **拉取项目，安装依赖**

```
# 进入项目主目录
cd LangChain-RAG
# 创建虚拟环境
python -m venv venv
# 激活虚拟环境win10
venv\Scripts\activate
# 激活虚拟环境linux
source venv/bin/activate
# 后端依赖安装
pip install -r requirements.txt
```

* **配置nltk拓展包用于分词python -c 'import nltk; nltk.download("punkt")'**

```
git clone -b gh-pages https://gitee.com/qwererer2/nltk_data.git
mkdir -p /usr/share/nltk_data
unzip -d nltk_data/packages/tokenizers nltk_data/packages/tokenizers/punkt.zip
cp -R nltk_data/packages/* /usr/share/nltk_data
rm -rf nltk_data
```

- **配置OCR**（选做）

```
wget https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/english_g2.zip
wget https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/latin_g2.zip
wget https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/zh_sim_g2.zip
wget https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip

# 将以上模型解压到用户主目录
mkdir -p ~/.EasyOCR/model
unzip -d ~/.EasyOCR/model english_g2.zip
unzip -d ~/.EasyOCR/model latin_g2.zip
unzip -d ~/.EasyOCR/model zh_sim_g2.zip
unzip -d ~/.EasyOCR/model craft_mlt_25k.zip
```

- **修改前端配置**

```
# 修改文件路径 web_ui\.env.production
VITE_APP_API_HOST=https://tomcat-together-previously.ngrok-free.app
VITE_APP_API_PREFIX=/api
VITE_APP_WEB_PREFIX=/LangChain-RAG
VITE_APP_MODE=prod
需要将VITE_APP_API_HOST修改为你的服务发布域名或ip如本地运行则修改为http://localhost:8777
```

- **编译前端代码**

```
cd web_ui
# node 18.19.10以上版本
npm run build
```

- **启动项目**

```
# python 3.10以上版本
python main.py
```

- **访问项目**

```
# 本地启动访问地址
http://localhost:8777/LangChain-RAG/index.html
```

