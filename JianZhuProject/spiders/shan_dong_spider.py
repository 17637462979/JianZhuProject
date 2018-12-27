# -*- coding: utf-8 -*-
import codecs
import datetime
import logging
import time

import requests
import scrapy
import re
import os
from scrapy import cmdline

from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import CompassItem, QualityItem, JianzhuprojectItem
from JianZhuProject.settings import ALL_FINGER_CONTAINS
import urllib

now_date_time = datetime.datetime.now()


class ShanDongSpider(scrapy.Spider):
    name = 'shan_dong_spider'
    allowed_domains = ['www.sdjs.gov.cn', '221.214.94.41']
    start_urls = ['http://221.214.94.41:81/InformationReleasing/Ashx/InformationReleasing.ashx']

    redis_tools = RedisTools()

    pp = re.compile(r'\((.*)\)', re.S)

    def start_requests(self):
        url = self.start_urls[0] + '/' + self.get_query_string(1)
        yield scrapy.Request(url, callback=self.parse, headers=self.get_headers())

    def parse(self, response):
        url = response.url
        txt_str = response.text
        print url
        data = eval(re.search(self.pp, txt_str).group(1))
        detail_link = 'http://221.214.94.41:81/InformationReleasing/Ashx/InformationReleasing.ashx?callback=jQuery17108474795947085398&methodname=GetCorpQualificationCertInfo&CorpCode={}&CurrPageIndex=1&PageSize=5'
        for unit in data['data']['CorpInfoList']:
            url1 = 'http://www.sdjs.gov.cn/xyzj/DTFront/ZongHeSearch/Detail_Company.aspx?CorpCode={}&searchType=0'.format(unit['LegalMan'])
            headers = {
                'Referer': url1,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            }
            detail_url = detail_link.format(unit['LegalMan'])

            compass_items = self.parse_compass_info(unit, url1)
            quality_items = self.get_qualification_info(unit, detail_url, headers)
            print JianzhuprojectItem({
                'compass_items': compass_items,
                'qualification_items': quality_items,
                'project_items': None,
                'staff_items': None,
                'change_items': None,
                'behavior_items': None,
                'crawl_time': self.fmt_time(),
                'source_link': url,
                'compass_name': compass_items[0]['compass_name'],
                'honor_code': compass_items[0]['honor_code'],
                'other': None,
            })
            break

    def parse_compass_info(self, unit, url):
        company_item = CompassItem({  # 自动检查key是否合法
            'compass_name': unit['CorpName'],
            'compass_link': url,
            'honor_code': unit['CorpCode'],  # 信用代码
            'representative': unit['LegalMan'],  # 法人
            'compass_type': unit['EconomicNum'],  # 公司类型
            'provice': ''.join(unit['AreaName'].split('·')[:1]),
            'operating_addr': unit['Address'],  # 运营地址
            'establish_time': 'None',
            'register_capital': unit['RegPrin'],
            'net_asset': None,
        })
        return [company_item]

    def get_qualification_info(self, unit, url, headers):
        response = requests.get(url, headers=headers)
        txt_str = response.content
        qua_data = eval(re.search(self.pp, txt_str).group(1))
        _, __, ___ = unit['QualificationScope'], unit['CertCode'],unit['DanWeiType']
        quality_name_list, quality_code_list, quality_type_list = _.split(';'), __.split(';'), ___.split(';')
        item_list = [QualityItem({'quality_type': qtype,
                                'quality_code': qcode,
                                'quality_name': qname.replace('（新）', '').replace('(新)', ''),
                                'quality_start_date': 'None',
                                'quality_end_date': 'None',
                                'quality_detail_link': None,
                                'authority': 'None',
                                }) for (qname, qcode, qtype) in zip(quality_name_list, quality_code_list, quality_type_list) if qcode.upper()[0] in ['A', 'B', 'C']]
        return item_list

    def fmt_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    def get_headers(self):
        headers = {
            'Referer': 'http://www.sdjs.gov.cn/xyzj/DTFront/ZongHeSearch/Detail_Company.aspx?CorpCode=913716261671905552&searchType=0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
        }
        return headers

    def get_query_string(self, cur_page):
        query_dict = {
            "callback": "jQuery17106983271474465658",
            "methodname": "GetCorpInfo",
            "CurrPageIndex": str(cur_page),
            "PageSize": "12",
        }
        return urllib.urlencode(query_dict)


if __name__ == '__main__':
    cmdline.execute(['scrapy', 'crawl', ShanDongSpider.name])

