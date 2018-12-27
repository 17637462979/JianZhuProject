# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging

from pymongo import MongoClient
from JianZhuProject.auxiliary.redis_tools import RedisTools
import base64
import sys

from JianZhuProject.settings import ALL_FINGER_CONTAINS

reload(sys)
sys.setdefaultencoding('utf8')

conn = MongoClient(host='127.0.0.1', port=27017)
db = conn.zjsc


class JianzhuprojectPipeline(object):
    redis_tools = RedisTools()
    __cur_collections = None

    def __init__(self):
        self.db = db
        self.cnt = 1
        self.cur_collections = list(self.db.list_collections())

    def check_collection(self, spider):
        if {'name': spider.name} not in self.__cur_collections:
            self.db.create_collection(spider.name)

    def process_item(self, item_contaner, spider):
        try:
            self.db.get_collection(spider.name).insert({'item_contaner': item_contaner})
        except Exception as e:
            self.db.create_collection(spider.name).insert({'item_contaner': item_contaner})
        else:
            print 'Mongodb已保存'
            compass_name = item_contaner['compass_items'][0]['compass_name']
            honor_code = item_contaner['honor_code']
            source_link = item_contaner['source_link']
            spider_name = spider.name
            finger = source_link  # ascii码, decode、encode、str均报错,只用使用repr、或`xx`

            self.redis_tools.store_finger(ALL_FINGER_CONTAINS, finger)   # finger_contains集存储去重
            provice = item_contaner['compass_items'][0]['provice']
            common_info = '##'.join([compass_name, honor_code, provice, source_link])
            self.redis_tools.store_finger(spider_name, common_info)    # redis存储备用url关联
            # 集合保存信息,如果有多个源补充时,就保存多条信息, 对现有数据更新同时获取该公司多条link
            print('---------%d个信息item被保存' % self.cnt)
            self.cnt += 1
        return item_contaner

    def close_spider(self, spider):
        """爬虫结束后执行(一次)"""
        self.db = None
        self.conn = None
        print('关闭爬虫，本次一次存了 %d个信息item' % self.cnt)
        pass