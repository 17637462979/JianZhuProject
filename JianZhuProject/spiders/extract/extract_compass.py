# coding=utf-8
from JianZhuProject.items import CompassItem
from dateutil import parser

class ExtractCompass():
    def extract_compass_info(self, resp_detail, com_rules):
        response = resp_detail
        node = response.xpath(com_rules.get('cnodes')[0])[0]
        company_item = CompassItem()
        company_item['compass_link'] = response.url
        for k, v in com_rules.items():
            if 'node' in k:
                continue
            rule, map_key = v[0], v[1]
            if v[0] is None:
                company_item[map_key] = ''
            else:
                company_item[map_key] = node.xpath(rule).extract_first().replace('\n', '').replace('\t', '').replace('\r', '').replace('  ', '')
        return [company_item]



