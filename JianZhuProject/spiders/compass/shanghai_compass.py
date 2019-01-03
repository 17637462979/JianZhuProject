# coding=utf-8
import json

import scrapy
import time

from lxml import etree

from JianZhuProject import sit_list
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class ShangHaiCompass(BaseCompass):
    name = 'shanghai_compass'
    allow_domain = ['']
    custom_settings = {
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, }
    }
    log_file = '../logs/{}_log.log'.format(name)
    cnt = 1
    start_urls = [
        ('http://www.ciac.sh.cn/SHCreditInfoInterWeb/CreditBookAnounce/GetQyCreditReportAll?page=-1', sit_list[0])
    ]

    extract_dict = {
        'inner': {
            'nodes': '//table[contains(@class, "tablelist")]/tbody/tr',
            'cname': './td[2]/text()',
            'detail_link': 'None',
        },
    }

    redis_tools = RedisTools()

    def start_requests(self):
        for link, _ in self.start_urls:
            yield scrapy.Request(link, callback=self.parse_list, meta={'cur_page': '1'},
                                 dont_filter=True)

    def parse_list(self, response):

        data = json.loads(response.text)['resultdata']
        html = etree.HTML(data)
        ext_rules = self.extract_dict['inner']
        nodes = html.xpath(ext_rules['nodes'])
        item_contains = []
        for node in nodes:
            item = NameItem()
            item['compass_name'] = self.handle_cname(node.xpath(ext_rules['cname'])[0])
            item['detail_link'] = 'None'
            item['out_province'] = 'waisheng'
            if self.redis_tools.check_finger(item['compass_name']):
                print(u'{}已经爬取过'.format(item['compass_name']))
                continue
            item_contains.append(item)
        yield {'item_contains': item_contains}

        total_page_num = html.xpath('//label[@id="zongyeshu"]/text()')[0]
        meta = response.meta
        if int(total_page_num) > int(meta['cur_page']):
            print(u'当前页码:{}'.format(meta['cur_page']))
            yield self.turn_page(response)
        else:
            print(u'不能在翻页了, 当前最大页码:{}'.format(meta['cur_page']))
            return

    def turn_page(self, response):
        meta = response.meta
        headers = self.get_header(response.url, flag='2')
        formdata = self.get_form_data(response)
        meta['cur_page'] = str(int(meta['cur_page']) + 1)

        return scrapy.FormRequest(response.url, formdata=formdata, callback=self.parse_list, headers=headers, meta=meta)

    def handle_cname(self, cname, flag='inner'):
        return cname.replace('企业基本信息', '').strip('\n\t\r ')

    def handle_cdetail_link(self, link, flag='inner', url=''):
        if 'javascript:window' in link:
            import re
            pp = re.compile(r"\('(.*?)'\)")
            return 'http://218.14.207.72:8082/PublicPage/' + re.search(pp, link).group(1)
        if link.startswith('.'):
            return link.replace('.', 'http://zjj.jiangmen.gov.cn/public/licensing')
        else:
            return 'http://www.stjs.org.cn/xxgk/' + link

    def get_form_data(self, resp):
        meta = resp.meta
        formdata = {
            'mainZZ': '0',
            'aptText': '',
            'areaCode': '0',
            'entName': '',
            'pageSize': '10',
            'pageIndex': str(meta['cur_page']),
        }
        return formdata


if __name__ == '__main__':
    ShangHaiCompass().run()
