# coding=utf-8
import scrapy

from JianZhuProject import sit_list
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class XiZangCompass(BaseCompass):
    name = 'xizang_compass'
    allow_domain = ['111.11.196.111']
    custom_settings = {
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, },
        # 'ALL_FINGER_CONTAINS': 'finger_contains_new1_tmp'
    }
    start_urls = [
        ('http://111.11.196.111/aspx/corpinfo/CorpInfo.aspx?PageIndex=1', sit_list[1]),  #
    ]

    extract_dict = {
        'outer': {
            'nodes': '//div[@class="col-sm-12"][1]//tbody/tr',
            'cname': './/a[@href]/text()',
            'detail_link': './/a[@href]/@href',
            'out_province': './td[3]/text()',
        },
    }

    def handle_cdetail_link(self, clink, flag='inner', url=''):
        # ../../aspx/corpinfo/CorpDetailInfo.aspx?corpid=504893
        return clink.replace('../..', 'http://111.11.196.111')

    def turn_page(self, response):
        url = response.url
        page_num = int(url.split('PageIndex=')[-1])
        base_link = url.split('?')[0]
        next_link = base_link + '?' + 'PageIndex={}'.format(page_num + 1)
        headers = self.get_header(response.url)
        return scrapy.Request(next_link, headers=headers, callback=self.parse_list, meta=response.meta)

    def get_header(self, url, flag='1'):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            'Host': '111.11.196.111',
        }
        if flag not in (1, '1'):
            headers['Referer'] = url
        return headers


if __name__ == '__main__':
    XiZangCompass().run()
