
# coding=utf-8
from __future__ import print_function

import re

import requests
from lxml import etree

from JianZhuProject.items import QualityItem, CompassItem
from JianZhuProject.spiders.base_template import ParentSpider
from JianZhuProject.spiders.extract.extract_qualification import ExtractQualification

Postion = ['ListPage', 'DetailPage', 'QualPage', 'ProjPage', 'StaffPage']


class ExtractQual(ExtractQualification):
    def extract_qualification_info(self, resp_detail, qual_rules):
        link = resp_detail.url
        # 'http://www.ahgcjs.com.cn:3318/pub/query/comp/compCaList/130901181300704576'
        url = link.replace('showCompInfo', 'compCaList')
        headers = {
            "Host": "www.ahgcjs.com.cn:3318",
            "Referer": url,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        }
        resp = requests.get(url, headers=headers)
        html = etree.HTML(resp.content)
        node = html.xpath(qual_rules.get('qnodes')[0])[0]
        qtype_li = node.xpath(qual_rules['qtype'][0])
        # print('\t\tqtype_li', len(qtype_li))
        qcode_li = node.xpath(qual_rules['qcode'][0])
        # print('\t\tqcode_li', len(qcode_li))
        qname_li = node.xpath(qual_rules['qname'][0])
        # print('\t\tqname_li', len(qname_li))
        qend_date_li = node.xpath(qual_rules['qend_date'][0])
        # print('\t\tqend_date_li', len(qend_date_li))
        qauthority_li = node.xpath(qual_rules['qauthority'][0])
        # print('\t\tqauthority_li', len(qauthority_li))
        qual_items = []
        for qtype, qcode, qname, qend_date, qauthority in zip(qtype_li, qcode_li, qname_li, qend_date_li, qauthority_li):
            for qn in qname.strip().split('级')[:-1]:
                item = QualityItem({
                    'quality_type': self.fmt_qtype(qtype),
                    'quality_code': qcode.strip('\t\n\r '),
                    'quality_name': qn + '级',
                    'quality_start_date': None,
                    'quality_end_date': self.fmt_time_str(qend_date),
                    'quality_detail_link': None,
                    'authority': qauthority.strip('\t\n\r '),
                })
                qual_items.append(item)
        return qual_items

    def fmt_time_str(self, ts):
        ts = ts.strip('\t\n\r ')
        if '年' in ts:
            pp = re.compile(ur'至(\d+)年(\d+)月(\d+)日', re.S)    # 注意需要使用ur
            return  '-'.join(re.search(pp, ts).groups())
        else:
            return ts

    def fmt_qtype(self, qtype):
        # "showDZZS('170630083608304519','建筑施工');"
        if 'showDZZS' in qtype:
            pp = re.compile(r".*?,'(.*)'\)")
            qtype = re.search(pp, qtype).group(1)
        return qtype


class AnHuiSpider(ParentSpider):
    name = 'an_hui_spider'
    custom_settings = {
        'ITEM_PIPELINES' : {'JianZhuProject.pipelines.JianzhuprojectPipeline': 300,}
    }
    allowed_domains = ['www.ahgcjs.com.cn:3318', 'www.ahgcjs.com.cn']
    start_urls = ['http://www.ahgcjs.com.cn:3318/pub/query/comp/compPubCaList/all/111120164101726998?flag=1']
    extract_dict = {
        'list_page': {
            'lines_rule': '//table[@class="inquiry_listhei"]//tr',
            'detail_link_rule': './td[2]/a[@class="actbar-btn"]/@href',  # 相对相对
            'have_next_page_rule': '//script[contains(text(), "__pgfm")]/text()',  # 返回一个bool值，标志是否还可翻页
            'next_page_rule': '//script[contains(text(), "__pgfm")]/text()',  # 绝对路径
            'total_page_num_rule': '//script[contains(text(), "__pgfm")]/text()',  # 列表页的总页码, 绝对路径  # __pgfm('',{"$total":19776,"$pgsz":15,"$pg":3,"$reload":0})
            'method': 'POST',
        },
        'detail_page': {
            'method': 'GET',
            'compass': {
                'cnodes': ['//div[@class="inquiry_listcont"]/table'],   #
                'cname': [u'.//td[contains(@class,"inquiry") and contains(text(), "企业名称")]/following-sibling::*[1]/text()', 'compass_name'],
                # 'clink': '',
                'chonor_code': [u'.//td[contains(@class,"inquiry") and contains(text(), "执照编号")]/following-sibling::*[1]/text()', 'honor_code'],
                'clegal_person': [u'.//td[contains(@class,"inquiry") and contains(text(), "代表人")]/following-sibling::*[1]/text()', 'representative'],
                'ctype': [u'.//td[contains(@class,"inquiry") and contains(text(), "登记类型")]/following-sibling::*[1]/text()', 'compass_type'],
                'cprovince': [u'.//td[contains(@class,"inquiry") and contains(text(), "注册地")]/following-sibling::*[1]/text()', 'provice'],
                'coperation_addr': [u'.//td[contains(@class,"inquiry") and contains(text(), "注册地址")]/following-sibling::*[1]/text()', 'operating_addr'],
                'cestablish_time': [u'.//td[contains(@class,"inquiry") and contains(text(), "注册日期")]/following-sibling::*[1]/text()', 'establish_time'],
                'cregister_capital': [None, 'register_capital'],
                'cnet_asset': [None, 'net_asset']
            },
            'qualification': {
                'qnodes': [u'//table//td[contains(text(), "企业资质")]/../..'],
                'qtype': [u'.//img[@alt="电子证书"]/@onclick', 'quality_type'],
                'qcode': [u'.//td[contains(@class,"inquiry") and contains(text(), "证书编号")]/following-sibling::td[1]/text()',
                    'quality_code'],
                'qname': [u'.//td[contains(@class,"inquiry") and contains(text(), "资质内容")]/following-sibling::td[1]/text()',
                    'quality_name'],
                'qstart_date': [None, 'quality_start_date'],
                'qend_date': [u'.//td[contains(@class,"inquiry") and contains(text(), "有效日期")]/following-sibling::td[1]/text()',
                    'quality_end_date'],
                'qdetail_link': [None, 'quality_detail_link'],
                'qauthority': [u'.//td[contains(@class,"inquiry") and contains(text(), "发证机关")]/following-sibling::td[1]/text()',
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

    extq = ExtractQual()
    def get_headers(self, url, link, position):
        """
        获取前往详细页面的headers
        :param url: 列表页的url(当前)
        :param position: 哪个位置的headers
        :param link: 如果是DetailPage，link是详细页的url; 如果是ListPage，link=url
        :return:
        """
        if position == Postion[1]:
            headers = {
                "Host": "www.ahgcjs.com.cn:3318",
                "Referer": url,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
            }
        elif position == Postion[0]:
            headers = {
                "Host": "www.ahgcjs.com.cn:3318",
                "Referer": url,
                'Origin': self.get_domain_info(url),
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
            }
        else:
            headers = {

            }
        return headers

    def extract_compass_info(self, resp_detail, com_rules):
        response = resp_detail
        node = response.xpath(com_rules.get('cnodes')[0])[0]
        company_item = CompassItem()
        company_item['compass_link'] = response.url

        for k, v in com_rules.items():
            if 'node' in k:
                continue
            rule, map_key = v[0], v[1]
            if v[0] is None:
                company_item[map_key] = ''
            else:
                company_item[map_key] = node.xpath(rule).extract_first().replace('\n', '').replace('\t', '').replace('\r', '').replace('  ', '')
                if k == 'cname':
                    company_item[map_key] = self.fmt_cname(company_item[map_key])
                    print('cname--->:', map_key, company_item[map_key])
        return [company_item]

    def extract_qualification_info(self, resp_detail, qual_rules):
        # http://www.ahgcjs.com.cn:3318/pub/query/comp/compBadCredit/130901181300704576
        quali_items = self.extq.extract_qualification_info(resp_detail, qual_rules)
        return quali_items

    def get_project_link(self, resp_detail, compass_items):
        # http://www.ahgcjs.com.cn:3318/pub/query/comp/compPerfList/130901181300704576
        link = resp_detail.url
        link = link.replace('showCompInfo', 'compPerfList')
        return link

    def get_staff_link(self, resp_detail, compass_items):
        # http://www.ahgcjs.com.cn:3318/pub/query/comp/showRegPersonList/130901181300704576
        link = resp_detail.url
        link = link.replace('showCompInfo', 'showRegPersonList')
        return link

    def get_behavior_link(self, resp_detail, compass_items):
        # http://www.ahgcjs.com.cn:3318/pub/query/comp/compWellCredit/130901181300704576
        link = resp_detail.url
        link = link.replace('showCompInfo', 'compWellCredit')
        return link

    def get_change_link(self, resp_detail, compass_items):
        return ''

    def judge_next_page(self, resp):
        # __pgfm('',{"$total":19792,"$pgsz":15,"$pg":3,"$reload":0})
        cur_page_num = resp.meta.get('cur_page_num', '1')
        total_page = resp.meta.get('total_page', None)
        if not total_page:
            total_page, total = self.get_total_page(resp)
        return int(cur_page_num) < int(total_page)

    def get_form_data(self, response, postion):
        cur_page = response.meta.get('cur_page', '1')
        total_page = response.meta.get('total_page', None)
        if not total_page:
            total_page, total = self.get_total_page(response)
        formdata = {
            "$total": str(int(total_page) * 15),
            "$pgsz": "15",
            "$pg": str(int(cur_page)+1),
            "$reload": "0"
        }
        return formdata

    def get_total_page(self, resp):
        js_str = resp.xpath(self.extract_dict['list_page']['have_next_page_rule'])[0].extract()
        pp = re.compile(ur'(\{.*\})', re.S)
        json_page = eval(str(re.search(pp, js_str).group()))
        cur_page, total_page = json_page['$pg'], int(json_page['$total']) / int(json_page['$pgsz'])
        print('json_page:', cur_page, total_page)
        return total_page, json_page['$total']

    def fmt_cname(self, cname):
        tar_str = ['（', '）', '】', '【', '-', '', '']
        if '】' in cname:
            cname = cname.split('】')[-1]
        return cname



if __name__ == '__main__':
    an_hui = AnHuiSpider()
    an_hui.run()