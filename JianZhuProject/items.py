# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


"""
    说明： item字段作用--1、数据字段， 2、抓取信息字段基本完整性检查
"""


class JianzhuprojectItem(scrapy.Item):
    # 字段大字典

    compass_items = scrapy.Field()   # 公司基本信息, 类型[{},{}]
    qualification_items = scrapy.Field()   # [{},{}]
    staff_items = scrapy.Field()  # [{},{}]
    project_items = scrapy.Field()
    behavior_items = scrapy.Field()
    change_items = scrapy.Field()
    crawl_time = scrapy.Field()   # 抓取时间  格式: 2018-12-12 12:00:00

    # 如下链接是替补链接, 防止出现一个公司出现超级多的属性链接(如注册人员数量、工程数量的), 用此链接来记录以待后续补取或定期更新,一般以公司链接或真实链接赋值处理
    # 公司名、公司link、信用代码已在item上述中，此处不写
    compass_name = scrapy.Field()
    honor_code = scrapy.Field()
    source_link = scrapy.Field()   # 公司基本连接

    project_link = scrapy.Field()   # 打开工程项目的link
    staff_link = scrapy.Field()    # 打开公司注册人员的link
    behavior_link = scrapy.Field()
    change_link = scrapy.Field()

    same_seq = scrapy.Field()   # 01组成的字符串，从左到右：工程link、人员link、行为link、变更link，与source_link不同则相应位为1，相同为0


class CompassItem(scrapy.Item):   # ----> 对应com_item
    # 检查item字段是否全
    compass_name = scrapy.Field()   # 公司名字, 字符串类型
    compass_link = scrapy.Field()   # 公司link
    honor_code = scrapy.Field()   # 信用代码=企业唯一代码=营业执照注册号
    representative = scrapy.Field()  # 法人
    compass_type = scrapy.Field()   # 公司类型
    provice = scrapy.Field()   # 注册所属地
    operating_addr = scrapy.Field()  # 运营地址
    establish_time = scrapy.Field()  # 成立时间
    register_capital = scrapy.Field()  # 注册资本
    net_asset = scrapy.Field()   # 净资产


class QualityItem(scrapy.Item):  # ----> 对应qua_item
    # compass_name = scrapy.Field()   # 公司名字, 在写入数据库时添加,减少清洗复杂度
    # compass_link = scrapy.Field()   # 所属公司链接
    # honor_code = scrapy.Field()    # 必要的冗余字段

    # 基本信息
    quality_type = scrapy.Field()   # 资质类型
    quality_code = scrapy.Field()   # 资质证书编号
    quality_name = scrapy.Field()   # 资质名称 xxx甲级
    quality_start_date = scrapy.Field()   # 发证日期
    quality_end_date = scrapy.Field()  # 证书有效截止日期
    quality_detail_link = scrapy.Field()  # 资质详细链接
    authority = scrapy.Field()   # 发证机关


class StaffItem(scrapy.Item):  # ----> 对应staff_item
    # compass_name = scrapy.Field()   # 公司名字
    # compass_link = scrapy.Field()   # 所属公司链接
    # honor_code = scrapy.Field()    # 必要的冗余字段

    # 能从网页中获取的基本信息
    name = scrapy.Field()   # 姓名
    id_card = scrapy.Field()  # 身份证
    title = scrapy.Field()    # 职称
    title_code = scrapy.Field()  # 职称编码
    profession = scrapy.Field()   # 专业
    person_detail_link = scrapy.Field()   # 个人详细信息连接
    licence_start_date = scrapy.Field()   # 发证日期
    licence_end_date = scrapy.Field()   # 证件截止日期


class ProjectItem(scrapy.Item):   # ----> 对应pro_item
    # compass_name = scrapy.Field()   # 公司名字
    # compass_link = scrapy.Field()   # 所属公司链接
    # honor_code = scrapy.Field()    # 必要的冗余字段

    proj_code = scrapy.Field()  # 工程编号
    proj_name = scrapy.Field()  # 工程名
    proj_site = scrapy.Field()  # 工程地址
    proj_type = scrapy.Field()  # 类型
    employer = scrapy.Field()   # 建设单位名称=承包者
    proj_detail_link = scrapy.Field()   # 工程详情连接
    proj_link = scrapy.Field()  # 工程简要信息链接，一般以公司链接


class BehaviorItem(scrapy.Item):
    """良好行为、不良行为的item"""
    # 诚信记录编号、诚信记录主体、决定内容、实施部门（文号）、发布有效期

    # compass_name = scrapy.Field()
    # compass_link = scrapy.Field()
    # honor_code = scrapy.Field()

    # record_id、content、executor、issue_start_date、issue_end_date、body
    record_id = scrapy.Field()  # 行为编号
    content = scrapy.Field()   # 行为内容
    executor = scrapy.Field()   # 实行部门
    issue_start_date = scrapy.Field()
    issue_end_date = scrapy.Field()
    body = scrapy.Field()  # 行为主体, 公司名
    behavior_type = scrapy.Field()  # 两种取值: 良好1、不良-1


class ChangeItem(scrapy.Item):
    """变更信息item"""
    # compass_name = scrapy.Field()
    # honor_code = scrapy.Field()
    # compass_link = scrapy.Field()

    change_date = scrapy.Field()
    change_content = scrapy.Field()
    other_msg = scrapy.Field()



class NameItem(scrapy.Item):
    # 值用于保存公司名的item
    compass_name = scrapy.Field()
    detail_link = scrapy.Field()
    out_province = scrapy.Field()

