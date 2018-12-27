# -*- coding: utf-8 -*-
import time
from urlparse import urlparse

import requests
import scrapy
from lxml import etree
from scrapy import cmdline
import re
from JianZhuProject.items import JianzhuprojectItem, QualityItem, StaffItem, CompassItem, ChangeItem

ERR_MSG = '请检查网站结构'


class HljCompassSpider(scrapy.Spider):
    """黑龙江公司信息爬虫， 1677页，16768个"""
    name = 'hlj_spider'
    allowed_domains = ['111.40.23.65']
    start_urls = ['http://111.40.23.65:8095/cmspsp/corpAction_queryPage.action']

    def start_requests(self):
        for link in self.start_urls:
            yield scrapy.Request(url=link, callback=self.parse_list)

    def parse_list(self, response):
        url = response.url
        cur_page_num = response.meta.get('cur_page_num', '1')
        line_nodes = response.xpath('//div[@class="main-content"]//tbody/tr')
        detail_links = []
        for node in line_nodes:
            href = node.xpath('.//a/@href').extract_first()
            detail_links.append(href)
        detail_links = [self.get_domain(url, 1) + href for href in detail_links if not href.startswith('http')]

        for link in detail_links:
            # print '请求连接：', link
            yield scrapy.Request(url=link, callback=self.parse_detail)
        # 翻页
        next_page_flag = response.xpath(u'//form[@name="PageForm"]//a[contains(text(), "下一页")]/@href').extract_first()
        if next_page_flag == '#':
            print '已经是最后一页了，当前页码:%s' % cur_page_num
            return
        next_page_num = str(int(cur_page_num)+1)
        # print '正在翻页', next_page_flag
        form_data = {
            "condition.orderByItem": '',
            "condition.pageNo": next_page_num,
            "rowCounts": "16769",
        }
        headers = {
            "Host": "111.40.23.65:8095",
            "Origin": "http://111.40.23.65:8095",
            "Referer": "http://111.40.23.65:8095/cmspsp/corpAction_queryPage.action",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
        }
        yield scrapy.FormRequest(url, formdata=form_data, headers=headers, callback=self.parse_list, meta={'cur_page_num': next_page_num})

    def parse_detail(self, response):
        """解析公司详细页面"""
        url = response.url
        print '打印网址:', url
        if u'无法打开页面' in response.text:
            print '无法打开页面'
            return
        # 获取基本工商信息
        compass_items = self.get_company_info(response)
        # print '打印工商信息：', compass_items

        # 获取企业资质信息(这里和全国版不一样)
        quality_items = self.get_qualification_info(response)
        # print '打印企业资质信息:', quality_items

        # # 注册人员信息
        tt_people_str = response.xpath(u'//div[@id="ry_info"]//a[contains(text(), "全部")]/i/text()').extract_first()
        tt_people = int(self.get_total_num(tt_people_str))
        meta = response.meta
        staff_container = []
        for i in [tt_people/10*10]:
            meta['cur_people'] = 10
            form_data = {
                'indexQuanBu': str(i)
            }
            headers = {
                'Host': self.get_domain(response.url, 0),
                'Origin': self.get_domain(response.url, 1),
                'Referer': response.url,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
            }
            response1 = requests.post(response.url, data=form_data, headers=headers)
            staff_container.extend(self.parse_turn_page_data(response1))
        # print '打印注册员工信息:', staff_container

        # # 变更信息
        modify_item = self.get_change_info(response)
        # print '打印变更信息:', modify_item
        yield JianzhuprojectItem({
               'compass_items': compass_items,
               'qualification_items': quality_items,
               'project_items': None,
               'staff_items': self.remove_depulicated(staff_container),
               'change_items': modify_item,
               'behavior_items': None,
               'crawl_time': self.fmt_time(),
               'source_link': url,
               'compass_name': compass_items[0]['compass_name'],
               'honor_code': compass_items[0]['honor_code'],
               # 'quality_link': url,
               # 'project_link': url,
               # 'staff_link': url,
               'other': None,
        })

    def get_domain(self, url, flag=1):
        """返回值: 协议 + 服务器名 + 域名 + /"""
        # http://111.40.23.65:8095
        if flag:
            return "://".join(urlparse(url)[:2]) + '/'
        else:
            return urlparse(url).netloc

    def get_company_info(self, response):
        compass_name = response.xpath('//input[@id="corpName"]/@value').extract_first()
        base_nodes = response.xpath('//div[@class="t_end"]/ul//tr/td/text()')

        info_list = []
        for i, node in enumerate(base_nodes):
            if i % 2 == 0:
                continue
            info_list.append(node.extract())
        [honor_code, representative, compass_type, provice, operating_addr] = info_list
        company_item = CompassItem({   # 自动检查key是否合法
             'compass_name': compass_name,
             'compass_link': response.url,
             'honor_code': honor_code,
             'representative': representative,
             'compass_type': compass_type,
             'provice': provice,
             'operating_addr': operating_addr,
             'establish_time': None,
             'register_capital': None,
             'net_asset': None,
             # 'crawl_time': self.fmt_time()
        })
        return [company_item]

    def get_qualification_info(self, response):
        """
        获取企业资质信息
        :param response: scrapy相应对象
        :return: 列表数组 [{}, {}]
        """
        item_list = self.my_version(response)
        return item_list

    def get_change_info(self, response):
        line_nodes = response.xpath('//div[@id="change_info"]//tbody/tr')
        change_list = []
        for node in line_nodes:
            _ = node.xpath('./td/text()').extract()
            change_date = _[1].strip('.0 ')   # 变更时间
            change_content = _[2].strip()   # 变更内容
            other_msg = ''
            change_list.append(ChangeItem({'change_date': change_date, 'change_content': change_content, 'other_msg': other_msg}))
        return change_list

    def get_total_num(self, tt_people_str):
        """获取总人数， 返回数字"""

        pp = re.compile(r'\((\d+)\)')
        return re.search(pp, tt_people_str).group(1)

    def parse_turn_page_data(self, response):
        # print '解析。。。'
        # meta = response.meta
        response = etree.HTML(response.text)
        line_nodes = response.xpath('//div[@id="ry_info"]//tbody[@id="quanbu"]/tr')
        staff_list = []
        for node in line_nodes:
            name = ''.join(node.xpath('./td/text()')).strip()
            id_card = ''.join(node.xpath('./td/text()')).strip()
            title = ''.join(node.xpath('./td/text()')).strip()
            title_code = ''.join(node.xpath('./td/text()')).strip()
            profession = ''.join(node.xpath('./td/text()')).strip()
            staff_item = StaffItem({
                'name': name,
                'id_card': id_card,
                'title': title,
                'title_code': title_code,
                'profession': profession,
                'person_detail_link': None,
                'licence_start_date': None,
                'licence_end_date': None
            })
            staff_list.append(staff_item)
        return staff_list

    # 提取资质，解析rowspan
    def my_version(self, response):
        text_str = response.text
        html = etree.HTML(text_str)
        nodes = html.xpath('//div[@id="qy_info"]//tbody/tr')
        cnt_list = []
        for node in nodes:
            cnt_list.append(len(node.xpath('./td')))
        item_list = []
        for i, num in enumerate(cnt_list):
            if int(num) < 7:
                _class = ''.join(nodes[i].xpath('./td/@class'))
                if _class == 'tl':
                    qua_type = item_list[-1]['quality_type']
                    qua_name = nodes[i].xpath('./td/text()')[0]
                    qua_code = item_list[-1]['quality_code']
                    quality_end_date = item_list[-1]['quality_end_date']
                    authority = item_list[-1]['authority']
                    quality_detail_link = item_list[-1]['quality_detail_link']   # 需要正则拼接
                else:
                    qua_type = qua_name = qua_code = quality_end_date = authority = quality_detail_link = ERR_MSG
            else:
                qua_type = ''.join(nodes[i].xpath('./td[2]/text()')).strip()
                qua_code = ''.join(nodes[i].xpath('./td[3]/text()')).strip()
                qua_name = ''.join(nodes[i].xpath('./td[4]/text()')).strip()
                quality_end_date = ''.join(nodes[i].xpath('./td[5]/text()')).strip()
                authority = ''.join(nodes[i].xpath('./td[6]/text()')).strip()
                quality_detail_link = ''.join(nodes[i].xpath('./td[7]/a/@onclick')).strip()

            item = QualityItem({'quality_type': qua_type,
                                'quality_code': qua_code,
                                'quality_name': qua_name,
                                'quality_start_date': None,
                                'quality_end_date': quality_end_date,
                                'quality_detail_link': quality_detail_link,
                                'authority': authority,
                                })
            item_list.append(item)
        return item_list

    def fmt_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    def remove_depulicated(self, items):
        res = reduce(lambda new_items, item: new_items if item['name'] in set(
            [_['name'] for _ in new_items]) else new_items + [item], [[]] + items)
        return res


if __name__ == '__main__':
    cmdline.execute('scrapy crawl hlj_spider'.split())