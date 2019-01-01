# coding=utf-8
from __future__ import print_function
import redis

from JianZhuProject.settings import ALL_FINGER_CONTAINS


class RedisTools():
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 6379
        self.red_conn = redis.Redis(self.host, self.port, db=5)
        print(u'成功连接redis')

    def check_finger(self, finger, name=ALL_FINGER_CONTAINS):
        is_member = self.red_conn.sismember(name, value=finger)  # 公司容器
        return is_member

    def store_finger(self, name, finger):
        self.red_conn.sadd(name, finger)
        # print(name, finger)
        print(u'指纹%s存储成功' % finger)
