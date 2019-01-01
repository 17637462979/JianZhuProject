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
    allow_domain = ['219.129.189.10:8080', 'www.jyjzcx.com', 'www.zsjs.gov.cn']
    custom_settings = {
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300, }
    }
    log_file = '../logs/{}_log.log'.format(name)
    cnt = 1
    start_urls = [
        # ("http://219.129.189.10:8080/yjcxk/web-nav/enterprises?pageNumber=1", sit_list[0]),
        # ("http://219.129.189.10:8080/yjcxk/web-nav/enterprises?pageNumber=0", sit_list[1]),
        # ("http://219.129.189.10:8080/yjcxk/web-nav/persons?pageNumber=1&pageSize=17550", sit_list[0])
        # ('http://www.jyjzcx.com/web/companylist.action?pageNum=1&pageSize=15', sit_list[0])
        # ('http://www.zsjs.gov.cn/web/enterprise/findEnterprises?page=1&start=45', sit_list[0]),
        ('https://gcjs.sg.gov.cn/website/buildproject/buildProjectSjAction!proMainList.action?pager.offset=20',
         sit_list[0]),
    ]
    extract_dict = {
        'inner': {
            'nodes': '//table[@class="list_div"]//tr',
            'cname': './td/a/text()',
            'detail_link': './td/a/@href',  # https://gcjs.sg.gov.cn     #'http://www.jyjzcx.com' + xxx,
            'next_page_url': '//a[@class="laypage_next"]/@data-page'  #
        }
    }

    redis_tools = RedisTools()

    def start_requests(self):
        for link, sit in self.start_urls:
            yield scrapy.Request(link, callback=self.parse_list1, meta={'cur_page': '1'})

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
        if int(meta['cur_page']) >= 4:
            print(u'不能在翻页了')
            return
        meta['cur_page'] = str(int(meta['cur_page']) + 1)
        # link = 'http://www.jyjzcx.com/web/companylist.action?pageNum={}&pageSize=15'.format(meta['cur_page'])
        headers = self.get_header(response.url, flag='2')
        form_data = self.get_form_data(response)
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
        return cname.replace('企业基本信息', '')

    def handle_cdetail_link(self, link):

        return 'https://gcjs.sg.gov.cn' + link

    def get_form_data(self, resp):
        meta = resp.meta
        formdata = {
            'tId': '',
            'tpId': '3',
            'areaCode': '440200',
            'gkmlbh2': '',
            'gkywbt': '',
            'startTime': '',
            'endTime': '',
            'pagesize': '20',
            'pageNumber': str(meta['cur_page']),
            'SYSTEM_YANGANG_IS_RESET_SEARCH': 'false',
            'currentpage': str(meta['cur_page']),
        }
        if 'buildProjectS' in resp.url:
            formdata['gkmlbh'] = 'XYDW_QYZZ'
        else:
            formdata['gkmlbh'] = 'XYDW_QYJB'

        return formdata


if __name__ == '__main__':
    GuangDongPart01Compass().run()
