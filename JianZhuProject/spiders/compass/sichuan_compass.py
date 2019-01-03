# coding=utf-8
import json

import scrapy
import time

from lxml import etree

from JianZhuProject import sit_list
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class SiChuanCompass(BaseCompass):
    name = 'sichuan_compass'
    allow_domain = ['xmgk.scjst.gov.cn']
    custom_settings = {
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, }
    }
    log_file = '../logs/{}_log.log'.format(name)
    cnt = 1
    start_urls = [
        ('http://xmgk.scjst.gov.cn/QueryInfo/Ente/EnteList.aspx', sit_list[0])
    ]

    extract_dict = {
        'inner': {
            'nodes': '//table[contains(@class, "list")]//tr[position()>1]',
            'cname': './/a[contains(@href, "EnteZsxx") and @title]/@title',
            'detail_link': './/a[contains(@href, "EnteZsxx") and @title]/@href',
        # 'http://xmgk.scjst.gov.cn/QueryInfo/Ente/' + xxx
            'next_page_flag': u'//a[@disabled="disabled" and contains(text(), "下页")]/text()',
        },
        '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',

    }

    redis_tools = RedisTools()

    def start_requests(self):
        for link, _ in self.start_urls:
            yield scrapy.Request(link, callback=self.parse_list, meta={'cur_page': '1'},
                                 dont_filter=True)

    def parse_list(self, response):

        ext_rules = self.extract_dict['inner']
        nodes = response.xpath(ext_rules['nodes'])
        item_contains = []

        for node in nodes:
            item = NameItem()
            item['compass_name'] = self.handle_cname(node.xpath(ext_rules['cname']).extract_first())
            item['detail_link'] = self.handle_cdetail_link(node.xpath(ext_rules['detail_link']).extract_first())
            item['out_province'] = 'waisheng'
            if self.redis_tools.check_finger(item['compass_name']):
                print(u'{}已经爬取过'.format(item['compass_name']))
                continue
            item_contains.append(item)
        yield {'item_contains': item_contains}

        next_page_flag = response.xpath(ext_rules['next_page_flag'])
        meta = response.meta
        if not next_page_flag:
            print(u'当前页码:{}'.format(meta['cur_page']))
            yield self.turn_page(response)
        else:
            print(u'不能在翻页了, 当前最大页码:{}'.format(meta['cur_page']))
            return

    def turn_page(self, response):
        meta = response.meta
        headers = self.get_header(response.url, flag='2')
        meta['cur_page'] = str(int(meta['cur_page']) + 1)
        formdata = self.get_form_data(response)
        print(headers)
        return scrapy.FormRequest(response.url, formdata=formdata, callback=self.parse_list, headers=headers, meta=meta)

    def handle_cdetail_link(self, link, flag='inner', url=''):
        if link.startswith('.'):
            return link.replace('.', 'http://xmgk.scjst.gov.cn/QueryInfo/Ente/')
        else:
            return 'http://xmgk.scjst.gov.cn/QueryInfo/Ente/' + link

    def get_form_data(self, resp):
        meta = resp.meta
        formdata = {
            '__VIEWSTATE': resp.xpath(self.extract_dict['__VIEWSTATE']).extract_first(),
            '__EVENTVALIDATION': resp.xpath(self.extract_dict['__EVENTVALIDATION']).extract_first(),
            '__EVENTARGUMENT': meta['cur_page'],  # 实际是下一页的页码
            '__VIEWSTATEGENERATOR': 'E1A883C9',
            '__EVENTTARGET': 'ctl00$mainContent$gvPager',
            'ctl00$mainContent$txt_entname': '',
            'ctl00$mainContent$lx114': '',
            'ctl00$mainContent$cxtj': '',
            'UBottom1:dg1': '',
            'UBottom1:dg2': '',
            'UBottom1:dg3': '',
            'UBottom1:dg4': '',
            'UBottom1:dg5': '',
            'UBottom1:dg6': '',
        }
        return formdata


if __name__ == '__main__':
    SiChuanCompass().run()
