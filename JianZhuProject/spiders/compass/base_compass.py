
# coding=utf-8
import scrapy
from scrapy import cmdline

from JianZhuProject import sit_list
from JianZhuProject.items import NameItem

class BaseCompass(scrapy.Spider):
    name = ''
    allow_domain = ['']
    start_urls = ['']
    extract_dict = None

    def start_requests(self):
        print('start_requests.....')
        for url, sit in self.start_urls:
            headers = self.get_header(url, flag='1')
            yield scrapy.Request(url=url, callback=self.parse_list, headers=headers,
                                 meta={'sit': sit, 'pre_page_num': '0'})

    def parse_list(self, response):
        print('parse_list....', response.text)
        item_contains = []
        url = response.url
        sit = response.meta['sit']
        if sit == sit_list[0]:
            inner_nodes = response.xpath(self.extract_dict['inner']['nodes'])
            inner = self.extract_dict['inner']
            print("inner_nodes:", len(inner_nodes))
            for node in inner_nodes:
                item = NameItem()
                item['compass_name'] = self.handle_cname(node.xpath(inner['cname']).extract_first(), 'inner')
                item['detail_link'] = self.handle_cdetail_link(node.xpath(inner['detail_link']).extract_first(),
                                                               'inner', url)
                item['out_province'] = inner['out_province'][1] if isinstance(inner['out_province'], list) else 'None'
                item_contains.append(item)
        if sit == sit_list[1]:
            print(u'解析外省....')
            outer_nodes = response.xpath(self.extract_dict['outer']['nodes'])
            outer = self.extract_dict['outer']
            for node in outer_nodes:
                item = NameItem()
                item['compass_name'] = self.handle_cname(node.xpath(outer['cname']).extract_first(), 'outer')
                item['detail_link'] = self.handle_cdetail_link(node.xpath(outer['detail_link']).extract_first(),
                                                               'outer', url)
                item['out_province'] = self.handle_out_province(node.xpath(outer['out_province']).extract_first())
                item_contains.append(item)

        yield {'item_contains': item_contains}

        yield self.turn_page(response)

    def turn_page(self, response):
        print('必须重写turn_page方法')
        pass

    def handle_out_province(self, s):
        return s.strip('\r\n\t ')

    def handle_cname(self, cname, flag='inner'):
        """
        处理公司名称
        :param cname: 字符串公司名
        :return: 干净的名字
        """
        return cname.strip('\r\n\t ')

    def handle_cdetail_link(self, clink, flag='inner', url=''):
        """
        处理进入公司详细页的链接
        :param clink: 字符串链接, 最原始
        :return: 直接能够使用的链接,（无论是post还是get）
        """
        if clink.startswith('http'):
            good_link = clink
        else:
            domain_str = self.get_domain_info(url)  # 待重写，domain_str可变, 结尾一定没有/
            if clink.startswith('..'):
                good_link = clink.replace('..', domain_str, 1)
            elif clink.startswith('.'):
                good_link = clink.replace('.', domain_str, 1)
            elif clink.startswith('/'):
                good_link = domain_str + clink
            else:
                print('请重写该方法handle_cdetail_link')
                good_link = ''
        return good_link

    def handles_province(self, cprovice):
        """
        处理省份信息
        :param cprovice:
        :return: 只有省信息
        """
        return cprovice.strip('\r\n\t ')

    def get_domain_info(self, link):
        # 根据link的开头特点需要进行重写
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        import urlparse
        res = urlparse.urlparse(link)
        return res.scheme + '://' + res.netloc
        # return 'jzjg.gzjs.gov.cn:8088'

    def get_header(self, url, flag='1'):
        domain_str = self.get_domain_info(url)
        header = {
            'Host': domain_str.split('//')[-1],
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
        }
        if flag not in (1, '1'):
            header['Origin'], header['Referer'] = domain_str, url
        return header

    def run(self):
        cmdline.execute(['scrapy', 'crawl', self.name])
