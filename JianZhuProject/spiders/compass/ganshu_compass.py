# coding=utf-8
import re
import scrapy
from scrapy import cmdline

from JianZhuProject import sit_list
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class GanShuCompass(BaseCompass):
    name = 'ganshu_compass'
    allow_domain = ['www.gsjs.gansu.gov.cn']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,}
    }
    start_urls = [
        # ('http://www.gsjs.gansu.gov.cn/index.aspx?tabid=8a907b00-5038-42a5-89e7-ab6c9a9f24de', sit_list[0]),   # 省内
        ('http://www.gsjs.gansu.gov.cn/index.aspx?tabid=99deb541-340c-455f-858b-d1211036148e', sit_list[1])  # 省外
    ]

    extract_dict = {
        'inner': {
            'nodes': '//table[@class="datagrid2"]/tr[contains(@class, "itemstyleXX")]',
            'cname': './/td/a[contains(@onclick, "ItemID")]/text()',
            'detail_link': './/td/a[contains(@onclick, "ItemID")]/@onclick',
            'out_province': ['None', 'ganshu'],
        },
        'outer': {
            'nodes': '//table[@class="datagrid2"]/tr[contains(@class, "itemstyleXX")]',
            'cname': './td//text()',
            'detail_link': './td[contains(@onclick, "ItemID")]/@onclick',
            'out_province': '//select[@id="_ctl8_dprlRegionCode"]/option[(@value)]/text()',
            'out_province_no': '//select[@id="_ctl8_dprlRegionCode"]/option[contains(@value, "0")]/@value',
        },
        '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',
    }

    def start_requests(self):
        print('start_requests.....')
        headers = {
            "Connection": "keep-alive",
            "Host": "www.gsjs.gansu.gov.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        }
        for url, sit in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_entry, headers=headers, meta={'sit': sit})

    def parse_entry(self, response):
        print('parse_entry...', response.meta['sit'])
        if response.meta['sit'] == sit_list[1]:
            out_province_no_list = response.xpath(self.extract_dict['outer']['out_province_no']).extract()
            for no in out_province_no_list:
                response.meta['province_no'] = no
                formdata = self.get_form_data(response)
                headers = self.get_headers()
                yield scrapy.FormRequest(response.url, callback=self.parse_list, formdata=formdata, headers=headers,
                                         meta=response.meta)
        else:
            formdata = self.get_form_data(response)
            headers = self.get_headers()

            yield scrapy.FormRequest(response.url, callback=self.parse_list, formdata=formdata, headers=headers,
                                     meta=response.meta)

    def turn_page(self, response):
        bt_status = response.xpath('//div[@class="PageSize"]/a[contains(text(), "下一页")]/@disabled').extract_first()
        if bt_status == 'disabled':
            print('不能翻页了')
        else:
            formdata = self.get_form_data(response)
            headers = self.get_headers()
            yield scrapy.FormRequest(response.url, callback=self.parse_list, headers=headers, formdata=formdata)

    def get_form_data(self, rep):
        print('get_form_data', rep.meta.get('province_no', "620000"))
        __VIEWSTATE = rep.xpath(self.extract_dict['__VIEWSTATE']).extract_first()
        __EVENTVALIDATION = rep.xpath(self.extract_dict['__EVENTVALIDATION']).extract_first()
        __VIEWSTATEGENERATOR = "90059987"
        form_data = {
            '__VIEWSTATE': __VIEWSTATE,
            '__EVENTVALIDATION': __EVENTVALIDATION,
            '__VIEWSTATEGENERATOR': __VIEWSTATEGENERATOR,
            '__EVENTTARGET': '_ctl9$_ctl2',
            "_ctl9:dropAptitudeType": "",
            "_ctl9:tbEnterpriseName": "",
            "_ctl9:dprlRegionCode": rep.meta.get('province_no', "620000"),
            "_ctl9:_ctl4": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATEENCRYPTED": "",
            "_ctl9:btnDemand": ""
        }

        return form_data

    def get_headers(self):
        headers = {
            "Host": "www.gsjs.gansu.gov.cn",
            "Origin": "http://www.gsjs.gansu.gov.cn",
            "Referer": "http://www.gsjs.gansu.gov.cn/index.aspx?tabid=8a907b00-5038-42a5-89e7-ab6c9a9f24de",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        }
        return headers

    def handle_cdetail_link(self, link, flag='inner'):
        if flag == 'inner':
            pp = re.compile(r'(Desktop.*?)\'', re.S)
            print(type(link))
            print(type(''.join(re.search(pp, link).groups())))
            link = 'http://www.gsjs.gansu.gov.cn/' + ''.join(re.search(pp, link).groups())
        return link


if __name__ == '__main__':
    cmdline.execute('scrapy crawl ganshu_compass'.split())
