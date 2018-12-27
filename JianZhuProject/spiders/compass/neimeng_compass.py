# coding=utf-8
import json
from lxml import etree

import scrapy
import re
from JianZhuProject import sit_list
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class NeiMongCompass(BaseCompass):
    name = 'neimong_compass'
    allow_domain = ['110.16.70.26']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,},
        # 'ALL_FINGER_CONTAINS': 'finger_contains_new1_tmp'
    }
    start_urls = [
        (
        'http://110.16.70.26/nmjgpublisher/handle/ProjectsInfoHandler.ashx?type=CorpInfo&lblPageCount={total_page}&lblPageIndex={cur_page}&lblRowsCount={total_rows}&lblPageSize=20',
        sit_list[0]),  #
    ]

    extract_dict = {
        'inner': {
            'nodes': '//tr',
            'cname': './a[contains(@onclick, "OnReturn")]/text()',
            'detail_link': './a[contains(@onclick, "OnReturn")]/@onclick',
        # "OnReturn('911508001172071957','巴彦淖尔市第三建筑有限责任公司')"
            'out_province': ['None', 'neimonggu'],
        },
    }

    def parse_list(self, response):

        json_resp = json.loads(response.text)
        total_page = json_resp['nPageCount']
        total_rows = json_resp['nPageRowsCount']
        cur_page_num = json_resp['nPageIndex']
        html_str = json_resp['tb']

        item_contains = []
        html = etree.HTML(html_str, 'lxml')
        nodes = html.xpath(self.extract_dict['inner']['nodes'])
        for node in nodes:
            item = NameItem()
            item['cname'] = node.xpath(self.extract_dict['inner']['cname']).extract_first()
            item['detail_link'] = self.handle_cdetail_link(
                node.xpath(self.extract_dict['inner']['detail_link']).extract_first())
            item['out_province'] = self.extract_dict['inner']['out_province'][1]
            item_contains.append(item)
        yield item_contains

        if int(cur_page_num) < int(total_page):
            self.turn_page(response)
        else:
            print('不能再翻页了，当前页码:', cur_page_num)
            print(response.text)
            return

    def turn_page(self, response):
        url = response.url
        next_page_no = response.xpath(self.extract_dict['inner']['turn_page_no']).extract_first()
        last_page_no = response.xpath(self.extract_dict['inner']['last_page_no']).extract_first()
        if next_page_no == last_page_no:
            print('不能继续翻页了，当前最大页码:', next_page_no)
            return
        headers = self.get_header(response.url, flag='2')
        meta = response.meta

        return scrapy.Request(url, headers=headers, callback=self.parse_list, meta=meta)

    def get_header(self, url, flag='1'):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            'Host': '110.16.70.26',
            'Referer': url
        }
        # if flag not in (1, '1'):
        #     headers['Referer'] = url
        return headers

    def handle_cdetail_link(self, clink, flag='outer', url=''):
        # OnReturn('91152202743857259K','阿尔山市白狼天原林产有限责任公司')
        import re
        pp = re.compile(r"OnReturn\('(.*?)','(.*?)'\);")
        [CorpCode, cname] = re.findall(pp, clink)[0]
        link = 'http://110.16.70.26/nmjgpublisher/corpinfo/CorpDetailInfoObtain.aspx?CorpCode={}&CorpName={}&VType=1'.format(
            CorpCode, cname)
        return link


if __name__ == '__main__':
    NeiMongCompass().run()
