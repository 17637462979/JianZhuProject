# coding=utf-8
import re
import scrapy
from scrapy import cmdline

from JianZhuProject import sit_list
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class GuiZhouCompass(BaseCompass):
    name = 'guizhou_compass'
    allow_domain = ['jzjg.gzjs.gov.cn:8088']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,}
    }
    start_urls = [
        ('http://jzjg.gzjs.gov.cn:8088/gzzhxt/SYGS/SYGSGL/QYCX_new.aspx', sit_list[0]),  # 省内
        # ('http://jzjg.gzjs.gov.cn:8088/gzzhxt/SYGS/SYGSGL/SWRQQYGSlist_new.aspx', sit_list[1])
    ]

    extract_dict = {
        'inner': {
            'nodes': '//table[@id="ContentMain_DataList1"]/tr[position()>1]',
            'cname': './/a[@onclick and @title]/text()',
            'detail_link': './/a[@onclick and @title]/@href',
            'out_province': ['None', 'guizhou'],
        },
        'outer': {
            'nodes': '//table[@id="ContentMain_DataList1"]/a[contains(@id, "ContentMain_DataList1_lnkDocTitle_")]',
            'cname': './@title',
            'detail_link': './@onclick',
            'out_province': '',
        },
        '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',
    }

    def turn_page(self, response):
        pre_page_num = response.xpath('//input[@id="ContentMain_HidIndexPage"]/@value').extract_first()
        total_page_num = response.xpath('//input[@id="ContentMain_HidPageCount"]/@value').extract_first()
        if int(pre_page_num) + 1 >= int(total_page_num):
            print('不能翻页了')
        else:
            formdata = self.get_form_data(response)
            formdata['ctl00$ContentMain$HidIndexPage'] = str(int(pre_page_num) + 2)
            formdata['ctl00$ContentMain$HidPageCount'] = str(total_page_num)
            headers = self.get_header(response.url, flag='2')  # 表示不是第一次发的请求
            yield scrapy.FormRequest(response.url, callback=self.parse_list, headers=headers, formdata=formdata)

    def get_form_data(self, rep):

        __VIEWSTATE = rep.xpath(self.extract_dict['__VIEWSTATE']).extract_first()
        __EVENTVALIDATION = rep.xpath(self.extract_dict['__EVENTVALIDATION']).extract_first()
        __VIEWSTATEGENERATOR = "19DAD8CC"
        form_data = {
            '__VIEWSTATE': __VIEWSTATE,
            '__EVENTVALIDATION': __EVENTVALIDATION,
            '__VIEWSTATEGENERATOR': __VIEWSTATEGENERATOR,
            '__EVENTTARGET': 'ctl00$ContentMain$LinkButtonNextPage',
            "ctl00$txtWTNR": "",
            "ctl00$txtTJR": "",
            "ctl00$ContentMain$txtQuery": "",
            "ctl00$ContentMain$HidColnumID": "0",
        }

        return form_data

    def get_header(self, url, flag='1'):
        headers = {
            "Host": "jzjg.gzjs.gov.cn:8088",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        }
        if flag != '1':
            headers['Origin'] = 'http://' + headers['Host']
            headers['Referer'] = url
        return headers

    def handle_cdetail_link(self, link, flag='inner'):
        # ShowWin('96DC4961-7903-40F5-A0E5-24A6BF6AC05D','911401000607370472','v');return false;
        # http://jzjg.gzjs.gov.cn:8088/gzzhxt/SysWebCenter/WebQYSB/Web_GSDWInfo_New.aspx?opType=v&GUID=96DC4961-7903-40F5-A0E5-24A6BF6AC05D&CorpCode=911401000607370472
        import re
        pp = re.compile(r"ShowWin\('(.*?)','(.*?)','(.*?)'\);")
        [GUID, CorpCode, opType] = re.findall(pp, link)[0]
        detail_link = 'http://jzjg.gzjs.gov.cn:8088/gzzhxt/SysWebCenter/WebQYSB/Web_GSDWInfo_New.aspx?opType={}&GUID={}&CorpCode={}'.format(
            opType, GUID, CorpCode)
        return detail_link


if __name__ == '__main__':
    cmdline.execute('scrapy crawl guizhou_compass'.split())
