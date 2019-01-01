# coding=utf-8
import json

import scrapy
import time

from JianZhuProject import sit_list
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class GuangDongPart01Compass(BaseCompass):
    name = 'guangdong01_compass'
    allow_domain = ['219.129.189.10:8080', 'www.jyjzcx.com', 'www.zsjs.gov.cn', 'mmzjcx.maoming.gov.cn']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, }
    }
    log_file = '../logs/{}_log.log'.format(name)
    cnt = 1
    start_urls = [
        # ("http://219.129.189.10:8080/yjcxk/web-nav/enterprises?pageNumber=1", sit_list[0]),
        # ("http://219.129.189.10:8080/yjcxk/web-nav/enterprises?pageNumber=0", sit_list[1]),
        # ("http://219.129.189.10:8080/yjcxk/web-nav/persons?pageNumber=1&pageSize=17550", sit_list[0])
        # ('http://www.jyjzcx.com/web/companylist.action?pageNum=1&pageSize=15', sit_list[0])
        # ('http://www.zsjs.gov.cn/web/enterprise/findEnterprises?page=1&start=45', sit_list[0]),
        # ('https://gcjs.sg.gov.cn/website/buildproject/buildProjectSjAction!proMainList.action?pager.offset=20',
        #  sit_list[0]),
        ('http://mmzjcx.maoming.gov.cn/PublicPage/CorpMoreList.aspx?clearPaging=true&strNav=4', sit_list[0])
    ]
    ctypes = [3, 2, 1, 4, 6, 5, 7, 8, 9, 10, 11, 12, 'A', 'B', 'C', 'D']

    extract_dict = {
        'inner': {
            'nodes': '//table[contains(@id, "GridView1")]//tr[position()>1]',
            'cname': './td/a/text()',
            'detail_link': './td/a/@onclick',  #
            'next_page': '//input[contains(@id, "btnNext") and @disabled]'  #
        },
        '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',
        '__VIEWSTATEENCRYPTED': '//input[@id="__VIEWSTATEENCRYPTED"]/@value',
    }

    redis_tools = RedisTools()

    def start_requests(self):
        link = self.start_urls[0][0]
        for ctype in self.ctypes[:1]:
            yield scrapy.Request(link, callback=self.parse_list1, meta={'cur_page': '1', 'ctype': ctype},
                                 dont_filter=True)

    def parse_list1(self, response):
        ext_rules = self.extract_dict['inner']
        nodes = response.xpath(ext_rules['nodes'])
        item_contains = []
        for node in nodes:
            item = NameItem()
            item['compass_name'] = self.handle_cname(node.xpath(ext_rules['cname']).extract_first())
            item['detail_link'] = self.handle_cdetail_link(node.xpath(ext_rules['detail_link']).extract_first())
            item['out_province'] = 'waisheng'
            if self.redis_tools.check_finger(item['detail_link']):
                print(u'{}已经爬取过'.format(item['compass_name']))
                continue
            item_contains.append(item)
        yield {'item_contains': item_contains}
        yield self.turn_page(response)

    def turn_page(self, response):
        meta = response.meta
        if response.xpath(self.extract_dict['inner']['next_page']).extract_first():
            print(u'不能在翻页了')
            return
        headers = self.get_header(response.url, flag='2')
        form_data = self.get_form_data(response)
        meta['cur_page'] = str(int(meta['cur_page']) + 1)
        print(u'下一页:', meta['cur_page'])
        return scrapy.FormRequest(response.url, formdata=form_data, callback=self.parse_list1, headers=headers,
                                  meta=meta)

    def parse_list2(self, response):
        json_data = json.loads(response.body_as_unicode())

        item_contains = []
        for row in json_data['rows']:
            item = NameItem()
            item['compass_name'] = row['cxaa05']
            item['detail_link'] = row['link']
            item['out_province'] = 'waisheng'
            item_contains.append(item)
        yield {'item_contains': item_contains}
        meta = response.meta
        total_page = (json_data['total'] + 14) / 15
        cur_page = meta['cur_page']
        if int(cur_page) >= int(total_page):
            print(u'不能继续翻页了，当前最大页码为:', cur_page)
            return
        yield self.turn_page1(response)

    def turn_page1(self, resp):
        meta = resp.meta
        meta['cur_page'], start_row = int(meta['cur_page']) + 1, int(meta['cur_page']) * 15
        link = 'http://www.zsjs.gov.cn/web/enterprise/findEnterprises?page={}&start={}'.format(meta['cur_page'],
                                                                                               start_row)
        headers = self.get_header(resp.url, flag='2')
        return scrapy.Request(link, callback=self.parse_list2, meta=meta, headers=headers)


        # def parse_list(self, response):
        #     data = json.loads(response.body_as_unicode())['data']['rows']
        #     item_contains = []
        #     for unit in data:
        #         if 'persons' in response.url:
        #             compass_name = unit['entName']
        #             detail_link = 'None'
        #             out_province = 'waisheng'
        #         else:
        #             compass_name = unit['companyName']
        #             detail_link = 'http://219.129.189.10:8080/yjcxk/vueStatic/html/companyDetail.jsp?id=' + unit['id']
        #             out_province = 'guangdong'
        #         if detail_link in ('', 'None'):
        #             if self.redis_tools.check_finger(compass_name):
        #                 continue
        #         else:
        #             if self.redis_tools.check_finger(detail_link):
        #                 continue
        #         item = NameItem({
        #             'compass_name': compass_name,
        #             'detail_link': detail_link,
        #             'out_province': out_province
        #         })
        #         if '测试企业' in item['compass_name']:
        #             continue
        #         item_contains.append(item)
        #     yield {'item_contains': item_contains}
        #
        #     # def turn_page(self, response):
        #     #     next_page_num = response['']
        #     #     "http://219.129.189.10:8080/yjcxk/web-nav/persons?pageNumber={}&pageSize=5000".format(next_page_num)
        #     #     return

    def handle_cname(self, cname):
        return cname.replace('企业基本信息', '').strip('\n\t\r ')

    def handle_cdetail_link(self, link):
        if 'javascript:window' in link:
            import re
            pp = re.compile(r"\('(.*?)'\)")
            return 'http://mmzjcx.maoming.gov.cn/PublicPage/' + re.search(pp, link).group(1)

    def get_form_data(self, resp):
        meta = resp.meta
        formdata = {
            'ctl00$cph_context$ScriptManager1': 'ctl00$cph_context$UpdatePanel1|ctl00$cph_context$GridViewPaging1$btnNext',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': resp.xpath(self.extract_dict['__VIEWSTATE']).extract_first(),
            '__EVENTVALIDATION': resp.xpath(self.extract_dict['__EVENTVALIDATION']).extract_first(),
            '__VIEWSTATEENCRYPTED': resp.xpath(self.extract_dict['__VIEWSTATEENCRYPTED']).extract_first(),
            'ctl00$cph_context$ddlCorpType': str(meta['ctype']),
            'ctl00$cph_context$ddlCorpSincerityGrade': '',
            'ctl00$cph_context$txtCorpName': u'请输入相关的企业名称',
            'ctl00$cph_context$GridViewPaging1$txtGridViewPagingForwardTo': str(meta['cur_page']),
            'ctl00$cph_context$GridViewPaging1$btnNext.x': '12',
            'ctl00$cph_context$GridViewPaging1$btnNext.y': '5',
        }

        return formdata


if __name__ == '__main__':
    GuangDongPart01Compass().run()
