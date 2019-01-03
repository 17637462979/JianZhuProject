# coding=utf-8
import json
import random

import scrapy
import time

from lxml import etree

from JianZhuProject import sit_list
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class JiangSuCompass(BaseCompass):
    name = 'jiangsu_compass'
    allow_domain = ['58.213.147.230:7001']
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, }
    }
    log_file = '../logs/{}_log.log'.format(name)
    cnt = 1
    start_urls = [
        ('http://58.213.147.230:7001/Jsjzyxyglpt/faces/public/companyies.jsp?qylx=jlqy', sit_list[0])
    ]

    extract_dict = {
        'inner': {
            'nodes': '//table[@mainbody]//tr[@onclick]',
            'cname': './td[2]/div[@title]/nobr//text()',
            'detail_link': './td[2]/div[@title]//a[contains(@href, "corp")]/@href',
            # 'http://xmgk.scjst.gov.cn/QueryInfo/Ente/' + xxx
            'next_page_flag': u'//a[@disabled="disabled" and contains(text(), "下页")]/text()',
        },
        'view': '//input[@name="com.sun.faces.VIEW"]/@value',
    }

    redis_tools = RedisTools()

    def start_requests(self):
        for link, _ in self.start_urls:
            yield scrapy.Request(link, callback=self.parse_list, meta={'cur_page': '1', 'total_page_num': 35},
                                 dont_filter=True)

    def parse_list(self, response):

        ext_rules = self.extract_dict['inner']
        nodes = response.xpath(ext_rules['nodes'])
        item_contains = []

        for node in nodes:
            item = NameItem()
            item['compass_name'] = self.handle_cname(node.xpath(ext_rules['cname']).extract_first())
            item['detail_link'] = self.handle_cdetail_link(node.xpath(ext_rules['detail_link']).extract_first())
            item['out_province'] = 'jiangsu'
            if self.redis_tools.check_finger(item['compass_name']):
                print(u'{}已经爬取过'.format(item['compass_name']))
                continue
            item_contains.append(item)
        yield {'item_contains': item_contains}

        meta = response.meta
        if int(meta['total_page_num']) > int(meta['cur_page']):
            print(u'当前页码:{}'.format(meta['cur_page']))
            yield self.turn_page(response)
        else:
            print(u'不能在翻页了, 当前最大页码:{}'.format(meta['cur_page']))
            return

    def turn_page(self, response):
        meta = response.meta
        headers = self.get_header(response.url, flag='2')
        if int(meta['cur_page']) % 10:
            time.sleep(random.random() * 4)
        meta['cur_page'] = str(int(meta['cur_page']) + 1)
        formdata = self.get_form_data(response)
        return scrapy.FormRequest(response.url, formdata=formdata, callback=self.parse_list, headers=headers, meta=meta)

    def handle_cdetail_link(self, link, flag='inner', url=''):
        # javascript:newWindow('jlqy/basicInfoView.jsp?action=viewJlqyJbxx&corpCode=71629845-5',1024,0,'jlqyView');
        # http://58.213.147.230:7001/Jsjzyxyglpt/faces/public/jlqy/basicInfoView.jsp?action=viewJlqyJbxx&corpCode=71628806-2
        import re
        pp = re.compile(r"\('(.*?)'\);")
        _ = re.search(pp, link).group(1)
        return 'http://58.213.147.230:7001/Jsjzyxyglpt/faces/public/' + _

    def get_form_data(self, resp):
        meta = resp.meta
        formdata = {
            'projectWinSelectedTabPageIndex': '1',
            'basicWinSelectedTabPageIndex': '1',
            'peopleWinSelectedTabPageIndex': '1',
            'form:refreshAct': '',
            'form:page': meta['cur_page'],
            'form:_id0': 'jlqy',
            'form:_id2': '',
            'form:_id3': '',
            'form:_id4': '',
            'form:checkCode': '',
            'pageSize': '30',
            'com.sun.faces.VIEW': resp.xpath(self.extract_dict['view']).extract_first(),
            'form': 'form',
        }
        return formdata


if __name__ == '__main__':
    JiangSuCompass().run()
