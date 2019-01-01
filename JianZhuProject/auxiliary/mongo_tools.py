
# coding=utf-8
from __future__ import print_function
import pymongo

class MongoTools():
    def __init__(self):
        self.host = 'localhost'
        self.port = 27017
        self.mongo_conn = pymongo.MongoClient(self.host, self.port)

        print('成功连接mongo')

    def get_documents(self, batch_size, skip_num):
        result = self.mongo_conn.zjsc.compass_table.find().limit(int(batch_size)).skip(int(skip_num))
        return result