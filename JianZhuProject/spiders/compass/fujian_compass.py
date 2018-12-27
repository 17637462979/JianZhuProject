# coding=utf-8
import scrapy

from JianZhuProject import sit_list
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class FuJianCompass(BaseCompass):
    name = 'fujian_compass'
    allow_domain = ['www.fjjs.gov.cn:97']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,},
        # 'ALL_FINGER_CONTAINS': 'finger_contains_new1_tmp'
    }
    start_urls = [
        ('http://www.fjjs.gov.cn:97/HurdPlatform/Credit/Construction/CreditIndex.aspx?certificationtypeid=3',
         sit_list[0]),  # 省内
    ]

    extract_dict = {
        'inner': {
            'nodes': '//table[contains(@id,"CompanyList")]/tr[position()>1]',
            'cname': './/a[contains(@id,"CompanyName")]//text()',
            'detail_link': './/a[contains(@id,"CompanyName")]/@href',
            'out_province': ['None', 'fujian'],
        },
        '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        '__VIEWSTATEGENERATOR': '//input[@id="__VIEWSTATEGENERATOR"]/@value',
        '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',

        'hidid': './/iuput[contains(@id, "CompanyList_hddID")]/@value',  # 隐藏的序号，fordata
        'next_page_btn': u'//a[@title="下一页" and contains(@id, "nextpagebtn")]/@id'
    }

    def turn_page(self, response):
        next_page_btn = (response.xpath(self.extract_dict['next_page_btn']).extract_first())
        cur_page_num = int(response.meta.get('pre_page_num'))

        print('cur_page_num....', cur_page_num)
        print('next_page_btn...', next_page_btn)
        sit = response.meta['sit']
        if not next_page_btn:
            print('不能翻页了')
        else:
            formdata = self.get_form_data(response)
            print('打印formdata：\n', formdata)
            headers = self.get_header(response.url, flag='2')  # 表示不是第一次发的请求
            print('打印headers：\n', headers)
            return scrapy.FormRequest(response.url, callback=self.parse_list, headers=headers, formdata=formdata,
                                      meta={'sit': sit, 'pre_page_num': str(int(cur_page_num) + 1)})

    def get_form_data(self, rep):
        __VIEWSTATE = rep.xpath(self.extract_dict['__VIEWSTATE']).extract_first()
        __VIEWSTATEGENERATOR = rep.xpath(self.extract_dict['__VIEWSTATEGENERATOR']).extract_first()
        __EVENTVALIDATION = rep.xpath(self.extract_dict['__EVENTVALIDATION']).extract_first()
        cur_page_num = rep.meta.get('pre_page_num', '1')
        form_data = {
            '__EVENTTARGET': ' ctl00$ContentPlaceHolder$pGrid$nextpagebtn',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': __VIEWSTATE,
            '__VIEWSTATEGENERATOR': __VIEWSTATEGENERATOR,
            '__EVENTVALIDATION': __EVENTVALIDATION,
            'ctl00$ContentPlaceHolder$txtCompanyName': '',
            'ctl00$ContentPlaceHolder$pGrid$dplist': cur_page_num,
        }
        hid_id_list = rep.xpath(self.extract_dict['hidid']).extract()
        kstr = "ctl00$ContentPlaceHolder$gridViewCompanyList$ctl{}$hddID"
        for i, hid in enumerate(hid_id_list):
            k = kstr.format('0' + str(i))
            form_data[k] = hid
        return form_data

    def handle_cdetail_link(self, clink, flag='inner', url=''):
        if clink.startswith('http'):
            good_link = clink
        else:
            domain_str = 'http://www.fjjs.gov.cn:97/HurdPlatform/Credit'
            if clink.startswith('..'):
                good_link = clink.replace('..', domain_str, 1)
            elif clink.startswith('.'):
                good_link = clink.replace('.', domain_str, 1)
            elif clink.startswith('/'):
                good_link = domain_str + clink
            else:
                print('请重写该方法')
                good_link = ''
        return good_link


if __name__ == '__main__':
    FuJianCompass().run()
