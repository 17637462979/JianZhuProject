# coding=utf-8
import json

import scrapy
from lxml import etree
from scrapy import cmdline

from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass

sit_list = ['省内', '省外']
class LiaoLinCompass(BaseCompass):
    name = 'liaolin_compass'
    allow_domain = ['218.60.144.163']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,}
    }
    start_urls = [
        'http://218.60.144.163/LNJGPublisher/corpinfo/CorpInfo.aspx',
    ]
    redis_tools = RedisTools()

    inner_extract_dict = {
        'nodes': '//div[@id="div_Province"]//tr[@class="odd" or @class="even"]',
        'cname': './td[contains(@class, "company_name")]/@title',
        'detail_link': './td[contains(@class, "company_name")]/a[contains(@onclick, "OpenCorpDetail")]/@onclick',
        'out_province': 'None'
    }

    outer_extract_dict = {
        'nodes': '//div[@id="div_outCast"]//tr[@class="odd" or @class="even"]',
        'detail_link': './td[last()]/a[contains(@onclick, "onshow")]/@onclick',
        'cname': './td[2]/text()',
        'out_province': './td[4]/text()'
    }

    def start_requests(self):
        headers = {
            'Accept':'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
            'Referer': 'http://cx.jljsw.gov.cn/corpinfo/CorpInfo.aspx',
            'Host': 'cx.jljsw.gov.cn',
        }
        for link, sit in self.start_urls:
            yield scrapy.Request(link, headers=headers, callback=self.parse_list)

    def parse_list(self, response):
        item_contains = []

        node1 = response.xpath(self.inner_extract_dict['nodes'])
        node2 = response.xpath(self.outer_extract_dict['nodes'])
        for node in node1:
            inner_item = NameItem()
            inner_item['compass_name'] = self.handle_cname(node.xpath(self.inner_extract_dict['cname']).extract_first())
            inner_item['detail_link'] = self.handle_cdetail_link(node.xpath(self.inner_extract_dict['detail_link']).extract_first())
            inner_item['out_province'] = 'liaolin'
            if not self.redis_tools.check_finger(inner_item['detail_link']):
                item_contains.append(inner_item)
            else:
                print('{}已经爬取过'.format(inner_item['detail_link']))

        for node in node2:
            outer_item = NameItem()
            outer_item['compass_name'] = self.handle_cname(node.xpath(self.outer_extract_dict['cname']).extract_first())
            outer_item['detail_link'] = self.handle_cdetail_link(
                node.xpath(self.outer_extract_dict['detail_link']).extract_first())
            outer_item['out_province'] = node.xpath(self.outer_extract_dict['out_province']).extract_first()

            if not self.redis_tools.check_finger(outer_item['detail_link']):
                item_contains.append(outer_item)
            else:
                print('{}已经爬取过'.format(outer_item['detail_link']))

        yield {'item_contains': item_contains}

        # 翻页
        total_page = int(json_data['nPageCount'])
        cur_page = int(json_data['nPageIndex'])

        if int(total_page) > int(cur_page):
            print('翻页....')
            next_page = cur_page + 1
            mpara = 'SnCorpData' if sit == sit_list[0] else 'SwCorpData'
            next_link = 'http://cx.jljsw.gov.cn/handle/NewHandler.ashx?method={}&nPageIndex={}&nPageSize=20'.format(mpara, next_page)
            response.meta['cur_page'] = next_page
            yield scrapy.Request(next_link, callback=self.parse_list, meta=response.meta)
        else:
            print('不能继续翻页了,当前页码:', cur_page)

    def handle_cname(self, cname):
        """
        处理公司名称
        :param cname: 字符串公司名
        :return: 干净的名字
        """
        return cname

    def handle_cdetail_link(self, clink):
        """
        处理进入公司详细页的链接
        :param clink: 字符串链接, 最原始
        :return: 直接能够使用的链接,（无论是post还是get）
        """
        if clink.startswith('http'):
            good_link = clink
        else:
            domain_str = 'http://cx.jljsw.gov.cn'  # 待重写，domain_str可变, 结尾一定没有/
            if clink.startswith('..'):
                good_link = clink.replace('..', domain_str, 1)
            elif clink.startswith('.'):
                good_link = clink.replace('.', domain_str, 1)
            elif clink.startswith('/'):
                good_link = domain_str + clink
            else:
                print('请重写该方法')
                good_link = ''
        return good_link


    def handles_province(self, cprovice):
        """
        处理省份信息
        :param cprovice:
        :return: 只有省信息
        """
        pass

if __name__ == '__main__':
    cmdline.execute('scrapy crawl jilin_compass'.split())