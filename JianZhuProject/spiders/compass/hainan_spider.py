# coding=utf-8
import re
import scrapy
from scrapy import cmdline

from JianZhuProject import sit_list
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class HaiNanCompass(BaseCompass):
    name = 'hainan_compass'
    allow_domain = ['pt.hnjst.gov.cn:8008']
    custom_settings = {
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, },
        # 'ALL_FINGER_CONTAINS': 'finger_contains_new1_tmp'
    }
    start_urls = [
        ('http://pt.hnjst.gov.cn:8008/WebSite_Publish/Default.aspx?action=IntegrityMge/ucCreditCompanyInfoList',
         sit_list[1]),  # 混合
    ]

    extract_dict = {
        'outer': {
            'nodes': '//table[@class="ListStyle"]/tr[position()>1]',
            'cname': './/a[contains(@id,"CompanyName")]//text()',
            'detail_link': './/a[contains(@id,"CompanyName")]/@href',
            'out_province': './/span[contains(@id,"Province")]/text()',
        },
        '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        '__VIEWSTATEGENERATOR': '//input[@id="__VIEWSTATEGENERATOR"]/@value',
    }

    def start_requests(self):
        for link, sit in self.start_urls:
            headers = self.get_header(link, flag='1')
            yield scrapy.Request(link, headers=headers, callback=self.parse_list, meta={'pre_page_num': 1, 'sit': sit})

    def turn_page(self, response):
        print('turn_page....')
        total_page_num = int(
            response.xpath('//table[@class="pageCot"]//a[contains(@id,"btnLast")]/text()').extract_first())
        cur_page_num = int(response.meta['pre_page_num'])
        sit = response.meta['sit']
        print(cur_page_num, total_page_num)
        if cur_page_num > int(total_page_num):
            print('不能翻页了')
        else:
            formdata = self.get_form_data(response)
            formdata['ID_IntegrityMge_ucCreditCompanyInfoList$ucPager1$txtCurrPage'] = str(cur_page_num)
            headers = self.get_header(response.url, flag='2')  # 表示不是第一次发的请求
            return scrapy.FormRequest(response.url, callback=self.parse_list, headers=headers, formdata=formdata,
                                      meta={'sit': sit, 'pre_page_num': cur_page_num + 1})

    def get_form_data(self, rep):
        __VIEWSTATE = rep.xpath(self.extract_dict['__VIEWSTATE']).extract_first()
        __VIEWSTATEGENERATOR = rep.xpath(self.extract_dict['__VIEWSTATEGENERATOR']).extract_first()
        form_data = {
            '__EVENTTARGET': 'ID_IntegrityMge_ucCreditCompanyInfoList$ucPager1$btnNext',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': __VIEWSTATE,
            '__VIEWSTATEGENERATOR': __VIEWSTATEGENERATOR,
            'ID_IntegrityMge_ucCreditCompanyInfoList$txtProjectName': '',
            'ID_IntegrityMge_ucCreditCompanyInfoList$ddlProvince': u'全部',
            'ID_IntegrityMge_ucCreditCompanyInfoList$txtValidCode': '',
            'ID_IntegrityMge_ucCreditCompanyInfoList$ucPager1$txtCurrPage': '',
        }
        return form_data

    def get_header(self, url, flag='1'):
        headers = {
            'Host': 'pt.hnjst.gov.cn:8008',
            'Referer': 'http://pt.hnjst.gov.cn:8008/WebSite_Publish/Default.aspx?action=IntegrityMge/ucList&TIndex=0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
        }
        if flag != '1':
            headers['Origin'] = 'http://' + headers['Host']
            headers[
                'Referer'] = 'http://pt.hnjst.gov.cn:8008/WebSite_Publish/Default.aspx?action=IntegrityMge/ucCreditCompanyInfoList'
        return headers

    def handle_cdetail_link(self, link, flag='inner'):
        # ‘http://pt.hnjst.gov.cn:8008/WebSite_Publish/’ + Default.aspx?action=IntegrityMge/ucShow&Type=&ActDatumBase_Guid=978bd93f-f704-44e1-964d-506097e3e4f0
        detail_link = 'http://pt.hnjst.gov.cn:8008/WebSite_Publish/' + link
        return detail_link


if __name__ == '__main__':
    cmdline.execute('scrapy crawl {}'.format(HaiNanCompass.name).split())
