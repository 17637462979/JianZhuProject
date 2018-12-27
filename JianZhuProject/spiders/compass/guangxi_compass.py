# coding=utf-8
import scrapy
import re
from JianZhuProject import sit_list
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class GuangXiCompass(BaseCompass):
    name = 'guangxi_compass'
    allow_domain = ['dn4.gxzjt.gov.cn:1141']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,},
        # 'ALL_FINGER_CONTAINS': 'finger_contains_new1_tmp'
    }
    start_urls = [
        ('http://dn4.gxzjt.gov.cn:1141/cxkBackManage/HuiYuanInfoMis2_GX_Out/Pages/ShiGongInfo_Center/Unit_List.aspx',
         sit_list[1]),  #
    ]

    extract_dict = {
        'outer': {
            'nodes': '//table[@id="DataGrid1_BodyTable"]//tr[@keyvalue]',
            'cname': u'.//td[@colname="单位名称"]//text()',
            'detail_link': u'.//td[@colname="查看"]//div[contains(@onclick, "OpenTopDialog")]/@onclick',
            'out_province': u'.//td[@colname="注册地区"]//text()',
        },
        '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        '__VIEWSTATEGENERATOR': '//input[@id="__VIEWSTATEGENERATOR"]/@value',
        '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',
    }

    def turn_page(self, response):
        url = response.url
        headers = self.get_header(response.url)
        meta = response.meta
        meta['pre_page_num'] = str(int(meta['pre_page_num']) + 1)
        formdata = self.get_form_data(response)
        return scrapy.FormRequest(url, headers=headers, formdata=formdata, callback=self.parse_list, meta=meta)

    def get_header(self, url, flag='1'):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            'Host': 'dn4.gxzjt.gov.cn:1141',
        }
        if flag not in (1, '1'):
            headers['Referer'] = url
        return headers

    def get_form_data(self, resp):
        txt = resp.body_as_unicode()
        print(txt)
        meta = resp.meta
        headers = {
            "ctl00$ScriptManager1": u"ctl00$UpdatePanel4|ctl00$cphContent$DataGrid1$ctl12",
            "ctl00$cphCondition$tbDanWeiName": u"",
            "ctl00$cphCondition$tbZuZhiJGDM": u"",
            "ctl00$cphCondition$DDLXiaQu$TextDDLXiaQu": u"请选择",
            "ctl00$cphCondition$DDLXiaQu$ValueDDLXiaQu": u"",
            "ctl00$cphCondition$DDLHangYeType$TextDDLHangYeType": u"所有",
            "ctl00$cphCondition$DDLHangYeType$ValueDDLHangYeType": u"",
            "ctl00_cphContent_DataGrid1_RowSelecter_0": u"",
            "ctl00_cphContent_DataGrid1_RowSelecter_1": u"",
            "ctl00_cphContent_DataGrid1_RowSelecter_2": u"",
            "ctl00_cphContent_DataGrid1_RowSelecter_3": u"",
            "ctl00_cphContent_DataGrid1_RowSelecter_4": u"",
            "ctl00_cphContent_DataGrid1_RowSelecter_5": u"",
            "ctl00_cphContent_DataGrid1_RowSelecter_6": u"",
            "ctl00_cphContent_DataGrid1_RowSelecter_7": u"",
            "ctl00_cphContent_DataGrid1_RowSelecter_8": u"",
            "ctl00_cphContent_DataGrid1_RowSelecter_9": u"",
            "__EVENTTARGET": "ctl00$cphContent$DataGrid1$ctl12",
            "__EVENTARGUMENT": "",
            "__ASYNCPOST": "true",
            "ctl00$cphContent$DataGrid1$PageNumDataGrid1": meta['pre_page_num']
        }
        plist = ['ctl00_cphContent_DataGrid1_ClientState', '__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION']
        for pk in plist:
            pp = re.compile(r'{}\|(.*?)\|'.format(pk), re.S)
            pkv = re.search(pp, txt).groups()[0]
            headers[pk] = pkv
        return headers

    def handle_cdetail_link(self, clink, flag='outer', url=''):
        pp = re.compile(ur"OpenTopDialog\('(.*?)'\)", re.I)
        link = re.search(pp, clink).group(1)
        link = link.replace('..', 'http://dn4.gxzjt.gov.cn:1141/cxkBackManage/HuiYuanInfoMis2_GX_Out/Pages')
        return link

    def handle_out_province(self, s):
        s = s.replace(u'\xb7', '-').split('-')[0]
        return s.strip('\r\n\t ')


if __name__ == '__main__':
    GuangXiCompass().run()
