
# coding=utf-8
import scrapy


class BaseCompass(scrapy.Spider):
    name = ''
    allow_domain = ['']
    start_urls = ['']
    extract_dict = None

    def start_requests(self):
        print('start_requests.....')
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_list)

    def parse_list(self, response):

        nodes = response.xpath()
        for node in nodes:
            compass_name = node.xpath()
            detail_link = node.xpath()
            out_province = ''

        self.turn_page()


    def turn_page(self):
        pass


    def handle_cname(self, cname):
        """
        处理公司名称
        :param cname: 字符串公司名
        :return: 干净的名字
        """
        pass

    def handle_cdetail_link(self, clink):
        """
        处理进入公司详细页的链接
        :param clink: 字符串链接, 最原始
        :return: 直接能够使用的链接,（无论是post还是get）
        """
        pass

    def handles_province(self, cprovice):
        """
        处理省份信息
        :param cprovice:
        :return: 只有省信息
        """
        pass

