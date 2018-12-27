# -*- coding: utf-8 -*-
import codecs
import datetime
import logging
import time

import scrapy
import re
import os
from scrapy import cmdline

from JianZhuProject.auxiliary.redis_tools import RedisTools
from JianZhuProject.items import CompassItem, QualityItem, JianzhuprojectItem
from JianZhuProject.settings import ALL_FINGER_CONTAINS

now_date_time = datetime.datetime.now()


class YunNanSpider(scrapy.Spider):
    name = 'yun_nan_spider'
    allowed_domains = ['220.163.15.148']
    start_urls = ['http://220.163.15.148/InfoQuery/EnterpriseList?page=1']
    redis_tools = RedisTools()
    LOG_FILE = 'logs/{}_{}_{}_{}.log'.format(name, now_date_time.year, now_date_time.month, now_date_time.day)
    log_path = os.path.join(os.path.abspath('..'), LOG_FILE)
    log_dir = os.path.dirname(log_path)
    if not os.path.exists(log_dir):
        os.makedirs(os.path.dirname(log_path))

    def parse(self, response):
        url = response.url
        line_links = response.xpath('//tbody/tr/td[@class="left"]/a/@href').extract()
        line_links = ['http://220.163.15.148' + link for link in line_links]
        for link in line_links:
            is_crawled = self.redis_tools.check_finger(link, name=ALL_FINGER_CONTAINS)
            if is_crawled:
                print('%s已经抓取过！'%link)
                continue
            if is_crawled:
                logging.info('%s has already crawled！', link)
                continue
            print 'parse detail page info.....'
            headers = {
                'Referer': url,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            }
            yield scrapy.Request(url=link, callback=self.parse_detail, headers=headers)
        # 翻页
        ss = response.xpath('//div[@class="jump fl"]/span[1]/text()').extract_first()
        [total_line, per_page] = re.findall('\d+', ss)   # 总记录数, 每页显示多少行
        total_page = (int(total_line) / int(per_page) + 1) if int(total_line) % int(per_page) else int(total_line) / int(per_page)
        next_page_num = int(response.meta.get('cur_page_num', '1')) + 1
        if next_page_num > total_page:
            logging.info('不能继续翻页啦, 当前是第{}页,已经是最后一页啦'.format(next_page_num))
            return
        link = 'http://220.163.15.148/InfoQuery/EnterpriseList?page={}'
        next_link = link.format(next_page_num)
        # print '下一页...', next_link
        yield scrapy.Request(next_link, callback=self.parse, meta={'cur_page_num': next_page_num})

    def parse_detail(self, response):
        url = response.url
        compass_items = self.get_company_info(response)
        quality_items = self.get_qualification_info(response)
        # quality_items = self.get_project_info(response)
        yield JianzhuprojectItem({
            'compass_items': compass_items,
            'qualification_items': None,
            'project_items': None,
            'staff_items': None,
            'change_items': None,
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

    def get_company_info(self, response):
        compass_name = ''.join(response.xpath('//div[@class="tLayer-1"]/h3/text()').extract()).strip()
        honor_code, register_capital = response.xpath('//div[@class="tLayer-1"]/table/tr[1]/td[not(@class)]/text()').extract()
        honor_code = 'None' if len(honor_code) < 7 else honor_code
        representive = ''.join(response.xpath('//div[@class="tLayer-1"]/table/tr[2]/td[not(@class)][1]/text()').extract())
        compass_type = response.xpath('//div[@class="tLayer-1"]/table/tr[3]/td[not(@class)]/text()').extract()[0]
        establish_time = ''.join(response.xpath('//div[@class="tLayer-1"]/table/tr[4]/td[not(@class)][2]/text()').extract()).strip()
        provice = ''.join(response.xpath('//div[@class="tLayer-1"]/table/tr[5]/td[not(@class)][2]/text()').extract())
        operating_addr = ''.join(response.xpath('//div[@class="tLayer-1"]/table/tr[6]/td[not(@class)][1]/text()').extract())
        company_item = CompassItem({  # 自动检查key是否合法
            'compass_name': compass_name,
            'compass_link': response.url,
            'honor_code': honor_code,  # 信用代码
            'representative': representive,  # 法人
            'compass_type': compass_type,  # 公司类型
            'provice': provice,
            'operating_addr': operating_addr,  # 运营地址
            'establish_time': establish_time,
            'register_capital': register_capital,
            'net_asset': None,
        })
        # print company_item
        return [company_item]

    def get_qualification_info(self, response):
        pass

    def get_project_info(self, response):
        pass

    def fmt_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    def get_headers(self):
        headers = {
            'Referer': 'http://220.163.15.148/InfoQuery/EnterpriseList?page=769',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
        }
        return headers


if __name__ == '__main__':
    cmdline.execute(['scrapy', 'crawl ', YunNanSpider.name])

