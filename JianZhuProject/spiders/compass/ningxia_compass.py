# coding=utf-8
import json

import scrapy

from JianZhuProject import sit_list
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass
import urlparse


class NingXiaCompass(BaseCompass):
    name = 'ningxia_compass'
    allow_domain = ['www.hebjs.gov.cn']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,}
    }
    cnt = 1
    start_urls = [
        # 省内，统一使用'省外'
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=1&islocal=JN01', sit_list[1]),  # '工程勘察 '),
        ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=2&islocal=JN01', sit_list[1]),  # '工程设计 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=3&islocal=JN01', sit_list[1]),  # '建筑业 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=4&islocal=JN01', sit_list[1]),  # '工程监理 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=5&islocal=JN01', sit_list[1]),  # '工程招标代理 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=6&islocal=JN01', sit_list[1]), # '设计施工一体化 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=7&islocal=JN01', sit_list[1]), # '工程造价咨询 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=10&islocal=JN01', sit_list[1]),  # '质量检测 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=11&islocal=JN01', sit_list[1]),  # '城乡规划 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=12&islocal=JN01', sit_list[1]),  # '园林绿化 '),
        # # 省外
        ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=1&islocal=JN02', sit_list[1]),  # '工程勘察 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=2&islocal=JN02', sit_list[1]),  # '工程设计 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=3&islocal=JN02', sit_list[1]),  # '建筑业 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=4&islocal=JN02', sit_list[1]),  # '工程监理 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=5&islocal=JN02', sit_list[1]),  # '工程招标代理 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=6&islocal=JN02', sit_list[1]),  # '设计施工一体化 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=7&islocal=JN02', sit_list[1]),  # '工程造价咨询 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=10&islocal=JN02', sit_list[1]),  # '质量检测 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=11&islocal=JN02', sit_list[1]),  # '城乡规划 '),
        # ('http://218.95.173.11:8092/jzptweb/company_list.html?qualification=12&islocal=JN02', sit_list[1]),  # '园林绿化 '),
    ]

    # redis_tools = RedisTools()

    def start_requests(self):
        for refer, sit in self.start_urls:
            headers = self.get_header(refer, flag='1')
            url = 'http://218.95.173.11:8092/portal.php?'
            formdata = self.get_form_data(refer)
            yield scrapy.FormRequest(url=url, callback=self.parse_list, formdata=formdata, headers=headers,
                                     meta={'sit': sit, 'cur_page_num': '1', 'refer': refer})

    def parse_list(self, response):
        json_data = json.loads(response.text)
        per_page_rows = 15
        total_page_num = (json_data['datax'] + per_page_rows - 1) / per_page_rows
        item_contains = []
        for unit in json_data['data']:
            cname, compass_id, out_province = unit['ci_name'], unit['id'], unit['ci_reg_addr']
            detail_link = 'http://218.95.173.11:8092/selectact/query.jspx?resid=IDIXWP2KBO&rowid={}&rows=10'.format(
                compass_id)
            item = NameItem({'compass_name': cname, 'detail_link': detail_link, 'out_province': out_province})
            item_contains.append(item)
        yield {'item_contains': item_contains}

        if int(response.meta['cur_page_num']) < int(total_page_num):
            self.cnt += 1
            print('即将翻%d页' % self.cnt)
            yield self.turn_page(response)
        else:
            print('不能继续翻页了, 当前页码:', response.meta['cur_page_num'])

    def turn_page(self, response):
        print('turn_page:')
        refer = response.meta['refer']
        headers = self.get_header(refer)
        formdata = self.get_form_data(refer)
        next_page_num = int(response.meta['cur_page_num']) + 1
        formdata['page'] = str(next_page_num)
        return scrapy.FormRequest(response.url, formdata=formdata, headers=headers, callback=self.parse_list,
                                  meta={'refer': refer, 'cur_page_num': str(next_page_num)})

    def get_form_data(self, refer):
        print(refer)
        res = urlparse.urlparse(refer)
        query_str2dict = urlparse.parse_qs(res.query)  # {'islocal': ['JN02'], 'qualification': ['12']}
        print(query_str2dict)
        formdata = {
            # "page": str(next_page_num),
            "resid": "web_company.quaryCorp",
            "ci_qualification_code": query_str2dict['qualification'][0],
            "ci_islocal_code": query_str2dict['islocal'][0],
            "rows": "14",
        }
        if query_str2dict['islocal'][0] == 'JN02':
            formdata['rows'] = "15"
        return formdata

    def get_header(self, url, flag='1'):
        headers = {
            'Host': '218.95.173.11:8092',
            'Origin': 'http://218.95.173.11:8092',
            'Referer': url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest'

        }
        return headers

    def handle_cdetail_link(self, clink, flag='inner', url=''):

        return good_link


if __name__ == '__main__':
    NingXiaCompass().run()
