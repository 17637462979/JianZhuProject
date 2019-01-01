
# coding=utf-8
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.settings import ALL_FINGER_CONTAINS


class CorpNamePipeline(object):
    redis_tools = RedisTools()

    def __init__(self):
        self.cnt = 1

    def process_item(self, item_contains, spider):
        for item in item_contains['item_contains']:
            spider_name = spider.name

            compass_name = item['compass_name']
            detail_link = item['detail_link']
            out_province = item['out_province']   # 'None'为本省, 否则保存外省名

            if item['detail_link'] is None or item['detail_link'].upper() in ('NONE', ''):
                finger = compass_name
            else:
                finger = item['detail_link']  # 公司名作为指纹
            self.redis_tools.store_finger(ALL_FINGER_CONTAINS, finger)
            common_info = '##'.join([compass_name, detail_link, out_province])
            self.redis_tools.store_finger(spider_name, common_info)
            print('---------%d个信息item被保存' % self.cnt)
            self.cnt += 1
        return item_contains

    def close_spider(self, spider):
        """爬虫结束后执行(一次)"""
        self.db = None
        self.conn = None
        print('关闭爬虫，本次一次存了 %d个信息item' % self.cnt)
        pass