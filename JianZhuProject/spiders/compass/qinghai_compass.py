# coding=utf-8
import json

import scrapy
import re
from JianZhuProject import sit_list
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class QingHaiCompass(BaseCompass):
    name = 'qinghai_compass'
    allow_domain = ['jzsc.qhcin.gov.cn']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,}
    }
    cnt = 1
    start_urls = [
        # ('http://jzsc.qhcin.gov.cn/dataservice/query/comp/list', sit_list[1]),
        ('http://jsy.xjjs.gov.cn/dataservice/query/comp/list', sit_list[1])
    ]
    # redis_tools = RedisTools()

    extract_dict = {
        'outer': {
            'nodes': '//div[@class="mtop"]//tbody//tr[@onclick]',
            'cname': './td[3]/text()',
            'detail_link': './@onclick',
        # onclick="javascript:location.href='/dataservice/query/comp/compDetail/171221155516081987'"
            'out_province': './td[last()]/text()',  # 青海省-西宁市-城东区
        },
        'page_info': '//script[contains(text(), "__pgfm")]/text()'
    }

    def turn_page(self, response):
        meta = response.meta
        if 'total_pgae_num' not in meta or 'cur_page_num' not in meta:
            page_str = response.xpath(self.extract_dict['page_info']).extract_first()
            pp = re.compile(r'.*?,(.*)\)')
            page_info = eval(re.search(pp, page_str).group(1))
            total_pgae_num = (int(page_info['$total']) + int(page_info['$pgsz']) - 1) / int(page_info['$pgsz'])
            cur_page_num = meta['cur_page_num'] = str(page_info['$pg'])
            meta['total_page_num'] = str(page_info['$total'])
            meta['page_size'] = str(page_info['$pgsz'])
        else:
            total_pgae_num = meta['total_pgae_num']
            cur_page_num = meta['cur_page_num']
        if int(total_pgae_num) <= int(cur_page_num):
            print('不能继续翻页了, 当前最大页码:', cur_page_num)
            return
        meta['cur_page_num'] = str(int(cur_page_num) + 1)
        headers = self.get_header(response.url)
        formdata = self.get_form_data(response)
        self.cnt += 1
        print('第{}次翻页'.format(self.cnt))
        return scrapy.FormRequest(response.url, headers=headers, formdata=formdata, callback=self.parse_list, meta=meta)

    def get_header(self, url, flag='1'):
        headers = {
            "Host": self.get_domain_info(url),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
            "Origin": 'http://' + self.get_domain_info(url),
            'refer': url
        }
        return headers

    def handle_cdetail_link(self, clink, flag='inner', url=''):
        # "javascript:location.href='/dataservice/query/comp/compDetail/170821133514681163'"
        if clink.startswith('http'):
            good_link = clink
        else:
            pp = re.compile(r"href='(.*)'")
            good_link = 'http://jzsc.qhcin.gov.cn' + re.search(pp, clink).group(1)
        return good_link

    def get_form_data(self, resp):
        meta = resp.meta
        formdata = {
            '$pg': meta['cur_page_num'],
            '$reload': '0',
            '$total': meta['total_page_num'],
            '$pgsz': meta['page_size'],
        }
        return formdata

    def handle_out_province(self, s):
        return s.split('-')[0]

    def get_domain_info(self, link):
        # 根据link的开头特点需要进行重写
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        import urlparse
        res = urlparse.urlparse(link)
        return res.netloc
        # return 'jzjg.gzjs.gov.cn:8088'


if __name__ == '__main__':
    QingHaiCompass().run()
