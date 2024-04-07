from trulens_eval import Tru
from config.model_config import EVAL_DB_FILE_PATH

tru = Tru(database_url=r"sqlite:///" + EVAL_DB_FILE_PATH)
tru.run_dashboard()