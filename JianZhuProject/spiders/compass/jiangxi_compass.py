# coding=utf-8
import json

import scrapy
import re
from JianZhuProject import sit_list
from JianZhuProject.items import NameItem

from JianZhuProject.spiders.compass.base_compass import BaseCompass
import re


class JiangXiCompass(BaseCompass):
    name = 'jiangxi_compass'
    start_urls = [
        # ('http://jzsc.qhcin.gov.cn/dataservice/query/comp/list', sit_list[1]),
        ("http://59.52.254.106:8093/qualificationCertificateListForPublic", sit_list[0], 'inner1'),
        ("http://59.52.254.78/jxjsw/webSite/appInfo/entcredit.aspx", sit_list[0], 'inner2'),
        ("http://59.52.254.108:8093/acsOutNetQueryPageList", sit_list[0], 'inner1'),
        ("http://59.52.254.106:8893/outQueryEnterpriseAll", sit_list[1], 'inner3'),
        ("http://59.52.254.106:8893/outQueryBusinessList", sit_list[1], 'inner3'),
    ]
    allow_domain = ['59.52.254.106:8093', '59.52.254.78', '59.52.254.108:8093', '59.52.254.106:8893']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,}
    }
    cnt = 1
    # redis_tools = RedisTools()

    extract_dict = {
        'inner1': {  # acsOutNetQueryPageList  qualificationCertificateListForPublic
            'nodes': '//table[contains(@class, "listTable")]//tr[position()>2] | //table[contains(@class, "listTable")]/tbody[2]/tr[position()]',
            'cname': './td[2]/text()',
            'detail_link': './/a[@onclick]/@onclick',
            # winopen('/toViewQualificationForPublic?qualificationCertificate.id=34668629',1000,500,'详情');
            'out_province': ['None', 'jiangxi'],
        },
        'inner3': {  # outQueryEnterpriseAll、outQueryBusinessList:
            'nodes': '//table[contains(@class, "so_table")]//tr[position()>1]',
            'cname': './td[2]/text()',
            'detail_link': './/a[@onclick]/@onclick',
            # winopen('/outQuerySingleProject?applicationId=2333950',1000,600,'查看审批意见');
            'out_province': ['None', 'waisheng'],
        },
        'page_info1': '//a[contains(text(), "下页")]/@href',  # javascript:gotoPage(4);

        'inner2': {  # webSite
            'nodes': '//table[@class="News_List"]//tr[@class="GdItemStyle" or @class="GdAltStyle"]',
            'cname': './td[@class="firstCol"]//text()',
            'detail_link': './td[@class="firstCol"]/a/@href',
            # onclick="javascript:location.href='/dataservice/query/comp/compDetail/171221155516081987'"
            'out_province': ['None', 'jiangxi'],
        },
        'page_info2': '//script[contains(text(), "__pgfm")]/text()',

        '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        # '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',
        '__EVENTTARGET': '//input[@id="__EVENTTARGET"]/@value',
        '__EVENTARGUMENT': '//input[@id="__EVENTARGUMENT"]/@value',
        '__VIEWSTATEGENERATOR': '//input[@id="__VIEWSTATEGENERATOR"]/@value'
    }

    def start_requests(self):
        for link, sit, mark in self.start_urls:
            headers = self.get_headers(link, flag='1')
            meta = {'sit': sit, 'mark': mark, 'cur_page_num': 1}
            yield scrapy.Request(link, callback=self.parse_list, headers=headers, meta=meta)

    def parse_list(self, response):
        item_contains = []
        url = response.url
        meta = response.meta
        sit, mark = meta['sit'], meta['mark']
        ext_dict = self.extract_dict[mark]
        nodes = response.xpath(ext_dict['nodes'])
        for node in nodes:
            item = NameItem()
            item['compass_name'] = self.handle_cname(node.xpath(ext_dict['cname']).extract_first(), 'inner')
            item['detail_link'] = self.handle_cdetail_link(node.xpath(ext_dict['detail_link']).extract_first(),
                                                           'inner', url)
            item['out_province'] = ext_dict['out_province'][1] if isinstance(ext_dict['out_province'], list) else 'None'
            item_contains.append(item)

        yield {'item_contains': item_contains}

        yield self.turn_page(response)

    def turn_page(self, resp):
        link = resp.url
        meta = resp.meta
        headers = self.get_headers(link, flag='2')
        cur_page_num = resp.meta['cur_page_num']
        print('当前页:', cur_page_num)
        meta['cur_page_num'] = str(int(cur_page_num) + 1)
        if 'qualificationCertificateListForPublic' in resp.url:  # get
            url = link.split('?')[0] + '?pageIndex={}'.format(cur_page_num)
            return scrapy.Request(url, headers=headers, callback=self.parse_list, meta=meta)
        else:
            formdata = self.get_form_data(resp, flag='2')
            return scrapy.FormRequest(link, formdata=formdata, headers=headers, callback=self.parse_list)

    def get_headers(self, url, flag='1'):
        headers = {
            "Host": self.get_domain_inf(url, flag),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
        }
        if flag not in (1, '1'):
            headers['Origin'] = 'http://' + headers['Host']
            headers['refer'] = url
        return headers

    def handle_cdetail_link(self, clink, flag='inner', url=''):
        if 'queryPageDataFun' in clink:
            pp = re.compile(r",'(\w+)'")
            cname = re.search(pp, clink).group(1)
            clink = 'http://59.52.254.108:8093/acsOutRegistrationCertInfoList?q_applyMatterNum=new&q_corpName={}&q_administrativeCode='.format(
                cname)
        elif 'winopen' in clink:
            pp = re.compile(r"winopen\('(.*?)'")
            res = re.search(pp, clink).group(1)
            if res.startswith('/'):
                if 'outQuerySingleProject' in res:
                    clink = 'http://59.52.254.106:8893/' + res.replace('/', '')
                else:
                    clink = 'http://59.52.254.106:8093/' + res.replace('/', '')
            else:
                clink = 'http://59.52.254.106:8893/' + res
        elif clink.startswith('..'):
            clink = clink.replace('..', 'http://59.52.254.78/jxjsw/webSite')
        return clink

    def get_form_data(self, resp, flag):
        meta = resp.meta
        sit, mark = meta['sit'], meta['mark']
        if 'webSite' in resp.url:
            formdata = {
                "__EVENTTARGET": "_ctl0:ContentPlaceHolder1:Pager1:lb_Next",
                "__EVENTARGUMENT": resp.xpath(self.extract_dict['__EVENTARGUMENT']).extract_first(),
                "__VIEWSTATE": resp.xpath(self.extract_dict['__VIEWSTATE']).extract_first(),
                "__VIEWSTATEGENERATOR": resp.xpath(self.extract_dict['__VIEWSTATEGENERATOR']).extract_first(),
                "_ctl0:ContentPlaceHolder1:txtFEntName": "",
                "_ctl0:ContentPlaceHolder1:dbFEntType": "101",
                "_ctl0:ContentPlaceHolder1:txtCertiNo": "",
                "_ctl0:ContentPlaceHolder1:Pager1:txtGoto": "",
                "_ctl0:UBottom1:dg1": "",
                "_ctl0:UBottom1:dg2": "",
                "_ctl0:UBottom1:dg3": "",
                "_ctl0:UBottom1:dg4": "",
                "_ctl0:UBottom1:dg5": "",
                "_ctl0:UBottom1:dg6": "",
            }
            pass
        else:
            formdata = {
                'pageIndex': 2,
            }
        formdata = {

        }
        return ''

    def handle_out_province(self, s):
        return s.split('-')[0]

    def get_domain_inf(self, link, flag):
        # 根据link的开头特点需要进行重写
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        # import urlparse
        domain_str = link.split('//')[1].split('/')[0]
        return domain_str
        # res = urlparse.urlparse(link)
        # if flag in ('1', 1):
        #     return res.netloc
        # return res.scheme + '://' + res.netloc
        # return 'jzjg.gzjs.gov.cn:8088'


if __name__ == '__main__':
    JiangXiCompass().run()
