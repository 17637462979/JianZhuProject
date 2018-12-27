# -*- coding: utf-8 -*-
import scrapy

from JianZhuProject.items import CompassItem, QualityItem
from JianZhuProject.spiders.base_template import ParentSpider


class JilinSpdier(ParentSpider):
    name = 'ji_lin_spider'
    allowed_domains = ['cx.jljsw.gov.cn']
    start_urls = ['http://cx.jljsw.gov.cn/handle/NewHandler.ashx?method=SnCorpData&nPageIndex=1&nPageSize=20']

    extract_dict = {
        'list_page': {
            'lines_rule': '//table[@class="inquiry_listhei"]//tr',
            'detail_link_rule': './td[2]/a[@class="actbar-btn"]/@href',  # 相对相对
            'have_next_page_rule': '//script[contains(text(), "__pgfm")]/text()',  # 返回一个bool值，标志是否还可翻页
            'next_page_rule': '//script[contains(text(), "__pgfm")]/text()',  # 绝对路径
            'total_page_num_rule': '//script[contains(text(), "__pgfm")]/text()',
        # 列表页的总页码, 绝对路径  # __pgfm('',{"$total":19776,"$pgsz":15,"$pg":3,"$reload":0})
            'method': 'POST',
        },
        'detail_page': {
            'method': 'GET',
            'compass': {
                'cnodes': ['//div[@class="details_content"]//table[@class="cpd_basic_table"]'],  #
                'cname': [
                    u'.//td[@class="name_level3"]/text()','compass_name'],
                # 'clink': '',
                'chonor_code': [u'.//td[@id="LicenseNum"]/text()','honor_code'],
                'clegal_person': [u'.//td[@id="LegalMan"]/text()','representative'],
                'ctype': [u'.//td[@id="EconType"]/text()','compass_type'],
                'cprovince': [u'.//td[@id="Td1"]/text()','provice'],
                'coperation_addr': [u'.//td[@id="Description"]/text()','operating_addr'],
                'cestablish_time': [u'.//td[@id="CorpBirthDate"]/text()','establish_time'],
                'cregister_capital': [u'.//td[@id="RegPrin"]/text()', 'register_capital'],
                'cnet_asset': [None, 'net_asset']
            },
            'qualification': {
                'qnodes': [u'//table//td[contains(text(), "企业资质")]/../..'],
                'qtype': [u'.//img[@alt="电子证书"]/@onclick', 'quality_type'],
                'qcode': [
                    u'.//td[contains(@class,"inquiry") and contains(text(), "证书编号")]/following-sibling::td[1]/text()',
                    'quality_code'],
                'qname': [
                    u'.//td[contains(@class,"inquiry") and contains(text(), "资质内容")]/following-sibling::td[1]/text()',
                    'quality_name'],
                'qstart_date': [None, 'quality_start_date'],
                'qend_date': [
                    u'.//td[contains(@class,"inquiry") and contains(text(), "有效日期")]/following-sibling::td[1]/text()',
                    'quality_end_date'],
                'qdetail_link': [None, 'quality_detail_link'],
                'qauthority': [
                    u'.//td[contains(@class,"inquiry") and contains(text(), "发证机关")]/following-sibling::td[1]/text()',
                    'authority']
            },
            'project': {
                'pnodes': '',
                'pcode': '',
                'pname': '',
                'psite': '',
                'ptype': '',
                'employer': '',
                'pdetail_link': '',
                'plink': '',
            },
            'staff': {
                'snodes': '',
                'sname': '',
                'sid_card': '',
                'stitle': '',
                'stitle_code': '',
                'sprofession': '',
                'sdetail_link': '',
                'slicence_stime': '',
                'slicence_etime': '',
            },
            'change': {
                'ch_nodes': '',
                'ch_time': '',
                'ch_content': '',
                'other_msg': '',
            },
            'behavior': {
                'bnodes': '',
                'brecord_id': '',
                'bcontent': '',
                'bexecutor': '',
                'bpublish_stime': '',
                'bpublish_etime': '',
                'bbody': '',
                'btype': '',
            }
        }
    }

    def parse_detail(self, response):

        compass_items = self.get_company_info(response)
        quality_items = self.get_qualification_info(response)
        quality_items = self.get_project_info(response)

    def get_company_info(self, response):
        nodes = response.xpath('//div[@class="basic_infor"]//tbody/tr')
        company_item = CompassItem({   # 自动检查key是否合法
             'compass_name': nodes.xpath('./td[@class="name_level3"]').extract()[0],
             'compass_link': response.url,
             'honor_code': nodes.xpath('./td[@id="LicenseNum"]').extract()[0],   # 信用代码
             'representative': nodes.xpath('./td[@id="LegalMan"]').extract()[0],  # 法人
             'compass_type': nodes.xpath('./td[@id="EconType"]').extract()[0],   # 公司类型
             'provice': ''.join(nodes.xpath('./td[@id="Td1"]').extract()),
             'operating_addr': ''.join(nodes.xpath('./td[@id="Description"]')),   # 运营地址
             'establish_time': None,
             'register_capital': None,
             'net_asset': None,
        })
        return [company_item]

    def get_qualification_info(self, response):
        # html = etree.HTML(txt_str)
        qua_types = response.xpath('//div[@class="details_infor_content_01"]/div[@class="leibie"]//text()')
        content_nodes = response.xpath('//div[@class="details_infor_content_01"]/table')
        item_list = []
        for i, node in enumerate(content_nodes):
            quality_code, quality_start_date = node.xpath('.//td[@class="col_01_value"]/text()')
            authority, quality_end_date = node.xpath('.//td[@class="col_02_value"]/text()')
            quality_name = node.xpath('.//td[@title]/@title').extract()[0]
            item = QualityItem({'quality_type': qua_types[i],
                     'quality_code': quality_code,
                     'quality_name': quality_name,
                     'quality_start_date': quality_start_date,
                     'quality_end_date': quality_end_date,
                     'quality_detail_link': None,
                     'authority': authority,
                     })
            item_list.append(item)
        return item_list

    def get_project_info(self, response):
        
        base_link = 'http://218.60.144.163/LNJGPublisher/handle/Corp_Project.ashx?CorpCode=91210300941265393L&CorpName=鞍钢房产建设有限公司&nPageSize=30&nPageIndex={}'

        pass