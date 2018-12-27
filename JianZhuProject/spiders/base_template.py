# coding=utf-8
# ----新爬虫base_class.py基类
from __future__ import print_function
import time

import scrapy
from scrapy import cmdline

from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import JianzhuprojectItem
# from JianZhuProject.spiders.extract.extract_dict import EXTRACT_DICT
from extract.extract_compass import ExtractCompass


# 抽取工程类
from extract.extract_project import ExtractProject
# 抽取员工类
from extract.extract_staff import ExtractStaff
# 抽取行为类(诚信、良好、不良)
from extract.extract_behavior import ExtractBehavior
# 抽取变更类
from extract.extract_change import ExtractChange


Postion = ['ListPage', 'DetailPage', 'QualPage', 'ProjPage', 'StaffPage']


class ParentSpider(scrapy.Spider):
    name = ''

    allowed_domains = []
    start_urls = []

    extract_dict = None  # 字段提取大字典
    cnt = 1
    redis_tools = RedisTools()

    def __init__(self):
        super(ParentSpider, self).__init__()
        assert all([self.name, self.allowed_domains, self.start_urls, self.extract_dict]), '在关键的4个大变量中有未自实现的值, 请检查子类'

    def start_requests(self):
        print('start_requests.....')
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_list)

    def parse_list(self, resp_list_page):
        print('parse_list......')
        url = resp_list_page.url
        meta = resp_list_page.meta
        line_nodes = resp_list_page.xpath(self.extract_dict['list_page']['lines_rule'])
        print('\t\tline_nodes:', len(line_nodes))
        for node in line_nodes:
            position = Postion[1]   # DetailPage
            link = node.xpath(self.extract_dict['list_page']['detail_link_rule']).extract_first()
            good_link = self.handle_detail_link(url, link)
            is_crawled = self.redis_tools.check_finger(good_link)
            if is_crawled:
                print('%s已经抓取过'%good_link)
                continue
            detail_headers = self.get_headers(url, good_link, position)
            listpage_data = self.get_info_listPage(resp_list_page)
            meta['listpage_data'] = listpage_data
            if self.extract_dict['detail_page']['method'].upper() == 'GET':
                print('\t\t发详细页请求：get')
                yield scrapy.Request(url=good_link, callback=self.parse_detail, headers=detail_headers, meta=meta)
            else:
                # 注意：如果post方式、url查询参数动态变化，根据情况重写handle_detail_link()
                formdata = self.get_form_data(resp_list_page, position)
                yield scrapy.FormRequest(url=good_link, callback=self.parse_detail, headers=detail_headers, formdata=formdata, meta=meta)
            print('正在抓取第%d个公司相关信息'% self.cnt)
            self.cnt += 1
            # break

        if self.judge_next_page(resp_list_page):
            print('翻页。。。。')
            yield self.parse_turn_page(resp_list_page, method=self.extract_dict['list_page']['method'])
        else:
            print('翻页结束，当前是第{}页'.format(1))

    def parse_detail(self, resp_detail):
        print('parse_detail......')
        url = resp_detail.url
        compass_items = self.extract_compass_info(resp_detail, self.extract_dict['detail_page']['compass'])  # [item]
        print('len(compass_items): ', len(compass_items))

        quality_items = self.extract_qualification_info(resp_detail, self.extract_dict['detail_page']['qualification'])  # [item, item...]
        print('len(quality_items): ', len(quality_items))

        project_link = self.get_project_link(resp_detail, compass_items)   #
        print('len(project_link): ', len([project_link]))
        staff_link = self.get_staff_link(resp_detail, compass_items)
        print('len(staff_link): ', len([staff_link]))
        behavior_link = self.get_behavior_link(resp_detail, compass_items)  # 良好、不良
        print('len(behavior_link): ', len([behavior_link]))
        change_link = self.get_change_link(resp_detail, compass_items)
        print('len(change_link): ', len([change_link]))

        same_seq = self.get_same_seq([project_link, staff_link, behavior_link, change_link], url)
        yield JianzhuprojectItem({
               'compass_items': compass_items,
               'qualification_items': quality_items,
               'project_items': None,
               'staff_items': None,
               'change_items': None,
               'behavior_items': None,
               'crawl_time': self.fmt_time(),

               'compass_name': compass_items[0]['compass_name'],
               'honor_code': compass_items[0]['honor_code'],
               'source_link': url,

               'project_link': project_link,
               'staff_link': staff_link,
               'behavior_link': behavior_link,
               'change_link': change_link,
               'same_seq': same_seq,
        })

    def judge_next_page(self, resp):
        cur_page_num = resp.meta.get('cur_page_num', '1')
        is_have = resp.xpath(self.extract_dict['list_page']['have_next_page_rule'])
        total_page_num = resp.xpath(self.extract_dict['list_page']['total_page_num_rule'])
        return is_have and int(cur_page_num) < int(total_page_num)

    def parse_turn_page(self, resp_list, method):
        # 下一页参数
        print('parse_turn_page')
        response = resp_list
        url = response.url
        cur_page = int(response.meta.get('cur_page', 1))
        query_data = self.get_query_data(response, cur_page)  # query_string 字典
        form_data = self.get_form_data(response, Postion[0])  # form_data字典
        headers = self.get_headers(url, url, position=Postion[0])
        print('即将范第{}页.......'.format(cur_page))
        url = self.handle_url(url, query_data)
        response.meta['cur_page'] = str(cur_page + 1)
        if method.upper() == 'POST':
            return scrapy.FormRequest(url, callback=self.parse_list, formdata=form_data, headers=headers, meta=response.meta, dont_filter=True)
        else:
            # 注意：如果post方式，url查询参数动态变化，根据情况重写handle_url()
            return scrapy.Request(url, callback=self.parse_list, headers=headers, meta=response.meta)

    def get_same_seq(self, link_list, source_url):
        seq = ''
        for link in link_list:
            if link == source_url:
                seq += '1'
            else:
                seq += '0'
        assert len(seq) == len(link_list), 'seq长度错误, 请检查get_same_seq方法'
        return seq

    def handle_detail_link(self, url, link):
        if link.startswith('http'):
            good_link = link
        else:
            domain_str = self.get_domain_info(url)  # 待重写，domain_str可变, 结尾一定没有/
            if link.startswith('..'):
                good_link = link.replace('..', domain_str, count=1)
            elif link.startswith('.'):
                good_link = link.replace('.', domain_str, count=1)
            elif link.startswith('/'):
                good_link = domain_str + link
            else:
                print('请重写该方法')
                good_link = ''
        return good_link


    def handle_url(self, url, query_data):
        # 如果是请求ur的参数部分动态变化，则重写该方法
        return url

    def fmt_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    def get_form_data(self, response, postion):
        cur_page = response.meta.get('cur_page', 1)
        __VIEWSTATE = response.xpath('//input[@id="__VIEWSTATE"]/@value').extract_first()
        __EVENTVALIDATION = response.xpath('//input[@id="__EVENTVALIDATION"]/@value').extract_first()
        hidd_type = "1"
        newpage = str(int(cur_page) + 1)
        __EVENTTARGET = "Linkbutton3"
        return {"__VIEWSTATE": __EVENTVALIDATION, "__EVENTVALIDATION": __EVENTVALIDATION, "hidd_type": hidd_type, "newpage": newpage, "__EVENTTARGET": __EVENTTARGET}

    def get_query_data(self, response, cur_page):
        return {}

    def get_headers(self, url, link, position):
        # position: 只能取值-列表页ListPage、详细页DetailPage、资质页QualPage、工程页ProjPage、人员页StaffPage
        return {}

    def get_domain_info(self, link):
        # 根据link的开头特点需要进行重写
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        import urlparse
        res = urlparse.urlparse(link)
        return res.scheme + '://' + res.netloc

    def get_info_listPage(self, resp_list_page):
        """
        备用, 部分数据须从列表页才能获取完整数据, 自实现(一般不建议)
        :param resp_list_page: 列表页的response
        :return: 字典数据
        """
        return {}

    def extract_qualification_info(self, resp_detail, qual_rules):
        # 再一次发送请求
        return {"name": "需要重写"}

    def extract_compass_info(self, resp_detail, com_rules):
        return {}


    def get_staff_link(self, resp_detail, compass_items):
        return ''

    def get_behavior_link(self, resp_detail, compass_items):
        return ''

    def get_change_link(self, resp_detail, compass_items):
        return ''

    def get_project_link(self, resp_detail, compass_items):
        return ''

    def run(self):
        cmdline.execute(['scrapy ', 'crawl', self.name])