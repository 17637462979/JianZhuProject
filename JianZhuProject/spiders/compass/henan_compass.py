# coding=utf-8
import json

import scrapy
import re
from JianZhuProject import sit_list
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class HeNanCompass(BaseCompass):
    name = 'henan_compass'
    allow_domain = ['hngcjs.hnjs.gov.cn/']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,}
    }
    cnt = 1
    start_urls = [
        # 内省:
        ("http://hngcjs.hnjs.gov.cn/SiKuWeb/QiyeList.aspx?type=qyxx&val=null", sit_list[0]),  # "建筑业企业"
        ('http://hngcjs.hnjs.gov.cn/SiKuWeb/WSRY_List.aspx', sit_list[1])
    ]
    # redis_tools = RedisTools()

    extract_dict = {
        'inner': {
            'nodes': '//div[@id="tagContenth"]//tbody//tr[position()>1]',
            'cname': './td/a[contains(@href, "CorpName")]/text()',
            'detail_link': u'./td/a[contains(@href, "CorpName")]/@href',
            # "http://hngcjs.hnjs.gov.cn" + "/SiKuWeb/QiyeDetail.aspx?CorpName=新乡市长丰建设工程有限公司&CorpCode=91410726356120281N"
            'out_province': ['None', 'henan'],  # ***
        },
        'outer': {
            'nodes': '//div[@id="tagContenth"]//table[contains(@id, "GridView2")]//tr[position()>1 and contains(@style, "border-bottom")]',
            'cname': './td/a[contains(@href, "WSRY_Detail")]//text()',
            'detail_link': u'./td/a[contains(@href, "QiYeMingCheng")]/@href',
        # 'http://hngcjs.hnjs.gov.cn/SiKuWeb/'  + 'WSRY_Detail.aspx?QiYeMingCheng=中烨国际建工有限公司&TongYiSheHuiXinYongDaiMa=915114210560792727'
            'out_province': './td[last()]/text()',  # ***
        },
        'next_page_num': u'//a[contains(text(), "下页") and not(@disabled)]/@href',
    # "javascript:__doPostBack('AspNetPager2','3')"
        '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',
        '__VIEWSTATEGENERATOR': '//input[@id="__VIEWSTATEGENERATOR"]/@value',
    }

    def turn_page(self, response):
        print('turn_page:.....')
        have_next = response.xpath(self.extract_dict['next_page_num'])
        if not have_next:
            print('没有下一页啦', response.text)
            print(have_next)
            return
        print('当前是{}页'.format(self.cnt))
        headers = self.get_header(response.url, flag='2')
        form_data = self.get_form_data(response)
        next_link = response.url
        self.cnt += 1
        return scrapy.FormRequest(next_link, headers=headers, formdata=form_data, callback=self.parse_list,
                                  meta=response.meta)

    def get_header(self, url, flag='1'):
        headers = {
            "Host": "www.hebjs.gov.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",

        }
        if flag not in (1, '1'):
            headers["Referer"] = url  # 二次进入才有
        return headers

    def handle_cdetail_link(self, clink, flag='inner', url=''):
        if clink.startswith('http'):
            good_link = clink
        else:
            good_link = "http://hngcjs.hnjs.gov.cn/SiKuWeb/" + clink.replace('/SiKuWeb', '')
        return good_link

    def get_form_data(self, resp):
        have_next = resp.xpath(self.extract_dict['next_page_num']).extract_first()
        pp = re.compile(r"\('(.*?)','(\d+)'\)")
        form_data = dict(__VIEWSTATE=resp.xpath(self.extract_dict['__VIEWSTATE']).extract_first(),
                         __EVENTVALIDATION=resp.xpath(self.extract_dict['__EVENTVALIDATION']).extract_first(),
                         __VIEWSTATEGENERATOR=resp.xpath(self.extract_dict['__VIEWSTATEGENERATOR']).extract_first(),
                         CretType=u'全部资质类别',
                         )
        form_data['__EVENTTARGET'], form_data['__EVENTARGUMENT'] = re.search(pp, have_next).groups()
        return form_data


if __name__ == '__main__':
    HeNanCompass().run()
