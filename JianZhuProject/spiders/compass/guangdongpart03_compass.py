# coding=utf-8
import datetime
import json
import re

import scrapy
import time
import urllib
from JianZhuProject import sit_list
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class GuangDongPart03Compass(BaseCompass):
    name = 'guangdong03_compass'
    allow_domain = ['218.13.12.85']
    custom_settings = {
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, }
    }
    log_file = '../logs/{}_log.log'.format(name)
    cnt = 1
    start_urls = [
        ('http://218.13.12.85/cxpt/web/enterprise/getEnterpriseList.do', sit_list[0])
    ]
    refers = ['http://218.13.12.85/cxpt/website/enterpriseList.jsp']

    now_time = datetime.datetime.now().strftime('%Y-%m-%d')

    redis_tools = RedisTools()

    def start_requests(self):
        for link, sit in self.start_urls:
            headers = self.get_header(self.refers[0], flag='2')
            formdata = self.get_form_data(0)
            yield scrapy.FormRequest(link, headers=headers, formdata=formdata, callback=self.parse_list,
                                     meta={'pageIndex': '0', 'sit': sit})

    def parse_list(self, response):
        json_resp = json.loads(response.text)
        item_contains = []
        for unit in json_resp['data']:
            cname, cid, _id, bid, province = unit['corpName'], unit['corpCode'], unit['id'], unit['bid'], unit[
                'areacode']
            detail_link = 'http://218.13.12.85/cxpt/website/enterpriseInfo.jsp?entID={}&eid={}&bid={}'.format(cid, _id,
                                                                                                              bid)
            out_province = self.handle_out_province(province)

            if self.redis_tools.check_finger(cname):
                print(u'{}已经爬取过'.format(cname))
                continue
            item = NameItem({'compass_name': cname, 'detail_link': detail_link, 'out_province': out_province})
            item_contains.append(item)
        yield {'item_contains': item_contains}
        if 'total' not in response.meta:
            response.meta['total_page_num'] = (int(json_resp['total']) + 9) / 10
        if int(response.meta['pageIndex']) < int(response.meta['total_page_num']):
            yield self.turn_page(response)
        else:
            print('不能继续翻页了, 当前最大页码:{}'.format(response.meta['pageIndex']))
            return

    def turn_page(self, response):
        meta = response.meta

        link = response.url
        meta['pageIndex'] = str(int(meta['pageIndex']) + 1)
        formdata = self.get_form_data(meta['pageIndex'])
        headers = self.get_header(self.refers[0], flag='2')
        return scrapy.FormRequest(link, headers=headers, formdata=formdata, meta=meta, callback=self.parse_list)

    def get_form_data(self, next_page_num):
        formdata = {
            'mainZZ': '0',
            'aptText': '',
            'areaCode': '0',
            'entName': '',
            'pageSize': '10',
            'pageIndex': str(next_page_num),
        }
        return formdata

    def handle_out_province(self, s):
        if s is '':
            return 'waisheng'
        return s.split('-')[0]


if __name__ == '__main__':
    GuangDongPart03Compass().run()
