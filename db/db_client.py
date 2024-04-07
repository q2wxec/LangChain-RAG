
import sqlite3
import os
from db.sqllit import SQLiteConnectionPool

class KnowledgeBaseManager:
    def __init__(self,dbfile,logger):
        self.logger = logger
        self.check_database_(dbfile)
        self.cnxpool = SQLiteConnectionPool(dbfile, max_connections=10)
        self.create_tables_()
        self.logger.info("[SUCCESS] 数据库{}连接成功".format(dbfile))

    def check_database_(self, db_file):
        # 分离出文件名和目录路径
        directory = os.path.dirname(db_file)

        # 检查目录是否存在
        if not os.path.exists(directory):
            # 如果目录不存在，则创建它
            os.makedirs(directory, exist_ok=True)  # 使用exist_ok=True防止当目录已存在时报错

        # 现在可以进一步检查或操作db_file文件了
        if not os.path.isfile(db_file):
            # 尝试连接数据库
            conn = sqlite3.connect(db_file)
            
            # 关闭连接
            conn.close()
            pass

    def execute_query_(self, query, params, commit=False, fetch=False):
        conn = self.cnxpool.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)

        if commit:
            conn.commit()

        if fetch:
            result = cursor.fetchall()
        else:
            result = None

        cursor.close()
        conn.close()

        return result

    def create_tables_(self):
        query = """
            CREATE TABLE IF NOT EXISTS User (
                user_id VARCHAR(255) PRIMARY KEY,
                user_name VARCHAR(255)
            );
        """

        self.execute_query_(query, (), commit=True)
        query = """
            CREATE TABLE IF NOT EXISTS KnowledgeBase (
                kb_id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255),
                kb_name VARCHAR(255),
                deleted BOOL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
            );

        """
        self.execute_query_(query, (), commit=True)
        query = """
            CREATE TABLE IF NOT EXISTS File (
                file_id VARCHAR(255) PRIMARY KEY,
                kb_id VARCHAR(255),
                file_name VARCHAR(255),
                status VARCHAR(255),
                timestamp VARCHAR(255),
                deleted BOOL DEFAULT 0,
                file_size INT DEFAULT -1,
                content_length INT DEFAULT -1,
                chunk_size INT DEFAULT -1,
                FOREIGN KEY (kb_id) REFERENCES KnowledgeBase(kb_id) ON DELETE CASCADE
            );

        """
        self.execute_query_(query, (), commit=True)
        query = """
            CREATE TABLE IF NOT EXISTS Prompt (
                kb_id VARCHAR(255),
                user_id VARCHAR(255),
                prompt text,
                deleted BOOL DEFAULT 0,
                FOREIGN KEY (kb_id) REFERENCES KnowledgeBase(kb_id) ON DELETE CASCADE
            );

        """
        self.execute_query_(query, (), commit=True)        

        # 兼顾一下旧的表
        try:
            # timestamp 默认是197001010000
            query = """
                ALTER TABLE File
                ADD COLUMN timestamp VARCHAR(255) DEFAULT '197001010000';
            """
            self.logger.info('ADD COLUMN timestamp')
            res = self.execute_query_(query, (), commit=True)
            self.logger.info(res)
        except Exception as e:
            if 'duplicate column name' in str(e):
                self.logger.info(e)
            else:
                raise e
        
    def check_user_exist_(self, user_id):
        query = "SELECT user_id FROM User WHERE user_id = ?"
        result = self.execute_query_(query, (user_id,), fetch=True)
        self.logger.info("check_user_exist {}".format(result))
        return result is not None and len(result) > 0

    def check_kb_exist(self, user_id, kb_ids):
        kb_ids_str = ','.join("'{}'".format(str(x)) for x in kb_ids)
        query = "SELECT kb_id FROM KnowledgeBase WHERE kb_id IN ({}) AND deleted = 0 AND user_id = ?".format(kb_ids_str)
        result = self.execute_query_(query, (user_id,), fetch=True)
        self.logger.info("check_kb_exist {}".format(result))
        valid_kb_ids = [kb_info[0] for kb_info in result]
        unvalid_kb_ids = list(set(kb_ids) - set(valid_kb_ids))
        return unvalid_kb_ids

    def get_file_by_status(self, kb_ids, status):
        # query = "SELECT file_name FROM File WHERE kb_id = ? AND deleted = 0 AND status = ?"
        kb_ids_str = ','.join("'{}'".format(str(x)) for x in kb_ids)
        query = "SELECT file_id, file_name FROM File WHERE kb_id IN ({}) AND deleted = 0 AND status = ?".format(kb_ids_str)
        result = self.execute_query_(query, (status,), fetch=True)
        # result = self.execute_query_(query, (kb_id, "gray"), fetch=True)
        return result

    def check_file_exist(self, user_id, kb_id, file_ids):
        # 筛选出有效的文件
        if not file_ids:
            self.logger.info("check_file_exist []")
            return []
        
        file_ids_str = ','.join("'{}'".format(str(x)) for x in file_ids)
        query = """SELECT file_id, status FROM File 
                 WHERE deleted = 0
                 AND file_id IN ({})
                 AND kb_id = ? 
                 AND kb_id IN (SELECT kb_id FROM KnowledgeBase WHERE user_id = ?)""".format(file_ids_str)
        # self.execute_query_(query, (kb_id, user_id), commit=True)
        result = self.execute_query_(query, (kb_id, user_id), fetch=True)
        self.logger.info("check_file_exist {}".format(result))
        return result
    
    def check_file_exist_by_name(self, user_id, kb_id, file_names):
        results = []
        batch_size = 100  # 根据实际情况调整批次大小

        # 分批处理file_names
        for i in range(0, len(file_names), batch_size):
            batch_file_names = file_names[i:i+batch_size]
            file_names_str = ','.join("'{}'".format(str(x).replace("'", "\\'")) for x in batch_file_names)
            query = """
                SELECT file_id, file_name, file_size, status FROM File 
                WHERE deleted = 0
                AND file_name IN ({})
                AND kb_id = ? 
                AND kb_id IN (SELECT kb_id FROM KnowledgeBase WHERE user_id = ?)
            """.format(file_names_str)
            
            # 这里假设 execute_query_ 是一个可以执行SQL查询并提交或获取结果的方法
            batch_result = self.execute_query_(query, (kb_id, user_id), fetch=True)
            self.logger.info("check_file_exist_by_name batch {}: {}".format(i//batch_size, batch_result))
            results.extend(batch_result)

        return results

    # 对外接口不需要增加用户，新建知识库的时候增加用户就可以了
    def add_user_(self, user_id, user_name=None):
        query = "INSERT INTO User (user_id, user_name) VALUES (?, ?)"
        self.execute_query_(query, (user_id, user_name), commit=True)
        return user_id

    def new_vector_base(self, kb_id, user_id, kb_name, user_name=None):
        if not self.check_user_exist_(user_id):
            self.add_user_(user_id, user_name)
        query = "INSERT INTO KnowledgeBase (kb_id, user_id, kb_name) VALUES (?, ?, ?)"
        self.execute_query_(query, (kb_id, user_id, kb_name), commit=True)
        return kb_id, "success"

    # [知识库] 获取指定用户的所有知识库 
    def get_knowledge_bases(self, user_id):
        query = "SELECT kb_id, kb_name FROM KnowledgeBase WHERE user_id = ? AND deleted = 0"
        return self.execute_query_(query, (user_id,), fetch=True)
    
    def get_users(self):
        query = "SELECT user_id FROM User"
        return self.execute_query_(query, (), fetch=True)

    # [知识库] 获取指定kb_ids的知识库
    def get_knowledge_base_name(self, kb_ids):
        kb_ids_str = ','.join("'{}'".format(str(x)) for x in kb_ids)
        query = "SELECT user_id, kb_id, kb_name FROM KnowledgeBase WHERE kb_id IN ({}) AND deleted = 0".format(kb_ids_str)
        return self.execute_query_(query, (), fetch=True)

    # [知识库] 删除指定知识库
    def delete_knowledge_base(self, user_id, kb_ids):
        # 删除知识库
        kb_ids_str = ','.join("'{}'".format(str(x)) for x in kb_ids)
        query = "UPDATE KnowledgeBase SET deleted = 1 WHERE user_id = ? AND kb_id IN ({})".format(kb_ids_str)
        self.execute_query_(query, (user_id,), commit=True)
        # 删除知识库下面的文件
        query = """UPDATE File SET deleted = 1 WHERE kb_id IN ({}) AND kb_id IN (SELECT kb_id FROM KnowledgeBase WHERE user_id = ?)""".format(kb_ids_str)
        self.execute_query_(query, (user_id,), commit=True)
    
    # [知识库] 重命名知识库
    def rename_knowledge_base(self, user_id, kb_id, kb_name):
        query = "UPDATE KnowledgeBase SET kb_name = ? WHERE kb_id = ? AND user_id = ?"
        self.execute_query_(query, (kb_name, kb_id, user_id), commit=True)

    # [文件] 向指定知识库下面增加文件
    def add_file(self, file_id,user_id, kb_id, file_name, timestamp, status="gray"):
        # 如果他传回来了一个id, 那就说明这个表里肯定有
        if not self.check_user_exist_(user_id):
            return None, "invalid user_id, please check..."
        not_exist_kb_ids = self.check_kb_exist(user_id, [kb_id])
        if not_exist_kb_ids:
            return None, f"invalid kb_id, please check {not_exist_kb_ids}"
        
        query = "INSERT INTO File (file_id, kb_id, file_name, status, timestamp) VALUES (?, ?, ?, ?, ?)"
        self.execute_query_(query, (file_id, kb_id, file_name, status, timestamp), commit=True)
        return file_id, "success"

    #  更新file中的file_size
    def update_file_size(self, file_id, file_size):
        query = "UPDATE File SET file_size = ? WHERE file_id = ?"
        self.execute_query_(query, (file_size, file_id), commit=True)
    
    #  更新file中的content_length
    def update_content_length(self, file_id, content_length):
        query = "UPDATE File SET content_length = ? WHERE file_id = ?"
        self.execute_query_(query, (content_length, file_id), commit=True)
    
    #  更新file中的chunk_size
    def update_chunk_size(self, file_id, chunk_size):
        query = "UPDATE File SET chunk_size = ? WHERE file_id = ?"
        self.execute_query_(query, (chunk_size, file_id), commit=True)

    def update_file_status(self, file_id, status):
        query = "UPDATE File SET status = ? WHERE file_id = ?" 
        self.execute_query_(query, (status, file_id), commit=True)

    def from_status_to_status(self, file_ids, from_status, to_status):
        file_ids_str = ','.join("'{}'".format(str(x)) for x in file_ids)
        query = "UPDATE File SET status = ? WHERE file_id IN ({}) AND status = ?".format(file_ids_str)
        self.execute_query_(query, (to_status, from_status), commit=True)
        

    # [文件] 获取指定知识库下面所有文件的id和名称
    def get_files(self, user_id, kb_id):
        query = "SELECT file_id, file_name, status, file_size, content_length, timestamp FROM File WHERE kb_id = ? AND kb_id IN (SELECT kb_id FROM KnowledgeBase WHERE user_id = ?) AND deleted = 0"
        return self.execute_query_(query, (kb_id, user_id), fetch=True)

    # [文件] 删除指定文件
    def delete_files(self, kb_id, file_ids):
        file_ids_str = ','.join("'{}'".format(str(x)) for x in file_ids)
        query = "UPDATE File SET deleted = 1 WHERE kb_id = ? AND file_id IN ({})".format(file_ids_str)
        #self.logger.info("delete_files: {}".format(query))
        self.execute_query_(query, (kb_id,), commit=True)

    def add_prompt(self, user_id, kb_id, prompt):
        query = "INSERT INTO Prompt (user_id, kb_id, prompt) VALUES (?, ?, ?)"
        self.execute_query_(query, (user_id, kb_id, prompt), commit=True)
        return kb_id
    
    def update_prompt(self, user_id, kb_id, prompt):
        query = "UPDATE Prompt SET prompt = ?  WHERE kb_id = ? AND user_id = ?"
        self.execute_query_(query, (prompt,kb_id,user_id), commit=True)
        return kb_id
    
    def get_prompt(self, user_id, kb_id):
        query = "SELECT prompt from Prompt WHERE kb_id = ? AND user_id = ?"
        return self.execute_query_(query, (kb_id,user_id), fetch=True)