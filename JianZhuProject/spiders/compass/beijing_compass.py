# coding=utf-8
import json

import scrapy
import time

from JianZhuProject import sit_list
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class BeiJingCompass(BaseCompass):
    name = 'beijing_compass'
    allow_domain = ['xpt.bcactc.com']
    custom_settings = {
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, }
    }
    log_file = '../logs/{}_log.log'.format(name)
    cnt = 1
    start_urls = [
        ("http://xpt.bcactc.com/G2/basic/gfm/info!performancePublicList.do?data&filter_params_=enterpriseName",
         sit_list[1]),
        ("http://xpt.bcactc.com/G2/basic/gfm/info!entOrganizationList.do?data&filter_params_=enterpriseName",
         sit_list[1]),
        (
            "http://xpt.bcactc.com/G2/basic/gfm/info!entPersonInfoList.do?data&filter_params_=enterpriseName",
            sit_list[0]),
        ("http://xpt.bcactc.com/G2/basic/gfm/info!entPerformanceList.do?data&filter_params_=enterpriseName",
         sit_list[1]),
    ]

    redis_tools = RedisTools()

    def start_requests(self):
        for url, sit in self.start_urls:
            headers = self.get_header(url, flag='1')
            yield scrapy.Request(url=url, callback=self.parse_list, headers=headers,
                                 meta={'sit': sit, 'cur_page_num': '1'})

    def parse_list(self, response):

        meta = response.meta
        sit = meta['sit']
        out_province = 'beijing' if sit_list[0] == sit else 'waisheng'

        json_data = json.loads(response.body_as_unicode())['data']
        item_contains = []
        for unit in json_data:
            item = NameItem({
                'compass_name': unit['enterpriseName'],
                'detail_link': 'None',
                'out_province': out_province
            })
            item_contains.append(item)
        yield {'item_contains': item_contains}
        yield self.turn_page(response)

    def turn_page(self, response):
        meta = response.meta
        if 'total_page' not in meta:
            _ = json.loads(response.body_as_unicode())
            meta['total_page'], meta['cur_page_num'] = _['total'], _['page']

        print('当前页:{}, 总页码:{}'.format(meta['cur_page_num'], meta['total_page']))
        if int(meta['cur_page_num']) >= int(meta['total_page']):
            print('不能翻页了，当前最大页码:{}'.format(meta['cur_page_num']))
            return
        headers = self.get_header(response.url, flag='2')
        formdata = self.get_form_data(response)
        meta['cur_page_num'] = str(int(meta['cur_page_num']) + 1)
        return scrapy.FormRequest(response.url, headers=headers, formdata=formdata, callback=self.parse_list, meta=meta)

    def get_form_data(self, response):
        form_data = {
            'gridSearch': 'false',
            'nd': str(int(time.time() * 1000)),
            'PAGESIZE': '15',
            'PAGE': str(response.meta['cur_page_num']),
            'sortField': '',
            'sortDirection': 'asc',
        }
        return form_data

    def get_header(self, url, flag='1'):
        headers = {
            "Host": "xpt.bcactc.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",

        }
        if flag not in (1, '1'):
            headers["Referer"], headers["Origin"] = url, self.get_domain_info(url)  # 二次进入才有
        return headers

    def handle_cdetail_link(self, clink, flag='inner', url=''):
        if clink.startswith('http'):
            good_link = clink
        else:
            good_link = "" + clink
        return good_link


if __name__ == '__main__':
    BeiJingCompass().run()
