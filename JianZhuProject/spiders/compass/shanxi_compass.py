# coding=utf-8
import json

import scrapy
import re
from JianZhuProject import sit_list
from JianZhuProject.items import NameItem

from JianZhuProject.spiders.compass.base_compass import BaseCompass
import re


class ShanXiCompass(BaseCompass):
    name = 'shanxi_compass'
    start_urls = [
        ("http://js.shaanxi.gov.cn:9010/SxApp/share/WebSide/ZZCXList.aspx?fcol=800019", sit_list[0], 'inner1'),
        ("http://js.shaanxi.gov.cn:9010/SxApp/share/WebSide/ZZCXList.aspx?fsid=150", sit_list[0], 'inner1'),
        ("http://js.shaanxi.gov.cn:9010/SxApp/share/WebSide/ZZCXList.aspx?fsid=175", sit_list[0], 'inner1'),  # 质量检测机构
        ("http://js.shaanxi.gov.cn:9010/SxApp/share/WebSide/ZZCXList.aspx?fcol=80001919&fsid=202", sit_list[0],
         'inner1'),
        #
        (
        'http://124.115.170.171:7001/PDR/network/informationSearch/informationSearchList?pageNumber=1&libraryName=enterpriseLibrary',
        sit_list[0], 'inner2'),
        (
        'http://124.115.170.171:7001/PDR/network/informationSearch/informationSearchzbList?pageNumber=2&libraryName=enterpriseLibrary',
        sit_list[0], 'inner2'),
        #
        ("http://js.shaanxi.gov.cn:9010/SxApp/share/WebSide/ZZCXSGList.aspx?fsid=180", sit_list[1], 'inner3'),
        # # 外省进陕施工企业
        ("http://js.shaanxi.gov.cn:9010/SxApp/share/WebSide/ZZCXSGList.aspx?fsid=325", sit_list[1], 'inner3'),
        # # 外省进陕监理企业
        ("http://js.shaanxi.gov.cn:9010/SxApp/share/WebSide/ZZCXSGList.aspx?fsid=320", sit_list[1], 'inner3'),
        # 外省入陕招标企业
    ]
    allow_domain = ['59.52.254.106:8093', '59.52.254.78', '59.52.254.108:8093', '59.52.254.106:8893',
                    'js.shaanxi.gov.cn:9010']
    custom_settings = {
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, }
    }
    cnt = 1
    # redis_tools = RedisTools()

    extract_dict = {
        'inner1': {
            'nodes': '//table[@class="ch_dglit" or @class="m_dg1"]//tr[contains(@class,"ch_Grid") or contains(@class, "m_dg1")][position()>1]//td[2]',
            'cname': './text()',
            'detail_link': None,  # None
            'out_province': ['None', 'shangxi'],
            '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
            '__VIEWSTATEGENERATOR': '//input[@id="__VIEWSTATEGENERATOR"]/@value',
            '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',
        },
        'inner2': {
            'nodes': '//table[contains(@id, "enterprise")]//tr[position()>1]',
            'cname': './td[2]/@title',
            'detail_link': './td[2]//a[@onclick]/@onclick',
            'out_province': ['None', 'shanxi'],
        },
        'inner3': {
            'nodes': '//table[@class="m_dg1" or @class="ch_dglit"]//tr[contains(@class,"ch_Grid") or contains(@class, "m_dg1")][position()>1]/td[2]',
            'cname': './text()',
            'detail_link': None,
            'out_province': ['None', 'waisheng'],
            '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
            '__VIEWSTATEGENERATOR': '//input[@id="__VIEWSTATEGENERATOR"]/@value',
            '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',
        }
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
        print('nodes:', len(nodes))
        for node in nodes:
            item = NameItem()
            item['compass_name'] = self.handle_cname(node.xpath(ext_dict['cname']).extract_first(), 'inner')
            if ext_dict['detail_link']:
                item['detail_link'] = self.handle_cdetail_link(node.xpath(ext_dict['detail_link']).extract_first(),
                                                               'inner', url)
            else:
                item['detail_link'] = 'None'

            item['out_province'] = ext_dict['out_province'][1] if isinstance(ext_dict['out_province'], list) else 'None'
            if not self.redis_tools.check_finger(item['compass_name']):
                item_contains.append(item)
            else:
                print(u'{}已经抓取过了'.format(item['compass_name']))

        yield {'item_contains': item_contains}

        yield self.turn_page(response)

    def turn_page(self, resp):
        link = resp.url
        meta = resp.meta
        headers = self.get_headers(link, flag='2')

        if 'qualificationCertificateListForPublic' in resp.url:  # get
            url = link.split('?')[0] + '?pageIndex={}'.format(cur_page_num)
            return scrapy.Request(url, headers=headers, callback=self.parse_list, meta=meta)
        else:
            if not resp.xpath(
                    u'//a[@id="Pager1_lb_Next"]/@href | //a[not(@id) and @onclick="pageNext()" and contains(text(), "下一页")]/@onclick | //a[contains(text(), "下一页")]').extract_first():
                print(u'不能继续翻页了')
                return
            cur_page_num = resp.meta['cur_page_num']
            print(u'当前页:{}'.format(cur_page_num))
            meta['cur_page_num'] = str(int(cur_page_num) + 1)
            if meta['mark'] != 'inner2':
                form_data = self.get_form_data(resp, flag='2')
                return scrapy.FormRequest(link, formdata=form_data, headers=headers, callback=self.parse_list,
                                          meta=meta)
            else:
                link = 'http://124.115.170.171:7001/PDR/network/informationSearch/informationSearchzbList?pageNumber={}&libraryName=enterpriseLibrary'.format(
                    meta['cur_page_num'])
                return scrapy.FormRequest(link, headers=headers, callback=self.parse_list, meta=meta, dont_filter=True)

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
        if 'vie1' in clink:
            # vie1('安徽兴邦建筑工程有限公司','ab3ef43f-07fc-4e23-bfbd-8f5c9daa39ae' ,'9134010067892467X8','')
            # http://124.115.170.171:7001/PDR/network/Enterprise/Informations/view?enid={enid}&name={name}&org_code={org_code}&type=
            pp = re.compile(r"vie1\((.*?)\)")
            (enid) = re.search(pp, clink).group(1).replace("'", "").split(",")[0]
            clink = 'http://124.115.170.171:7001/PDR/network/Enterprise/Informations/view?enid={}'.format(enid)

        return clink

    def get_form_data(self, resp, flag):
        meta = resp.meta
        sit, mark = meta['sit'], meta['mark']
        ext_dict = self.extract_dict[mark]

        formdata = {
            '__VIEWSTATE': resp.xpath(ext_dict['__VIEWSTATE']).extract_first(),
            '__VIEWSTATEGENERATOR': resp.xpath(ext_dict['__VIEWSTATEGENERATOR']).extract_first(),
            '__EVENTVALIDATION': resp.xpath(ext_dict['__EVENTVALIDATION']).extract_first(),
            'txtFName': '',
            'txtFCertiNo': '',
        }
        if mark == 'inner1':
            formdata.update({
                '__EVENTTARGET': 'Pager1$lb_Next',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
                'Pager1$NavPage': '',
            })
        if mark == 'inner3':
            formdata.update({
                '__EVENTTARGET': 'Pager1',
                '__EVENTARGUMENT': resp.meta['cur_page_num'],
            })
        return formdata

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
    ShanXiCompass().run()
