import logging

from concurrent_log_handler import ConcurrentRotatingFileHandler
import time
import os

# 获取当前时间作为日志文件名的一部分
current_time = time.strftime("%Y%m%d_%H%M%S")
# 定义日志文件夹路径
log_folder = './temp/knowie_logs'
# 确保日志文件夹存在
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
# 定义日志文件的完整路径，包括文件夹和文件名
log_file = os.path.join(log_folder, f'log_{current_time}.log')

# 创建一个 logger 实例
logger = logging.getLogger()
# 设置 logger 的日志级别为 INFO，即只记录 INFO 及以上级别的日志信息
logger.setLevel(logging.INFO)

# 创建一个 ConcurrentRotatingFileHandler 实例
# log_file: 日志文件名
# "a": 文件的打开模式，追加模式
# 16*1024*1024: maxBytes，当日志文件达到 512KB 时进行轮转
# 5: backupCount，保留 5 个轮转日志文件的备份
handler = ConcurrentRotatingFileHandler(log_file, "a", 16 * 1024 * 1024, 5)
# 定义日志格式
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# 设置日志格式
handler.setFormatter(formatter)

# 将 handler 添加到 logger 中，这样 logger 就可以使用这个 handler 来记录日志了
logger.addHandler(handler)

