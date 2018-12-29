# coding=utf-8
import json

import scrapy

from JianZhuProject import sit_list
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class ChongQingCompass(BaseCompass):
    name = 'chongqing_compass'
    allow_domain = ['www.hebjs.gov.cn']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,}
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

    # redis_tools = RedisTools()

    extract_dict = {
        'rule1': {  # acsOutNetQueryPageList  qualificationCertificateListForPublic
            'nodes': '//table[@id="DataGrid1" or @rules="all"]//tr[position()>1]',
            'cname': './/a[contains(@href, "doPostBack") and not(contains(string(), "查看"))]//text()',
            'detail_link': '',  # # 赋值空
            'out_province': ['chongqing', 'waidi'],
        },
        'rule2': {
            'nodes': '//table[@id="DataGrid1"]/tbody/tr[position()>1]',
            'cname': './td[2]//text()',
            'detail_link': '',  # 赋值空
            'out_province': ['chongqing', 'waidi']
        }
    }

    def start_requests(self):
        for url, sit, rule in self.start_urls:
            headers = self.get_header(url, flag='1')
            print(url)
            yield scrapy.Request(url=url, callback=self.parse_list, headers=headers,
                                 meta={'sit': sit, 'pre_page_num': '0'})

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
            good_link = "" + clink
        return good_link


if __name__ == '__main__':
    ChongQingCompass().run()
