# coding=utf-8
import json

import scrapy
import time

from JianZhuProject import sit_list
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class GuangDongPart01Compass(BaseCompass):
    name = 'guangdong_compass'
    allow_domain = ['219.129.189.10:8080']
    custom_settings = {
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, }
    }
    log_file = '../logs/{}_log.log'.format(name)
    cnt = 1
    start_urls = [
        # ("http://219.129.189.10:8080/yjcxk/web-nav/enterprises?pageNumber=1", sit_list[0]),
        # ("http://219.129.189.10:8080/yjcxk/web-nav/enterprises?pageNumber=0", sit_list[1]),
        ("http://219.129.189.10:8080/yjcxk/web-nav/persons?pageNumber=1&pageSize=17550", sit_list[0])
    ]

    redis_tools = RedisTools()

    def start_requests(self):
        for link, sit in self.start_urls:
            yield scrapy.Request(link, callback=self.parse_list, dont_filter=True)

    def parse_list(self, response):
        data = json.loads(response.body_as_unicode())['data']['rows']
        item_contains = []
        print(u'有', len(data))
        for unit in data:
            if 'persons' in response.url:
                compass_name = unit['entName']
                detail_link = 'None'
                out_province = 'waisheng'
            else:
                compass_name = unit['companyName']
                detail_link = 'http://219.129.189.10:8080/yjcxk/vueStatic/html/companyDetail.jsp?id=' + unit['id']
                out_province = 'guangdong'
            if detail_link in ('', 'None'):
                if self.redis_tools.check_finger(compass_name):
                    continue
            else:
                if self.redis_tools.check_finger(detail_link):
                    continue
            item = NameItem({
                'compass_name': compass_name,
                'detail_link': detail_link,
                'out_province': out_province
            })
            if '测试企业' in item['compass_name']:
                continue
            item_contains.append(item)
        yield {'item_contains': item_contains}

        # def turn_page(self, response):
        #     next_page_num = response['']
        #     "http://219.129.189.10:8080/yjcxk/web-nav/persons?pageNumber={}&pageSize=5000".format(next_page_num)
        #     return


if __name__ == '__main__':
    GuangDongPart01Compass().run()
