# -*- coding: utf-8 -*-
import re
import time
import random

import requests
import scrapy
from lxml import etree
from scrapy import cmdline
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.ua import ua_pools


class JzscSpider(scrapy.Spider):
    name = 'jzsc'
    allowed_domains = ['jzsc.mohurd.gov.cn']
    start_urls = ['http://jzsc.mohurd.gov.cn/dataservice/query/comp/list']
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
    }
    page_num = 1
    custom_settings = {
        "DOWNLOAD_DELAY": 2
    }
    redis_tools = RedisTools()

    def start_requests(self):
        params = self.get_params()
        headers = self.get_headers()
        for url in self.start_urls:
            yield scrapy.FormRequest(url, formdata=params, callback=self.parse_list, headers=headers, meta={'page_num': '1'})

    def get_headers(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
            "Host": "jzsc.mohurd.gov.cn",
            "Origin": "http://jzsc.mohurd.gov.cn",
            "Referer": "http://jzsc.mohurd.gov.cn/dataservice/query/comp/list",
        }
        return headers

    def get_params(self, flag='list'):
        """
        获取请求参数
        :flag: 固定取值：'list'、'detail'
        :return: json字典
        """
        if flag == 'list':
            with open('record_cur_page.txt') as fp:
                record_num = fp.read().strip() or '1'
            form_data = {
                "$total": "329569",
                "$reload": "0",
                "$pg": str(int(record_num)+1),
                "$pgsz": "15",
            }
        return form_data

    def parse_list(self, response):
        """
        在列表页获取详细页的连接url
        :param response:
        :return: url
        """
        if response.status != 200 or 'cursorDefault' not in response.text:
            cur_page = int(response.meta.get("$pg"))
            print '在第%d页的页面结构不对或被反扒了'% cur_page
            with open('record_cur_page.txt') as fp:
                fp.write(cur_page)
                return
        # 提取详细页面的连接
        link_list = response.xpath(u'//tbody[@class="cursorDefault"]/tr/td[@data-header="企业名称"]/a/@href').extract()
        # print('本页面的连接有%d个' % len(link_list))
        for link in link_list:
            if not link.startswith('http'):
                link = 'http://jzsc.mohurd.gov.cn' + link
            # 加redis指紋记录
            is_crawl = self.redis_tools.check_finger(link)
            if is_crawl is False:
                time.sleep(random.random() * 2)
                self.default_headers['User-Agent'] = random.choice(ua_pools)
                yield scrapy.Request(url=link, headers=self.default_headers, callback=self.parse_detail)
            else:
                print u'link=%s已经爬取过.'% link

        # TODO 翻页
        time.sleep(random.random()*3)
        page_pattern = re.compile(r'__pgfm\(.*?({.*?})\)')
        res = re.search(page_pattern, response.text).groups(1)[0]
        json_page_data = eval(res)
        total, cur_page, page_size = json_page_data['$total'], json_page_data['$pg'],json_page_data['$pgsz']
        with open('record_cur_page.txt', 'w') as fp:
            fp.write(str(cur_page))
        if int(cur_page) < int(total):
            url, meta = response.url, response.meta
            form_data = {
                "$total": str(total),
                "$reload": "0",
                "$pg": str(int(cur_page) + 1),
                "$pgsz": "15",
            }
            print '进入下一页:', int(cur_page) + 1
            yield scrapy.FormRequest(url, formdata=form_data, callback=self.parse_list, headers=self.get_headers(), meta={'cur_page': form_data['$pg']})
        else:
            print '没有下一页，最大页码%d, 当前页码: %d' %(total, cur_page)

    def parse_detail(self, response):
        """
        解析该网址显示的公司信息
        :param response:
        :return:
        """
        # 获取base_info
        base_info = self.get_base_info(response)
        # print(u'打印base_info：', base_info)

        # 资质连接，注册人员连接， 工程项目连接, 不良行为连接.....
        [quality_link, staff_link, project_link, bad_link, good_link, black_link, change_link] = response.xpath('//div[@class="query_info_tab"]//a/@data-url').extract()
        # 获取quality_info
        quality_link = 'http://jzsc.mohurd.gov.cn' + quality_link
        # quality_info = self.get_quality_info(quality_link)
        # print(u'打印quality_info：', quality_info)

        # headers = self.get_headers()
        # headers['Referer'] = response.url
        # 注册人员信息staff_info
        # staff_info = self.get_staff_info(staff_link)
        # 工程项目信息project_info
        project_link = 'http://jzsc.mohurd.gov.cn' + project_link
        headers = response.headers
        headers['Referer'] = project_link
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        # project_info = yield scrapy.Request(project_link, headers=headers, callback=self.get_project_info, meta={'cur_page': 1})  # $pg
        # project_info = self.get_project_info(staff_link, headers)
        item = {
            'entry_link': response.url,
            'base_info': base_info,
            'quality_link': quality_link,
            'project_link': project_link,
            'staff_link': 'http://jzsc.mohurd.gov.cn' + staff_link,
            'bad_link': 'http://jzsc.mohurd.gov.cn' + bad_link,
            'change_link': 'http://jzsc.mohurd.gov.cn' + change_link,
            'good_link': 'http://jzsc.mohurd.gov.cn' + good_link,
            'black_link': 'http://jzsc.mohurd.gov.cn' + black_link
        }
        yield item

    def get_base_info(self, response):
        compass_name = response.xpath('//div[contains(@class, "query_info_box")]//b/text()').extract()[0]
        [honor_code, representative, compass_type, provice, operating_addr] = response.xpath('//div[@class="plr"]//tbody//tr/td[@data-header]/text()').extract()
        base_info = {'compass_name': compass_name, 'honor_code': honor_code, 'representative': representative, 'compass_type': compass_type, 'provice': provice, 'operating_addr': operating_addr}
        return base_info

    # def get_quality_info(self, link=None):
    #     if not link.startswith('http'):
    #         link = 'http://jzsc.mohurd.gov.cn' + link
    #     response = requests.get(link, headers=self.default_headers)
    #     html = etree.HTML(response.content)
    #     line_nodes = html.xpath('//tbody[@class="cursorDefault"]/tr')
    #     quality_info_list = []
    #     for i, node in enumerate(line_nodes):
    #         tmp_dict = {}
    #         tmp_dict['quality_type'] = node.xpath(u'./td[@data-header="资质类别"]/text()')[0]
    #         tmp_dict['quality_code'] = node.xpath(u'./td[@data-header="资质证书号"]/text()')[0]
    #         tmp_dict['quality_name'] = node.xpath(u'./td[@data-header="资质名称"]/text()')[0].strip()
    #         tmp_dict['quality_date'] = node.xpath(u'./td[@data-header="发证日期"]/text()')[0]
    #         tmp_dict['validity_date'] = node.xpath(u'./td[@data-header="证书有效期"]/text()')[0]
    #         tmp_dict['authority'] = node.xpath(u'./td[@data-header="发证机关"]/text()')[0]
    #         quality_info_list.append(tmp_dict)
    #     quality_info = quality_info_list
    #     return quality_info
    #
    # def get_staff_info(self, link=None):
    #     """
    #     获取公司注册人员信息
    #     :return: json字典
    #     """
    #     if not link.startswith('http'):
    #         link = 'http://jzsc.mohurd.gov.cn' + link
    #     response = requests.get(link, headers=self.default_headers)
    #
    #     if '暂未查询到' in response.content:
    #         print('暂未查询到已登记入库信息')
    #         return
    #
    #     html = etree.HTML(response.content)
    #     staff_nodes = html.xpath('//tbody/tr')
    #     staff_info = []
    #     for node in staff_nodes:
    #         tmp_dict = {}
    #         try:
    #             person_link = node.xpath('.//a[@onclick]/@onclick')[0]  # 正则提取url 'http://jzsc.mohurd.gov.cn'
    #             name = node.xpath(u'.//a[@onclick]/text()')[0]
    #             pp = re.compile(r".*?='(.*)'")
    #             person_link = 'http://jzsc.mohurd.gov.cn' + re.search(pp, person_link).group(1)
    #         except IndexError as e:
    #             print('页面html:', response.content)
    #         try:
    #             # [id_card, title, title_code, profession] = node.xpath('./td[@data-header][position()>2]/text()')
    #             id_card = node.xpath(u'./td[@data-header="身份证号"]/text()')[0]
    #             title = node.xpath(u'./td[@data-header="注册类别"]/text()')[0]
    #             title_code = node.xpath(u'./td[contains(@data-header, "注册号")]/text()')[0]
    #             profession = ''.join(node.xpath(u'./td[contains(@data-header, "注册专业")]/text()')) or 'None'
    #         except:
    #             print(u'异常', link)
    #         else:
    #             tmp_dict['name'], tmp_dict['id_card'], tmp_dict['title'], tmp_dict['title_code'], tmp_dict[
    #                 'profession'] = name, id_card, title, title_code, profession
    #             staff_info.append(tmp_dict)
    #     print(u'打印人工信息:')
    #     print(len(staff_info), staff_info)
    #     return {}
    #
    # def get_project_info(self, link, headers):
    #     """
    #     获取该公司历史的工程项目
    #     :return: json
    #     """
    #     if u'暂未查询到' in response.text:
    #         print '暂未查询到已登记入库信息'
    #         return None
    #
    #     # 获取 总页数
    #     project_info_list = []
    #     line_nodes = response.xpath('//tbody/tr[position()<26]')
    #     for i, node in enumerate(line_nodes):
    #         tmp_dict = {}
    #         tmp_dict['proj_code'] = node.xpath(u'./td[@data-header="项目编码"]/text()').extract()[0]
    #         tmp_dict['proj_name'] = node.xpath(u'./td[@data-header="项目名称"]//text()').extract()[0]
    #         tmp_dict['proj_site'] = ''.join(node.xpath(u'./td[@data-header="项目属地"]/text()').extract()).strip() or 'None'
    #         tmp_dict['proj_type'] = ''.join(node.xpath(u'./td[@data-header="项目类别"]/text()').extract()) or 'None'
    #         tmp_dict['employer'] = ''.join(node.xpath(u'./td[@data-header="建设单位"]/text()').extract()) or 'None'
    #         project_info_list.append(tmp_dict)
    #     print '打印prj：', project_info_list
    #     return project_info_list
    #     # 翻页
    #     # cur_page = response.meta['cur_page']
    #     # if cur_page < 5:
    #     #     headers = response.headers
    #     #     print '工程项目在发第%d页面的请求...'% (int(cur_page)+1)
    #     #     # self.turn_page_project(response.url, headers, cur_page)
    #     # else:
    #     #     print '工程页面翻页完毕', project_info_list
    #     #     return project_info_list
    #
    # def get_history_behavior(self):
    #     """
    #     获取公司历史行为信息：不良信息bad_info、良好行为good_info、黑名单记录blacklist_info、变更记录change_info
    #     :return: json大集合
    #     """
    #     return {}
    #
    # def turn_page_project(self, link, headers, cur_page):
    #     """工程项目的翻页方法"""
    #     # http://jzsc.mohurd.gov.cn/dataservice/query/comp/compPerformanceListSys/001607220057358999
    #     # post 请求
    #     form_data = {
    #         "$total": "76",
    #         "$reload": "0",
    #         "$pg": str(int(cur_page + 1)),
    #         "$pgsz": "25",
    #     }
    #     yield scrapy.FormRequest(link, formdata=form_data, headers=headers)
    #

if __name__ == '__main__':
    cmdline.execute('scrapy crawl jzsc'.split())
