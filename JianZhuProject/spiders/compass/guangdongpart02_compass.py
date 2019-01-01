# coding=utf-8
import json

import scrapy
import time

from JianZhuProject import sit_list
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class GuangDongPart02Compass(BaseCompass):
    name = 'guangdong02_compass'
    allow_domain = ['219.129.189.10:8080', 'www.jyjzcx.com', 'www.zsjs.gov.cn',
                    'mmzjcx.maoming.gov.cn', '218.14.207.72:8082',
                    'zjj.jiangmen.gov.cn']
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
        # ('http://mmzjcx.maoming.gov.cn/PublicPage/CorpMoreList.aspx?clearPaging=true&strNav=4', sit_list[0]),
        ('http://zjj.jiangmen.gov.cn/public/licensing/index_1.html', sit_list[0]),
    ]

    extract_dict = {
        'inner': {
            'nodes': '//table[@class="administrative"]//tr[position()>1]',
            'cname': './td/a/text()',
            'detail_link': './td/a/@href',  # 'http://zjj.jiangmen.gov.cn/public/licensing' + link
            'next_page': '//a[contains(text(), "下一页")]/@href'  #
        },
        # '__VIEWSTATE': '//input[@id="__VIEWSTATE"]/@value',
        # '__EVENTVALIDATION': '//input[@id="__EVENTVALIDATION"]/@value',
        # '__VIEWSTATEENCRYPTED': '//input[@id="__VIEWSTATEENCRYPTED"]/@value',
    }

    redis_tools = RedisTools()

    def start_requests(self):
        link = self.start_urls[0][0]
        for ctype, _ in self.start_urls:
            yield scrapy.Request(link, callback=self.parse_list, meta={'cur_page': '1'},
                                 dont_filter=True)

    def parse_list(self, response):
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
        next_page_link = response.xpath(self.extract_dict['inner']['next_page']).extract_first()
        if int(meta['cur_page']) >= 40:
            print(u'不能在翻页了')
            return
        headers = self.get_header(response.url, flag='2')
        meta['cur_page'] = str(int(meta['cur_page']) + 1)
        link = 'http://zjj.jiangmen.gov.cn/public/licensing/index_{}.html'.format(meta['cur_page'])
        return scrapy.Request(link, callback=self.parse_list, headers=headers, meta=meta)

    def handle_cname(self, cname, flag='inner'):
        return cname.replace('企业基本信息', '').strip('\n\t\r ')

    def handle_cdetail_link(self, link, flag='inner', url=''):
        if 'javascript:window' in link:
            import re
            pp = re.compile(r"\('(.*?)'\)")
            return 'http://218.14.207.72:8082/PublicPage/' + re.search(pp, link).group(1)
        if link.startswith('.'):
            return link.replace('.', 'http://zjj.jiangmen.gov.cn/public/licensing')

    def get_form_data(self, resp):
        meta = resp.meta
        formdata = {
            'ctl00$cph_context$ScriptManager1': 'ctl00$cph_context$UpdatePanel1|ctl00$cph_context$GridViewPaging1$btnNext',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': resp.xpath(self.extract_dict['__VIEWSTATE']).extract_first(),
            '__VIEWSTATEGENERATOR': '8D94C66F',
            '__VIEWSTATEENCRYPTED': '',
            '__EVENTVALIDATION': resp.xpath(self.extract_dict['__EVENTVALIDATION']).extract_first(),
            'ctl00$cph_context$corType': str(meta['ctype']),
            'ctl00$cph_context$corGrade': '全部',
            'ctl00$cph_context$corName': u'请输入相关的企业名称',
            'ctl00$cph_context$GridViewPaging1$txtGridViewPagingForwardTo': str(meta['cur_page']),
            'ctl00$cph_context$GridViewPaging1$btnNext.x': '12',
            'ctl00$cph_context$GridViewPaging1$btnNext.y': '5',
        }

        return formdata


if __name__ == '__main__':
    GuangDongPart02Compass().run()
