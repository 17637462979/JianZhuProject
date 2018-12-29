# coding=utf-8
import scrapy
import re
from JianZhuProject import sit_list
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class ZheJiangCompass(BaseCompass):
    name = 'zhejiang_compass'
    allow_domain = ['115.29.2.37:8080']
    custom_settings = {
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, },
        # 'ALL_FINGER_CONTAINS': 'finger_contains_new1_tmp'
    }
    start_urls = [
        ('http://115.29.2.37:8080/enterprise_ajax.php', sit_list[0]),  #
    ]

    extract_dict = {
        'inner': {
            'nodes': '//table[@class="t1"]/tr[@class="auto_h"]',
            'cname': './/a[@title]/@title',
            'detail_link': './/a[@title]/@href',  # "enterprise_detail.php?CORPCODE=72811462-5"
            'out_province': ['None', 'zhejiang'],
            'turn_page_no': u'//div[@id="pagebar"]//li[contains(text(), "下一页")]/@alt',
            'last_page_no': u'//div[@id="pagebar"]//li[contains(text(), "尾页")]/@alt'
        },
    }
    cnt = 1
    repeat = 0

    def turn_page(self, response):
        url = response.url

        next_page_no = response.xpath(self.extract_dict['inner']['turn_page_no']).extract_first()
        last_page_no = response.xpath(self.extract_dict['inner']['last_page_no']).extract_first()
        if next_page_no == last_page_no and self.repeat >= 1:
            print('不能继续翻页了，当前最大页码:', next_page_no)
            print(response.text)
            return
        elif next_page_no == last_page_no and self.repeat < 2:
            self.repeat += 1
        print('第%s页' % self.cnt)
        self.cnt += 1
        headers = self.get_header(response.url, flag='2')
        meta = response.meta

        formdata = self.get_form_data(response)
        return scrapy.FormRequest(url, headers=headers, formdata=formdata, callback=self.parse_list, meta=meta)

    def get_header(self, url, flag='1'):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            'Host': '115.29.2.37:8080',
        }
        if flag not in (1, '1'):
            headers['Origin'] = 'http://' + headers['Host']
            headers['Referer'] = url
        return headers

    def get_form_data(self, resp):
        page_no = resp.xpath(self.extract_dict['inner']['turn_page_no']).extract_first()
        headers = {
            "page": page_no,
            "CorpName": "",
            "APTITUDEKINDNAME": "",
            "CertID": "",
            "City": "",
            "EndDate": "",
        }
        return headers

    def handle_cdetail_link(self, clink, flag='outer', url=''):
        link = clink if clink.startswith('http') else 'http://115.29.2.37:8080/' + clink
        return link

        # def handle_out_province(self, s):
        #     s = s.replace(u'\xb7', '-').split('-')[0]
        #     return s.strip('\r\n\t ')


if __name__ == '__main__':
    ZheJiangCompass().run()
