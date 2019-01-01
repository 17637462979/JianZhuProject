# coding=utf-8
import json

import scrapy

from JianZhuProject import sit_list
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class ChongQingCompass(BaseCompass):
    name = 'chongqing_compass'
    allow_domain = ['jzzb.cqjsxx.com']
    custom_settings = {
        'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300}
    }
    log_file = '../logs/{}_log.log'.format(name)
    cnt = 1
    start_urls = [
        ('http://jzzb.cqjsxx.com/CQCollect/Qy_Query/YhzSgqy/YhzSgqy_List.aspx', sit_list[0], 'rule1'),
        ('http://jzzb.cqjsxx.com/CQCollect/Qy_Query/Sgqy/Sgqy_List.aspx', sit_list[0], 'rule1'),
        ('http://jzzb.cqjsxx.com/CQCollect/Qy_Query/Zljcjg/Zljcjg_List.aspx', sit_list[0], 'rule1'),
        ('http://jzzb.cqjsxx.com/CQCollect/Qy_Query/Zjzxjg/Zjzxjg_List.aspx', sit_list[0], 'rule1'),
        ('http://jzzb.cqjsxx.com/CQCollect/Qy_Query/Hntqy/Hntqy_List.aspx', sit_list[0], 'rule1'),
        ('http://jzzb.cqjsxx.com/CQCollect/Qy_Query/Ryxxbs/Rybabs_List.aspx', sit_list[1], 'rule1'),
        ('http://jzzb.cqjsxx.com/CQCollect/Qy_Query/Zbdljg/Zbdljg_List.aspx', sit_list[1], 'rule1'),
        ('http://jzzb.cqjsxx.com/CQCollect/Qy_Query/Zjzxjg/Wd_Zjzxjg_List.aspx', sit_list[1], 'rule1'),

        # == == == == == == == == == rule2
        ('http://jzzb.cqjsxx.com/CQCollect/Qy_Query/Jlqy/Jlqy_List.aspx', sit_list[0], 'rule2'),
        ('http://jzzb.cqjsxx.com/CQCollect/Qy_Query/Jlqy/WdJlqy_List.aspx', sit_list[1], 'rule2'),
    ]

    redis_tools = RedisTools()

    extract_dict = {
        'rule1': {  # acsOutNetQueryPageList  qualificationCertificateListForPublic
            'nodes': '//table[@id="DataGrid1" or @rules="all"]//tr[position()>1]',
            'cname': './/a[contains(@href, "doPostBack") and not(contains(string(), "查看"))]//text()',
            'detail_link': '',  # # 赋值空
            # 'out_province': ['chongqing', 'waidi'],
        },
        'rule2': {
            'nodes': '//table[@id="DataGrid1"]/tbody/tr[position()>1]',
            'cname': './td[2]//text()',
            'detail_link': '',  # 赋值空
            # 'out_province': ['chongqing', 'waidi']
        },
        'total_page': '//span[@id="TurnPage1_pagecount" or @id="Pager1_Pages"]//text()',
        '__VIEWSTATE': '//input[@name="__VIEWSTATE"]/@value',
        '__VIEWSTATEGENERATOR': '//input[@name="__VIEWSTATEGENERATOR"]/@value',
        '__EVENTTARGET': '//input[@name="__EVENTTARGET"]/@value',

    }

    def start_requests(self):
        for url, sit, rule in self.start_urls:
            headers = self.get_header(url, flag='1')
            yield scrapy.Request(url=url, callback=self.parse_list, headers=headers,
                                 meta={'sit': sit, 'cur_page_num': '1', 'rule': rule})

    def parse_list(self, response):

        meta = response.meta
        rule, sit = meta['rule'], meta['sit']
        out_province = 'chongqing' if sit_list[0] == sit else 'waisheng'
        ext_rule = self.extract_dict[rule]
        nodes = response.xpath(ext_rule['nodes'])
        item_contains = []
        for node in nodes:
            item = NameItem()
            item['compass_name'] = self.handle_cname(node.xpath(ext_rule['cname']).extract_first())
            item['detail_link'] = 'None'
            item['out_province'] = out_province
            item_contains.append(item)
        yield {'item_contains': item_contains}
        yield self.turn_page(response)

    def turn_page(self, response):
        meta = response.meta
        if 'total_page' not in meta:
            meta['total_page'] = meta.get('total_page', response.xpath(self.extract_dict['total_page']).extract_first())

        cur_page_num = meta['cur_page_num']
        print('当前页:{}, 总页码:{}'.format(cur_page_num, meta['total_page']))
        if int(cur_page_num) >= int(meta['total_page']):
            print('不能翻页了，当前最大页码:{}'.format(cur_page_num))
            return
        headers = self.get_header(response.url, flag='2')
        formdata = self.get_form_data(response)
        meta['cur_page_num'] = int(meta['cur_page_num']) + 1
        return scrapy.FormRequest(response.url, headers=headers, formdata=formdata, callback=self.parse_list, meta=meta)

    def get_form_data(self, response):
        form_data = {
            'TurnPage1:PageNum': '',
            'FName': '',
            '__EVENTARGUMENT': '',
            '__EVENTTARGET': 'TurnPage1:LB_Next',
            '__VIEWSTATE': ''.join(response.xpath(self.extract_dict['__VIEWSTATE']).extract()),
            '__VIEWSTATEGENERATOR': ''.join(response.xpath(self.extract_dict['__VIEWSTATEGENERATOR']).extract()),
        }
        return form_data

    def get_header(self, url, flag='1'):
        headers = {
            "Host": "jzzb.cqjsxx.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",

        }
        if flag not in (1, '1'):
            headers["Referer"], headers["Origin"] = url, self.get_domain_info(url)  # 二次进入才有
        return headers

if __name__ == '__main__':
    ChongQingCompass().run()
