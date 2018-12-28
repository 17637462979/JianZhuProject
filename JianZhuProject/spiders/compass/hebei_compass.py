# coding=utf-8
import json

import scrapy

from JianZhuProject import sit_list
from JianZhuProject.items import NameItem
from JianZhuProject.spiders.compass.base_compass import BaseCompass


class HeBeiCompass(BaseCompass):
    name = 'hebei_compass'
    allow_domain = ['www.hebjs.gov.cn']
    custom_settings = {
        # 'ITEM_PIPELINES': {'JianZhuProject.CorpNamePipeline.CorpNamePipeline': 300,}
    }
    cnt = 1
    start_urls = [
        # 内省:
        # ("http://www.hebjs.gov.cn/was5/web/search?channelid=264649", sit_list[0]),  # "建筑业企业"
        ("http://www.hebjs.gov.cn/was5/web/search?channelid=290807", sit_list[0]),  # "勘察企业"
        # ("http://www.hebjs.gov.cn/was5/web/search?channelid=278453", sit_list[0]),  # "设计企业",
        # ("http://www.hebjs.gov.cn/was5/web/search?channelid=273505", sit_list[0]),  # "安全生产许可证",
        # ("http://www.hebjs.gov.cn/was5/web/search?channelid=250510", sit_list[0]),  # "建设工程质量检测机构",
        # ("http://www.hebjs.gov.cn/was5/web/search?channelid=219809", sit_list[0]),  # "工程监理企业",
        # ("http://www.hebjs.gov.cn/was5/web/hbjst/list_xinyong_erjichaxun.jsp", sit_list[0]), # "建筑业企业信用综合评价",
        # ("http://www.hebjs.gov.cn/was5/web/search?channelid=215805", sit_list[0]),   # "招投标",
        # ("http://www.hebjs.gov.cn/was5/web/search?channelid=263141", sit_list[0]),   # "合同备案",
        # # 外省: cname cdetial_page  waisheng
        ("http://www.hebjs.gov.cn/was5/web/search?channelid=289933", sit_list[1]),  # "进冀建筑业企业（省政府上报）",
        # ("http://www.hebjs.gov.cn/was5/web/search?channelid=263175", sit_list[1]),   # "进冀建筑业企业(老系统)",
        # ("http://www.hebjs.gov.cn/was5/web/search?channelid=265706", sit_list[1]),   # "进冀工程监理企业(老系统)",
        # ("http://www.hebjs.gov.cn/was5/web/search?channelid=234215", sit_list[1]),   # "进冀工程勘察设计企业(老系统)",
    ]
    # redis_tools = RedisTools()

    extract_dict = {
        'inner': {
            'nodes': '//div[@class="tabbox"]/table//tr[position()>1]',
            'cpos': '//div[@class="tabbox"]/table//tr[1]/td/text()',  # 获取 "企业名称"、"详情"、"证书编号"的索引(从1开始) ---> 数字
            'cname': './td[{}]/text()',
            'detail_link': u'.//a[contains(text(), "详情")]/@href',
            # "http://www.hebjs.gov.cn/was5/web/" + detail?record=1&channelid=219809
            'out_province': ['None', 'hebei'],  # ***

        },
        'outer': {
            'nodes': '//div[@class="tabbox"]/table//tr[position()>1]',
            'cpos': '//div[@class="tabbox"]/table//tr[1]/td/text()',  # 获取 "企业名称"、"详情"、"证书编号"的索引(从1开始) ---> 数字
            'cname': './td[{}]/text()',
            'detail_link': u'.//a[contains(text(), "详情")]/@href',
            # "http://www.hebjs.gov.cn/was5/web/" + detail?record=1&channelid=219809
            'out_province': ['None', 'waisheng'],  # ***
        },
        'next_page_num': u'//a[contains(text(), "下一页")]/@href'
    # search?page=1097&channelid=264649&perpage=15&outlinepage=10&zsbh=&qymc=&zzlx=
    }

    def start_requests(self):
        # print('start_requests.....')
        for url, sit in self.start_urls:
            headers = self.get_header(url, flag='1')
            print(url)
            yield scrapy.Request(url=url, callback=self.parse_list, headers=headers,
                                 meta={'sit': sit, 'pre_page_num': '0'})

    def parse_list(self, response):
        print('parse_list....', response.text)
        item_contains = []
        url = response.url
        sit = response.meta['sit']
        cpos = response.xpath(self.extract_dict['inner']['cpos']).extract()
        p1 = cpos.index(u'详情') + 1 if u'详情' in cpos and cpos.index(u'详情') else 0
        p2 = cpos.index(u'企业名称') + 1 if u'企业名称' in cpos and cpos.index(u'企业名称') else 0
        p3 = cpos.index(u'证书编号') + 1 if u'证书编号' in cpos and cpos.index(u'证书编号') else 0
        if sit == sit_list[0]:
            inner_nodes = response.xpath(self.extract_dict['inner']['nodes'])
            inner = self.extract_dict['inner']
            print("inner_nodes:", len(inner_nodes))
            inner['cname'] = inner['cname'].format(p2)
            for node in inner_nodes:
                item = NameItem()
                item['compass_name'] = self.handle_cname(node.xpath(inner['cname']).extract_first(), 'inner')
                if p1:
                    item['detail_link'] = self.handle_cdetail_link(node.xpath(inner['detail_link']).extract_first(),
                                                                   'inner', url)
                else:
                    item['detail_link'] = None
                item['out_province'] = inner['out_province'][1] if isinstance(inner['out_province'], list) else 'None'
                item_contains.append(item)
        if sit == sit_list[1]:
            print(u'解析外省....')
            outer_nodes = response.xpath(self.extract_dict['outer']['nodes'])
            outer = self.extract_dict['outer']
            outer['cname'] = outer['cname'].format(p2)
            for node in outer_nodes:
                item = NameItem()
                item['compass_name'] = self.handle_cname(node.xpath(outer['cname']).extract_first(), 'outer')
                if p1:
                    item['detail_link'] = self.handle_cdetail_link(node.xpath(outer['detail_link']).extract_first(),
                                                                   'outer', url)
                if isinstance(outer['out_province'], list) and len(outer['out_province']) > 1:
                    item['out_province'] = outer['out_province'][1]
                else:
                    item['out_province'] = self.handle_out_province(node.xpath(outer['out_province']).extract_first())
                item_contains.append(item)

        yield {'item_contains': item_contains}

        yield self.turn_page(response)

    def turn_page(self, response):
        print('turn_page:.....')
        have_next = response.xpath(self.extract_dict['next_page_num'])
        if len(have_next) == 0:
            print('没有下一页啦', response.text)
            print(have_next)
            return
        print('当前是{}页'.format(self.cnt))
        next_link = 'http://www.hebjs.gov.cn/was5/web/' + have_next.extract_first()
        headers = self.get_header(response.url, flag='2')
        self.cnt += 1
        return scrapy.Request(next_link, headers=headers, callback=self.parse_list, meta=response.meta)

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
            good_link = "http://www.hebjs.gov.cn/was5/web/" + clink
        return good_link


if __name__ == '__main__':
    HeBeiCompass().run()
