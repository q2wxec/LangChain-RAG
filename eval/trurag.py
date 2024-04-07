from trulens_eval import TruChain, Feedback,Tru
import numpy as np
from trulens_eval.app import App
from trulens_eval.feedback import Groundedness
from trulens_eval.feedback.provider.langchain import Langchain
import os
from config.model_config import trulens_eval_on,EVAL_DB_FILE_PATH

if trulens_eval_on:
    # 分离出文件名和目录路径
    directory = os.path.dirname(EVAL_DB_FILE_PATH)

    # 检查目录是否存在
    if not os.path.exists(directory):
        # 如果目录不存在，则创建它
        os.makedirs(directory, exist_ok=True)  # 使用exist_ok=True防止当目录已存在时报错
    tru = Tru(database_url=r"sqlite:///" + EVAL_DB_FILE_PATH)

def tru_recorder(rag_chain,llm):
    # 使用TruChain类来包装rag对象，指定反馈函数和应用ID
    # Initialize provider class
    provider = Langchain(chain=llm)
    # select context to be used in feedback. the location of context is app specific.App
    # context = App.select_context(rag_chain)
    context = App.select_context(rag_chain)
    grounded = Groundedness(groundedness_provider=provider)
    # f_context_relevance, f_groundness, f_answer_relevance 定义反馈函数
    # Define a groundedness feedback function
    f_groundedness = (
        Feedback(grounded.groundedness_measure_with_cot_reasons)
        .on(context.collect()) # collect context chunks into a list
        .on_output()
        .aggregate(grounded.grounded_statements_aggregator)
    )

    # Question/answer relevance between overall question and answer.
    f_qa_relevance = Feedback(provider.relevance).on_input_output()
    # Question/statement relevance between question and each context chunk.
    f_context_relevance = (
        Feedback(provider.qs_relevance)
        .on_input()
        .on(context)
        .aggregate(np.mean)
        )
    # 使用with语句来运行rag对象，并记录反馈数据feedback_mode="deferred"
    tru_recorder = TruChain(rag_chain,
        app_id='LangChain_RAG',
        feedbacks=[f_qa_relevance, f_context_relevance, f_groundedness],
        tru=tru)
    return tru_recorder



# 定义要在线程池中执行的任务函数
# def worker_task(param):
#     # 这里是处理任务的具体逻辑
#     print(f"Processing task with param: {param}")
#     # 假设这是一个耗时操作，比如网络请求或计算等
#     tru.start_evaluator()
#     # time.sleep(1)  # 示例性的延时操作

# # 创建一个包含5个线程的线程池
# with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
#     executor.submit(worker_task) 

# 当with语句结束时，线程池会自动关闭和清理资源

# from typing import Optional

# from trulens_eval.app import App
# from trulens_eval.schema import Select
# from trulens_eval.utils.json import jsonify
# from trulens_eval.utils.serial import all_queries
# from trulens_eval.utils.serial import Lens
# from langchain.chains.base import Chain
# from langchain.schema import BaseRetriever
# def select_context(app: Optional[Chain] = None) -> Lens:
#     """
#     Get the path to the context in the query output.
#     """

#     if app is None:
#         raise ValueError(
#             "langchain app/chain is required to determine context for langchain apps. "
#             "Pass it in as the `app` argument"
#         )

#     retrievers = []

#     app_json = jsonify(app)
#     for lens in all_queries(app_json):
#         try:
#             comp = lens.get_sole_item(app)
#             if isinstance(comp, BaseRetriever):
#                 retrievers.append((lens, comp))

#         except Exception as e:
#             pass

#     if len(retrievers) == 0:
#         raise ValueError("Cannot find any `BaseRetriever` in app.")

#     if len(retrievers) > 1:
#         raise ValueError(
#             "Found more than one `BaseRetriever` in app:\n\t" + \
#             ("\n\t".join(map(
#                 lambda lr: f"{type(lr[1])} at {lr[0]}",
#                 retrievers)))
#         )
#     return Lens.of_string('__record__.app.middle[1].steps.docs.invoke.rets')
#     #(Select.RecordCalls + retrievers[0][0]).invoke.rets
