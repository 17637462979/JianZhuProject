# coding=utf-8
import json

import scrapy
import re
from JianZhuProject import sit_list
from JianZhuProject.items import NameItem

from JianZhuProject.spiders.compass.base_compass import BaseCompass


class HuNanCompass(BaseCompass):
    name = 'hunan_compass'
    allow_domain = ['www.hunanjz.com', 'qyryjg.hunanjz.com']
    custom_settings = {
        'DOWNLOAD_DELAY': 0.9,
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, }
    }

    start_urls = [
        # ('http://www.hunanjz.com/Html/QyxxList.aspx?lb=1', sit_list[0]),   # 完整
        # ('http://www.hunanjz.com/Html/QyxxList.aspx?lb=2', sit_list[0]),
        # ('http://www.hunanjz.com/Html/QyxxList.aspx?lb=3', sit_list[0]),   # 缺38 = 871-836

        # ('http://qyryjg.hunanjz.com/public/EnterpriseList.aspx', 'ctl00_ContentPlaceHolder1_btn_1'),   # 完整
        ('http://qyryjg.hunanjz.com/public/EnterpriseList.aspx', 'ctl00_ContentPlaceHolder1_btn_2'),
        ('http://qyryjg.hunanjz.com/public/EnterpriseList.aspx', 'ctl00_ContentPlaceHolder1_btn_7'),
        ('http://qyryjg.hunanjz.com/public/EnterpriseList.aspx', 'ctl00_ContentPlaceHolder1_btn_5'),
        ('http://qyryjg.hunanjz.com/public/EnterpriseList.aspx', 'ctl00_ContentPlaceHolder1_btn_zjzx'),
        ('http://qyryjg.hunanjz.com/public/EnterpriseList.aspx', 'ctl00_ContentPlaceHolder1_btn_sgtsc'),
        ('http://qyryjg.hunanjz.com/public/EnterpriseList.aspx', 'ctl00_ContentPlaceHolder1_btn_jcqy'),
        ('http://qyryjg.hunanjz.com/public/EnterpriseList.aspx', 'ctl00_ContentPlaceHolder1_btn_aqsc'),
        ('http://qyryjg.hunanjz.com/public/EnterpriseList.aspx', 'ctl00_ContentPlaceHolder1_btn_ws'),
    ]
    extract_dict = {
        'inner': {
            'nodes': '//td[contains(@id, "qylist")]/table[not(@id)]//tr[position()>1] | //div[contains(@id, "div_list") and @class="div_main"]/table[@id="table"]/tr[position()>1]',
            'cname': './/a[contains(@href, ".aspx?")]/text()',
            'detail_link': './/a[contains(@href, ".aspx?")]/@href',  # Qy_sgqydetail.aspx?id=1
            'out_province': ['None', 'hunan'],

        },
        '__EVENTARGUMENT': '//input[@id="__EVENTARGUMENT"]/@value',
        '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        '__VIEWSTATEGENERATOR': '//input[@id="__VIEWSTATEGENERATOR"]/@value',
        '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',
        'next_pgae_flag': u'//a[@disabled="disabled" and contains(text(), "下一页")]',
    }

    def start_requests(self):

        for link, para in self.start_urls:
            headers = self.get_header(link, flag='1')
            yield scrapy.Request(link, headers=headers, callback=self.parse_list,
                                 meta={'sit': sit_list[0], 'para': para, 'cur_page_num': '1'})
        pass

    def turn_page(self, response):

        next_flag = response.xpath(self.extract_dict['next_pgae_flag']).extract
        meta = response.meta
        cur_page_num = meta['cur_page_num']
        if not next_flag:
            print(u'不能继续翻页了, 当前最大页码:', cur_page_num)
            return
        if not response.body_as_unicode():
            print(u'返回响应体为空,{}\n{}'.format(response.body_as_unicode(), cur_page_num))
        formdata = self.get_form_data(response)
        headers = self.get_header(response.url, flag='2')
        meta['cur_page_num'] = str(int(cur_page_num) + 1)

        print(u'当前是第{}页{}'.format(cur_page_num, response.url))
        try:
            return scrapy.FormRequest(response.url, formdata=formdata, headers=headers, callback=self.parse_list,
                                      meta=meta)
        except Exception as e:
            with open(self.log_file, mode='aw') as fp:
                fp.write(str(e))
            raise

    def get_header(self, url, flag='1'):
        domain_str = self.get_domain_info(url)
        header = {
            'Host': domain_str.split('//')[-1],
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
        }
        if flag not in (1, '1'):
            header['Origin'], header['Referer'] = domain_str, url
        print(header)
        return header

    def get_form_data(self, resp):
        cur_page_num = resp.meta['cur_page_num']
        formdata = {
            '__VIEWSTATE': resp.xpath(self.extract_dict['__VIEWSTATE']).extract_first(),
            '__EVENTVALIDATION': resp.xpath(self.extract_dict['__EVENTVALIDATION']).extract_first(),
        }
        if 'EnterpriseList' in resp.url:
            formdata['ctl00_ScriptManager1_HiddenField'] = ''
            formdata['__EVENTARGUMENT'] = ''
            formdata['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$lkb_next'
            formdata['ctl00$ContentPlaceHolder1$ddlsz'] = '0'
            formdata['__EVENTARGUMENT'] = ''
            # formdata['__VIEWSTATEGENERATOR'] = resp.xpath(self.extract_dict['__VIEWSTATEGENERATOR']).extract_first()
        elif 'QyxxList' in resp.url:
            formdata['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$Lb_Next'
            formdata['ctl00$ContentPlaceHolder1$ddlsz:'] = ''
            formdata['ctl00$ContentPlaceHolder1$zsbh:'] = ''
            formdata['ctl00$ContentPlaceHolder1$qymc:'] = ''
            formdata['__EVENTARGUMENT:'] = ''
            formdata['__LASTFOCUS:'] = ''
            formdata['ctl00$ContentPlaceHolder1$ddl_page'] = cur_page_num
        else:
            print(u'url问题{}'.format(resp.body_as_unicode()))
        return formdata

    def handle_cdetail_link(self, clink, flag='inner', url=''):
        if 'EnterpriseDetail' in clink:
            clink = 'http://qyryjg.hunanjz.com/public/' + clink
        else:
            clink = 'http://www.hunanjz.com/Html/' + clink
        return clink


if __name__ == '__main__':
    HuNanCompass().run()
