# coding=utf-8
import re
import scrapy
from scrapy import cmdline

from JianZhuProject import sit_list
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class GanShuCompass(BaseCompass):
    name = 'ganshu_compass'
    allow_domain = ['www.gsjs.gansu.gov.cn']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,}
    }
    log_file = '../logs/{}_log.log'.format(name)
    start_urls = [
        ('http://www.gsjs.gansu.gov.cn/index.aspx?tabid=8a907b00-5038-42a5-89e7-ab6c9a9f24de', sit_list[0]),  # 省内
        # ('http://www.gsjs.gansu.gov.cn/index.aspx?tabid=99deb541-340c-455f-858b-d1211036148e', sit_list[0])  # 省外
    ]

    extract_dict = {
        'inner': {
            'nodes': '//table[@class="datagrid2"]//tr[contains(@class, "itemstyleXX")]',
            'cname': './/td/a[contains(@onclick, "ItemID")]/text()',
            'detail_link': './/td/a[contains(@onclick, "ItemID")]/@onclick',
            'out_province': ['None', 'ganshu'],
        },
        'outer': {
            'nodes': '//table[@class="datagrid2"]//tr[contains(@class, "itemstyleXX")]',
            'cname': './td//text()',
            'detail_link': './td[contains(@onclick, "ItemID")]/@onclick',
            'out_province': '//select[@id="_ctl8_dprlRegionCode"]/option[(@value)]/text()',
            'out_province_no': '//select[@id="_ctl8_dprlRegionCode"]/option[contains(@value, "0")]/@value',
        },
        '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',
    }

    def parse_list(self, response):
        item_contains = []
        sit = response.meta['sit']
        if sit == sit_list[0]:
            inner_nodes = response.xpath(self.extract_dict['inner']['nodes'])
            inner = self.extract_dict['inner']
            for node in inner_nodes:
                item = NameItem()
                item['compass_name'] = self.handle_cname(node.xpath(inner['cname']).extract_first(), 'inner')
                item['detail_link'] = self.handle_cdetail_link(node.xpath(inner['detail_link']).extract_first(),
                                                               'inner')
                if self.redis_tools.check_finger(item['detail_link']):
                    print('{}已经爬取过'.format(item['detail_link']))
                    continue
                item['out_province'] = inner['out_province'][1] if isinstance(inner['out_province'],
                                                                              list) else 'None'
                item_contains.append(item)

        if sit == sit_list[1]:
            print(u'解析外省....')
            outer_nodes = response.xpath(self.extract_dict['outer']['nodes'])
            outer = self.extract_dict['outer']
            print("outer_nodes:", len(outer_nodes))
            for node in outer_nodes:
                item = NameItem()
                print(node.xpath(outer['cname']).extract_first())
                item['compass_name'] = self.handle_cname(node.xpath(outer['cname']).extract_first(), 'outer')
                item['detail_link'] = self.handle_cdetail_link(node.xpath(outer['detail_link']).extract_first(),
                                                               'outer')
                if self.redis_tools.check_finger(item['detail_link']):
                    print(u'{}已经爬取过'.format(item['detail_link']))
                    continue
                if isinstance(outer['out_province'], list) and len(outer['out_province']) > 1:
                    item['out_province'] = outer['out_province'][1]
                else:
                    item['out_province'] = self.handle_out_province(
                        node.xpath(outer['out_province']).extract_first())
                item_contains.append(item)
        yield {'item_contains': item_contains}

        yield self.turn_page(response)

    def start_requests(self):
        print('start_requests.....')
        headers = {
            "Connection": "keep-alive",
            "Host": "www.gsjs.gansu.gov.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        }
        for url, sit in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_entry, headers=headers,
                                 meta={'sit': sit, 'cur_page_num': '1'})

    def parse_entry(self, response):
        print('parse_entry...', response.meta['sit'])
        if response.meta['sit'] == sit_list[1]:
            out_province_no_list = response.xpath(self.extract_dict['outer']['out_province_no']).extract()
            for no in out_province_no_list:
                response.meta['province_no'] = no
                formdata = self.get_form_data(response)
                headers = self.get_headers(response.url)
                yield scrapy.FormRequest(response.url, callback=self.parse_list, formdata=formdata, headers=headers,
                                         meta=response.meta)
        else:
            formdata = self.get_form_data(response)
            headers = self.get_headers(response.url)

            yield scrapy.FormRequest(response.url, callback=self.parse_list, formdata=formdata, headers=headers,
                                     meta=response.meta)

    def turn_page(self, response):
        bt_status = response.xpath(u'//div[@class="PageSize"]/a[contains(text(), "下一页")]/@disabled').extract_first()
        if bt_status == 'disabled':
            print('不能翻页了')
        else:
            response.meta['cur_page_num'] = str(int(response.meta['cur_page_num']) + 1)
            formdata = self.get_form_data(response)
            headers = self.get_headers(response.url)
            print(headers)
            print(formdata)
            return scrapy.FormRequest(response.url, callback=self.parse_list, headers=headers, formdata=formdata,
                                      meta=response.meta)

    def get_form_data(self, rep):
        __VIEWSTATE = rep.xpath(self.extract_dict['__VIEWSTATE']).extract_first()
        __EVENTVALIDATION = rep.xpath(self.extract_dict['__EVENTVALIDATION']).extract_first()
        __VIEWSTATEGENERATOR = "90059987"

        # form_data = {
        #     '__VIEWSTATE': __VIEWSTATE,
        #     '__EVENTVALIDATION': __EVENTVALIDATION,
        #     '__VIEWSTATEGENERATOR': __VIEWSTATEGENERATOR,
        #     '__EVENTTARGET': '_ctl9$_ctl2',
        #     "_ctl9:dropAptitudeType": "",
        #     "_ctl9:tbEnterpriseName": "",
        #     "_ctl9:dprlRegionCode": rep.meta.get('province_no', "620000"),
        #     "_ctl9:_ctl4": "",
        #     "__EVENTARGUMENT": "",
        #     "__VIEWSTATEENCRYPTED": "",
        #     "_ctl9:btnDemand": ""
        # }
        meta = rep.meta
        form_data = {
            'Webb_Upload_Enable': 'False',
            '__EVENTTARGET': '_ctl9$_ctl2',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': __VIEWSTATE,
            '__VIEWSTATEGENERATOR': '90059987',
            '__VIEWSTATEENCRYPTED': '',
            '__EVENTVALIDATION': __EVENTVALIDATION,
            '_ctl9:dropAptitudeType': '',
            '_ctl9:tbEnterpriseName': '',
            '_ctl9:dprlRegionCode': '620000',
            '_ctl9:btnDemand': '',

        }
        if meta['cur_page_num'] < 2:
            form_data['_ctl8:_ctl0'] = form_data['_ctl8:_ctl1'] = form_data['_ctl8:_ctl2'] = form_data[
                '_ctl8:_ctl3'] = ''
        else:
            form_data['_ctl9:_ctl4'] = ''
        return form_data

    def get_headers(self, refer):
        headers = {
            "Host": "www.gsjs.gansu.gov.cn",
            "Origin": "http://www.gsjs.gansu.gov.cn",
            "Referer": refer,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        }
        return headers

    def handle_cdetail_link(self, link, flag='inner'):
        if flag == 'inner':
            pp = re.compile(r'(Desktop.*?)\'', re.S)
            link = 'http://www.gsjs.gansu.gov.cn/' + ''.join(re.search(pp, link).groups())
        return link


if __name__ == '__main__':
    cmdline.execute('scrapy crawl ganshu_compass'.split())
