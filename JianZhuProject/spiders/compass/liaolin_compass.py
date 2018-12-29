# coding=utf-8
import json

import scrapy
from lxml import etree
from scrapy import cmdline

from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass
import re

sit_list = ['省内', '省外']
class LiaoLinCompass(BaseCompass):
    name = 'liaolin_compass'
    allow_domain = ['218.60.144.163']
    custom_settings = {
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, }
    }
    start_urls = [
        'http://218.60.144.163/LNJGPublisher/corpinfo/CorpInfo.aspx',
    ]
    log_file = '../logs/{}_log.log'.format(name)
    redis_tools = RedisTools()

    inner_extract_dict = {
        'nodes': '//div[@id="div_Province"]//tr[@class="odd" or @class="even"]',
        'cname': './td[contains(@class, "company_name")]/@title',
        'detail_link': './td[contains(@class, "company_name")]/a[contains(@onclick, "OpenCorpDetail")]/@onclick',
        'out_province': 'None',

        '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',
    }

    outer_extract_dict = {
        'nodes': '//div[@id="div_outCast"]//tr[@class="odd" or @class="even"]',
        'detail_link': './td[last()]/a[contains(@onclick, "onshow")]/@onclick',
        # onshow('30a48514-d54e-4a38-bafd-0d05296f1a01')
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
        for link in self.start_urls:
            yield scrapy.Request(link, headers=headers, callback=self.parse_list, meta={'cur_page_num': 1})

    def parse_list(self, response):
        item_contains = []

        node1 = response.xpath(self.inner_extract_dict['nodes'])
        node2 = response.xpath(self.outer_extract_dict['nodes'])
        try:
            for node in node1:
                inner_item = NameItem()
                inner_item['compass_name'] = self.handle_cname(
                    node.xpath(self.inner_extract_dict['cname']).extract_first())
                inner_item['detail_link'] = self.handle_cdetail_link(
                    node.xpath(self.inner_extract_dict['detail_link']).extract_first())
                inner_item['out_province'] = 'liaolin'
                if not self.redis_tools.check_finger(inner_item['detail_link']):
                    item_contains.append(inner_item)
                else:
                    print('{}已经爬取过'.format(inner_item['detail_link']))

            for node in node2:
                outer_item = NameItem()
                outer_item['compass_name'] = self.handle_cname(
                    node.xpath(self.outer_extract_dict['cname']).extract_first())
                outer_item['detail_link'] = self.handle_cdetail_link(
                    node.xpath(self.outer_extract_dict['detail_link']).extract_first())
                outer_item['out_province'] = self.handle_out_province(
                    node.xpath(self.outer_extract_dict['out_province']).extract_first())

                if not self.redis_tools.check_finger(outer_item['detail_link']):
                    item_contains.append(outer_item)
                else:
                    print(u'{}已经爬取过'.format(outer_item['detail_link']))
        except Exception as e:
            with open(self.log_file, 'wa') as fp:
                fp.write(str(e))
        yield {'item_contains': item_contains}

        # 翻页
        meta = response.meta
        cur_page_num = meta['cur_page_num']
        next_page_flag = response.xpath('//a[@id="Linkbutton3" and contains(@class, "aspNetDisabled")]').extract()
        if next_page_flag:
            print(u'不能继续翻页了，当前最大页码:')
            return
        print(u'翻页....')
        next_page = int(cur_page_num) + 1
        meta['cur_page_num'] = str(next_page)
        headers = self.get_header(response.url, flag='2')
        formdata = self.get_form_data(response)
        yield scrapy.FormRequest(response.url, formdata=formdata, callback=self.parse_list, meta=meta, headers=headers)


    def handle_cdetail_link(self, clink):
        """
        处理进入公司详细页的链接
        :param clink: 字符串链接, 最原始
        :return: 直接能够使用的链接,（无论是post还是get）
        """

        if 'OpenCorpDetail' in clink:
            pp = re.compile(ur"OpenCorpDetail\('(.*?)','(.*?)','(.*)'\)")
            [rowGuid, CorpCode, CorpName] = re.search(pp, clink).groups()
            good_link = 'http://218.60.144.163/LNJGPublisher/corpinfo/CorpDetailInfo.aspx?rowGuid={}&CorpCode={}&CorpName={}&VType=1'.format(
                rowGuid, CorpCode, CorpName)
        else:
            pp = re.compile(ur"onshow\('(.*?)'")
            fid = re.search(pp, clink).group(1)
            good_link = 'http://218.60.144.163/LNJGPublisher/corpinfo/outCaseCorpDetailInfo.aspx?Fid=' + fid
        return good_link

    def get_form_data(self, resp):
        formdata = {
            '__VIEWSTATE': resp.xpath(self.inner_extract_dict['__VIEWSTATE']).extract_first(),
            '__EVENTVALIDATION': resp.xpath(self.inner_extract_dict['__EVENTVALIDATION']).extract_first(),
            'hidd_type': '1',
            'txtCorpName': '',
            'ddlZzlx': '',
            'txtFOrgCode': '',
            'txtCertNum': '',
            'newpage': resp.meta['cur_page_num'],
            'newpage1': '',
            '__EVENTTARGET': 'Linkbutton3',
            '__EVENTARGUMENT': '',
        }
        return formdata

    def handle_out_province(self, s):
        return s.strip('\r\n\t ')

if __name__ == '__main__':
    LiaoLinCompass().run()
