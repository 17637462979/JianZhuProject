# -*- coding: utf-8 -*-
import sys
import time

import scrapy, urllib
from scrapy import cmdline
import sys
reload(sys) # Python2.5 初始化后删除了 sys.setdefaultencoding 方法，我们需要重新载入
sys.setdefaultencoding('utf-8')

from JianZhuProject.items import CompassItem, QualityItem, JianzhuprojectItem


class LiaoLingSpdier(scrapy.Spider):
    name = 'liao_ling_spdier'
    allowed_domains = ['218.60.144.163']
    start_urls = ['http://218.60.144.163/LNJGPublisher/corpinfo/CorpInfo.aspx']

    def start_requests(self):

        yield scrapy.Request(url=self.start_urls[0], callback=self.parse_list)

    def parse_list(self, response):

        line_links = response.xpath(
            '//div[@id="div_Province"]//tbody/tr/td[contains(@class, "company_name")]/a/@onclick').extract()
        print line_links
        for link in line_links:
            link = self.get_link(link)
            print link
            headers = {
                "Host": "218.60.144.163",
                "Referer": "http://218.60.144.163/LNJGPublisher/corpinfo/CorpInfo.aspx",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
            }
            yield scrapy.Request(url=link, headers=headers, callback=self.parse_detail)
        # 下一页参数
        url = response.url
        cur_page = response.meta.get('cur_page', 1)
        form_data = self.get_form_data(response, cur_page)
        headers = self.get_headers()
        print 'fanye.......{}'.format(cur_page)
        yield scrapy.FormRequest(url, callback=self.parse_list, form_data=form_data, headers=headers, meta={'cur_page': cur_page+1})


    def parse_detail(self, response):

        compass_items = self.get_company_info(response)
        quality_items = self.get_qualification_info(response)
        # quality_items = self.get_project_info(response)
        compass_name = compass_items[0]['compass_name']
        honor_code = compass_items[0]['honor_code']

        project_link = 'http://218.60.144.163/LNJGPublisher/handle/Corp_Project.ashx?CorpCode={}&CorpName={}&nPageCount=30&nPageSize=30'.format(honor_code, compass_name)   # 返回的结果数自行动态调整

        # ".." + encodeURI('9121030094127066XN') + "&CorpName=" + encodeURI('鞍钢厂容绿化筑路有限公司') + "&type=3",
        staff_link = 'http://218.60.144.163/LNJGPublisher/handle/Company_Details_CertifiedEngineers.ashx?CorpCode={}&CorpName={}&type=3'.format(honor_code, compass_name)
        behavior_link = 'http://218.60.144.163/LNJGPublisher/handle/Corp_Credit.ashx?CorpCode?CorpCode={}&CorpName={}'.format(
            honor_code, compass_name)

        is_same = self.get_same([project_link, staff_link, behavior_link])

        yield JianzhuprojectItem({
               'compass_items': compass_items,
               'qualification_items': quality_items,
               'project_items': None,
               'staff_items': None,
               'change_items': None,
               'behavior_items': None,
               'crawl_time': self.fmt_time(),
               'source_link': response.url,
               'compass_name': compass_items[0]['compass_name'],
               'honor_code': compass_items[0]['honor_code'],
               # 'quality_link': response.url,

               'project_link': project_link,
               'staff_link': staff_link,
               'behavior_link': behavior_link,
               'is_same': '',
        })


    def get_company_info(self, response):
        nodes = response.xpath('//div[@class="basic_infor"]//tbody/tr')
        compass_name = nodes[0].xpath('./td[@class="name_level3"]/text()').extract_first().strip()
        honor_code = nodes[1].xpath('./td[@id="LicenseNum"]/text()').extract_first().strip()
        representive = nodes[2].xpath('./td[@id="LegalMan"]/text()').extract_first().strip()
        compass_type = nodes[2].xpath('./td[@id="EconType"]/text()').extract_first().strip()
        provice = nodes[3].xpath('./td[@id="Td1"]/text()').extract_first().strip()
        operating_addr = nodes[3].xpath('./td[@id="Description"]').extract_first().strip()
        company_item = CompassItem({   # 自动检查key是否合法
             'compass_name': compass_name,
             'compass_link': response.url,
             'honor_code': honor_code,   # 信用代码
             'representative': representive,  # 法人
             'compass_type': compass_type,   # 公司类型
             'provice': provice,
             'operating_addr': operating_addr,   # 运营地址
             'establish_time': None,
             'register_capital': None,
             'net_asset': None,
        })
        return [company_item]

    def get_qualification_info(self, response):
        # html = etree.HTML(txt_str)
        qua_types = response.xpath('//div[@class="details_infor_content_01"]/div[@class="leibie"]//text()').extract()
        content_nodes = response.xpath('//div[@class="details_infor_content_01"]/table')
        item_list = []
        for i, node in enumerate(content_nodes):
            quality_code, quality_start_date = node.xpath('.//td[@class="col_01_value"]/text()').extract()
            authority, quality_end_date = node.xpath('.//td[@class="col_02_value"]/text()').extract()
            quality_name = node.xpath('.//td[@title]/@title').extract()[0]
            item = QualityItem({
                     'quality_type': qua_types[i],
                     'quality_code': quality_code,
                     'quality_name': quality_name,
                     'quality_start_date': quality_start_date,
                     'quality_end_date': quality_end_date,
                     'quality_detail_link': None,
                     'authority': authority,
                     })
            item_list.append(item)
        return item_list

    # def get_project_info(self, response):
    #     base_link = 'http://218.60.144.163/LNJGPublisher/handle/Corp_Project.ashx?CorpCode=91210300941265393L&CorpName=鞍钢房产建设有限公司&nPageSize=30&nPageIndex={}'
    #
    #     pass

    def get_form_data(self, response, cur_page):
        __VIEWSTATE = response.xpath('//input[@id="__VIEWSTATE"]/@value').extract_first()
        __EVENTVALIDATION = response.xpath('//input[@id="__EVENTVALIDATION"]/@value').extract_first()
        hidd_type = "1"
        newpage = str(int(cur_page) + 1)
        __EVENTTARGET = "Linkbutton3"
        return {"__VIEWSTATE": __EVENTVALIDATION, "__EVENTVALIDATION": __EVENTVALIDATION, "hidd_type": hidd_type, "newpage": newpage, "__EVENTTARGET": __EVENTTARGET}

    def get_headers(self):
        headers = {
            "Host": "218.60.144.163",
            "Origin": "http://218.60.144.163",
            "Pragma": "no-cache",
            "Referer": "http://218.60.144.163/LNJGPublisher/corpinfo/CorpInfo.aspx",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        }
        return headers

    def get_link(self, link):
        import re
        pp = re.compile(r'OpenCorpDetail\((.*)\)')
        _ = re.search(pp, link).groups()[0]
        [rowGuid, CorpCode, CorpName] = _.replace('\'', '').split(',')

        query_str = {
            'rowGuid': rowGuid,
            'CorpCode': CorpCode,
            'CorpName': CorpName,
        }
        # py2 need setdefaultencoding, else return none
        link = 'http://218.60.144.163/LNJGPublisher/corpinfo/CorpDetailInfo.aspx?' + urllib.urlencode(query_str)
        return link

    def fmt_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    def get_same(self):

        return ''

if __name__ == '__main__':
    cmdline.execute(['scrapy ', 'crawl', LiaoLingSpdier.name])