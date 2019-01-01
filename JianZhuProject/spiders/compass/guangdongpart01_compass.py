# coding=utf-8
import json

import scrapy
import time

from JianZhuProject import sit_list
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class GuangDongPart01Compass(BaseCompass):
    name = 'guangdong01_compass'
    allow_domain = ['219.129.189.10:8080', 'www.jyjzcx.com']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, }
    }
    log_file = '../logs/{}_log.log'.format(name)
    cnt = 1
    start_urls = [
        # ("http://219.129.189.10:8080/yjcxk/web-nav/enterprises?pageNumber=1", sit_list[0]),
        # ("http://219.129.189.10:8080/yjcxk/web-nav/enterprises?pageNumber=0", sit_list[1]),
        # ("http://219.129.189.10:8080/yjcxk/web-nav/persons?pageNumber=1&pageSize=17550", sit_list[0])
        ('http://www.jyjzcx.com/web/companylist.action?pageNum=1&pageSize=15', sit_list[0])

    ]
    extract_dict = {
        'inner': {
            'nodes': '//div[@class="list"]/table//tr[position()>1]',
            'cname': './td[@class="tdl"]/a/text()',
            'detail_link': './td[@class="tdl"]/a/@href',  # 'http://www.jyjzcx.com' + xxx,
            'next_page_url': '//a[@class="laypage_next"]/@data-page'  #
        }
    }

    redis_tools = RedisTools()

    def start_requests(self):
        for link, sit in self.start_urls:
            yield scrapy.Request(link, callback=self.parse_list1, meta={'cur_page': '1'})

    def parse_list1(self, response):
        ext_rules = self.extract_dict['inner']
        nodes = response.xpath(ext_rules['nodes'])
        item_contains = []
        for node in nodes:
            item = NameItem()
            item['compass_name'] = node.xpath(ext_rules['cname']).extract_first()
            item['detail_link'] = node.xpath(ext_rules['detail_link']).extract_first()
            item['out_province'] = 'waisheng'
            if self.redis_tools.check_finger(item['detail_link']):
                print(u'{}已经爬取郭'.format(item['compass_name']))
                continue
            item_contains.append(item)
        yield {'item_contains': item_contains}
        yield self.turn_page(response)

    def turn_page(self, response):
        meta = response.meta
        if int(meta['cur_page']) >= 19:
            print(u'不能在翻页了')
            return
        meta['cur_page'] = str(int(meta['cur_page']) + 1)
        link = 'http://www.jyjzcx.com/web/companylist.action?pageNum={}&pageSize=15'.format(meta['cur_page'])
        headers = self.get_header(response.url, flag='2')
        return scrapy.Request(link, callback=self.parse_list1, headers=headers, meta=meta)

        # def parse_list(self, response):
        #     data = json.loads(response.body_as_unicode())['data']['rows']
        #     item_contains = []
        #     for unit in data:
        #         if 'persons' in response.url:
        #             compass_name = unit['entName']
        #             detail_link = 'None'
        #             out_province = 'waisheng'
        #         else:
        #             compass_name = unit['companyName']
        #             detail_link = 'http://219.129.189.10:8080/yjcxk/vueStatic/html/companyDetail.jsp?id=' + unit['id']
        #             out_province = 'guangdong'
        #         if detail_link in ('', 'None'):
        #             if self.redis_tools.check_finger(compass_name):
        #                 continue
        #         else:
        #             if self.redis_tools.check_finger(detail_link):
        #                 continue
        #         item = NameItem({
        #             'compass_name': compass_name,
        #             'detail_link': detail_link,
        #             'out_province': out_province
        #         })
        #         if '测试企业' in item['compass_name']:
        #             continue
        #         item_contains.append(item)
        #     yield {'item_contains': item_contains}
        #
        #     # def turn_page(self, response):
        #     #     next_page_num = response['']
        #     #     "http://219.129.189.10:8080/yjcxk/web-nav/persons?pageNumber={}&pageSize=5000".format(next_page_num)
        #     #     return


if __name__ == '__main__':
    GuangDongPart01Compass().run()
