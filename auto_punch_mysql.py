"""
@Coding:utf-8
@Author:hbc
@Time:2022/8/28 14:42
@File:auto_punch_mysql
@Software:PyCharm
"""
import mysql.connector


class DBHandle:

    def __init__(self, logger, time):
        self.logging = logger
        self.time = time
        mysql_config = {
            'user': 'root',
            'password': '111111',
            'host': '192.168.9.48',
            'database': 't_data',
            'port': '3306',
            'ssl_disabled': True
        }
        try:
            self.cnx = mysql.connector.connect(**mysql_config)
            if self.cnx.is_connected():
                self.out_logger('connected to database')
        except Exception:
            # self.out_logger(f"mysql DB connection error:{e}")
            raise

    def out_logger(self, text):
        if self.logging:
            self.logging.info(f'{text}->{self.time.strftime("%Y-%m-%d %H:%M:%S", self.time.localtime())}')
        elif self.time:
            print(f'{text}->{self.time.strftime("%Y-%m-%d %H:%M:%S", self.time.localtime())}')
        else:
            print(f'{text}')

    def query_db(self):
        cursor = self.cnx.cursor()
        cursor.execute("SELECT * FROM user_punch_config")
        result = cursor.fetchall()
        return result


if __name__ == "__main__":
    data = DBHandle(None, None)
    data.query_db()
