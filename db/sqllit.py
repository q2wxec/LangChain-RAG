import sqlite3
from queue import Queue
from threading import Lock

class SQLiteConnectionPool:
    def __init__(self, db_file, max_connections=5):
        self.db_file = db_file
        self.max_connections = max_connections
        self.connections = Queue(maxsize=max_connections)
        self.lock = Lock()

    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        # 可以根据需要设置游标类型、事务隔离级别等
        return conn
    
   