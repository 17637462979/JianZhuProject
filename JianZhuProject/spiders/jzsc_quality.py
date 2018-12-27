# -*- coding: utf-8 -*-
import re
import time
import random

import requests
import scrapy
from lxml import etree
from scrapy import cmdline
from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import QualityItem, StaffItem, ProjectItem
from JianZhuProject.auxiliary.mongo_tools import MongoTools


class JzscQualitySpider(scrapy.Spider):
    name = 'jzsc_quality'
    allowed_domains = ['jzsc.mohurd.gov.cn']
    start_urls = ['http://jzsc.mohurd.gov.cn/dataservice/query/comp/list']
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
    }
    page_num = 1
    mongo_tools = MongoTools()
    redis_tools = RedisTools()

    def start_requests(self):
        skip = 0
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
            "Host": "jzsc.mohurd.gov.cn",
        }

        result = self.mongo_tools.get_documents(batch_size=50, skip_num=skip)
        redis_collections = ['compass', 'quality', 'staff', 'project']
        for i, data in enumerate(result):
            quality_link, staff_link, project_link, compass_link = data['quality_link'], data['staff_link'], data['project_link'], data['entry_link']
            for url in [quality_link]:
                if self.redis_tools.check_finger(finger=url, name=redis_collections[i]):
                    yield scrapy.FormRequest(url, callback=self.parse, headers=headers, meta={'compass_link': compass_link, 'quality_info_list': []})
                else:
                    print url, '已经抓取过了'


    def parse(self, response):
        """
        实质是翻页控制
        :param response: scrapy 响应对象
        :return: 该公司所有的资质信息 [{}, {}, {}.....]
        """
        meta, url = response.meta, response.url
        print url
        headers = {
            'Referer': url,
            'Origin': "http://jzsc.mohurd.gov.cn",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }
        if '__pgfm' in response.text:
            page_pattern = re.compile(r'__pgfm\(.*?({.*?})\)')
            res = re.search(page_pattern, response.text).groups(1)[0]
            json_page_data = eval(res)
            total, cur_page, page_size = json_page_data['$total'], json_page_data['$pg'], json_page_data['$pgsz']
        else:
            total = 1
        compass_link = meta['compass_link']
        items_list = []
        for pnum in range(total):   # 总页数
            form_data = {
                "$total": total,
                "$reload": "0",
                "$pg": str(int(pnum) + 1),
                "$pgsz": "25",
            }
            response = requests.post(url=url, headers=headers, data=form_data)
            quality_info_list = self.parse_page(response, compass_link)
            items_list.extend(quality_info_list)
        # print '打印len(items_list)', len(items_list)
        return {'items_list': items_list}

    def parse_page(self, response, compass_link):
        """
        解析资质信息，以页面为单位
        :param response:
        :param compass_link: 公司连接
        :return: [item1, item2]
        """
        if 'caDetailList' in response.url:
            return self.parse_quality(response, compass_link)
        elif 'regStaffList' in response.url:
            pass
            # return self.parse_staff(response, compass_link)
        else:
            # 'compPerformanceListSys'  工程项目信息
            # return self.parse_project(response, compass_link)
            pass

    def parse_quality(self, response, compass_link):
        print '解析资质资格信息.....'
        html = etree.HTML(response.text)
        line_nodes = html.xpath('//tbody/tr')
        quality_info_list = []
        print len(line_nodes)
        for i, node in enumerate(line_nodes):
            quality = QualityItem()
            quality['quality_type'] = ''.join(node.xpath(u'./td[@data-header="资质类别"]/text()'))
            quality['quality_code'] = ''.join(node.xpath(u'./td[@data-header="资质证书号"]/text()'))
            quality['quality_name'] = ''.join(node.xpath(u'./td[@data-header="资质名称"]/text()')).strip()
            quality['quality_date'] = ''.join(node.xpath(u'./td[@data-header="发证日期"]/text()'))
            quality['validity_date'] = ''.join(node.xpath(u'./td[@data-header="证书有效期"]/text()'))
            quality['authority'] = ''.join(node.xpath(u'./td[@data-header="发证机关"]/text()'))
            quality['compass_link'] = compass_link
            quality['quality_link'] = response.url
            quality['crawl_time'] = self.fmt_time()
            quality_info_list.append(quality)
        return quality_info_list

    def parse_staff(self, response, compass_link):
        print '解析注冊員工信息....'
        html = etree.HTML(response.content)
        staff_nodes = html.xpath('//tbody/tr')
        staff_info_list = []
        for i, node in enumerate(staff_nodes[:-1]):
            staff = StaffItem()
            staff['name'] = node.xpath(u'.//a[@onclick]/text()')[0]
            staff['id_card'] = node.xpath(u'./td[@data-header="身份证号"]/text()')[0]
            staff['title'] = node.xpath(u'./td[@data-header="注册类别"]/text()')[0]
            staff['title_code'] = node.xpath(u'./td[contains(@data-header, "注册号")]/text()')[0]
            staff['profession'] = ''.join(node.xpath(u'./td[contains(@data-header, "注册专业")]/text()')) or 'None'
            staff['html_link'] = response.url
            staff['person_link'] = node.xpath('.//a[@onclick]/@onclick')[0]
            staff['compass_link'] = compass_link
            staff['crawl_time'] = self.fmt_time()
            staff_info_list.append(staff)
        print '打印员工信息..', staff_info_list
        return staff_info_list

    def parse_project(self, response, compass_link):
        print '解析工程項目信息.....'
        html = etree.HTML(response.text)
        project_info_list = []
        line_nodes = html.xpath('//tbody/tr[position()<26]')
        for i, node in enumerate(line_nodes):
            project = ProjectItem()
            project['proj_code'] = node.xpath(u'./td[@data-header="项目编码"]/text()')[0]
            project['proj_name'] = node.xpath(u'./td[@data-header="项目名称"]//text()')[0]
            project['proj_site'] = ''.join(node.xpath(u'./td[@data-header="项目属地"]/text()')).strip() or 'None'
            project['proj_type'] = ''.join(node.xpath(u'./td[@data-header="项目类别"]/text()')) or 'None'
            project['employer'] = ''.join(node.xpath(u'./td[@data-header="建设单位"]/text()')) or 'None'
            project['proj_link'] = node.xpath('.//a[@onclick]/@onclick')[0]
            project['compass_link'] = compass_link
            project['crawl_time'] = self.fmt_time()
            project_info_list.append(project)
        print '打印prj：', project_info_list
        return project_info_list

    def fmt_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))


if __name__ == '__main__':
    cmdline.execute('scrapy crawl jzsc_quality'.split())

