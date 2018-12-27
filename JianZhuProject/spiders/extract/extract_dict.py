# coding=utf-8

EXTRACT_DICT = {
    'list_page': {
        'lines_rule': '',
        'detail_link_rule': '',  # 相对相对
        'have_next_page_rule': '',  # 返回一个bool值，标志是否还可翻页
        'next_page_rule': '',  # 绝对路径
        'total_page_num_rule': '',  # 列表页的总页码, 绝对路径
        'method': '',
    },
    'detail_page': {
        'method': 'POST',
        'compass': {
            'cnodes': '',
            'cname': '',
            'clink': '',
            'chonor_code': '',
            'clegal_person': '',
            'ctype': '',
            'cprovince': '',
            'coperation_addr': '',
            'cestablish_time': '',
            'cregister_capital': '',
            'cnet_asset': ''
        },
        'qualification': {
            'qnodes': '',
            'qtype': '',
            'qcode': '',
            'qname': '',
            'qstart_date': '',
            'qend_date': '',
            'qdetail_link': '',
            'qauthority': ''
        },
        'project': {
            'pnodes': '',
            'pcode': '',
            'pname': '',
            'psite': '',
            'ptype': '',
            'employer': '',
            'pdetail_link': '',
            'plink': '',
        },
        'staff': {
            'snodes': '',
            'sname': '',
            'sid_card': '',
            'stitle': '',
            'stitle_code': '',
            'sprofession': '',
            'sdetail_link': '',
            'slicence_stime': '',
            'slicence_etime': '',
        },
        'change': {
            'ch_nodes': '',
            'ch_time': '',
            'ch_content': '',
            'other_msg': '',
        },
        'behavior': {
            'bnodes': '',
            'brecord_id': '',
            'bcontent': '',
            'bexecutor': '',
            'bpublish_stime': '',
            'bpublish_etime': '',
            'bbody': '',
            'btype': '',
        }
    }
}

def outer():
    def check_big_dict(tar_dict, new_dict={}, blank_list1=[]):
        """
        遍历嵌套字典, 前提是字典嵌套字典，并且key不重复
        :param tar_dict: 字典
        :param new_dict: 新字典, 自由层
        :return: new_dict
        """
        for k, v in tar_dict.items():
            if isinstance(v, dict):
                check_big_dict(v, new_dict=new_dict, blank_list1=blank_list1)
            else:
                new_dict[k] = v
                blank_list1.append(k) if v.strip() =='' else ''

        return new_dict, blank_list1
    # print '非空值字段有:%s'% (set(new_dict) - set(blank_list1))
    return check_big_dict

# f = outer()
# new_dict, blank_list1 = f(EXTRACT_DICT, new_dict={})
# # new_dict, blank_list1 = outer(EXTRACT_DICT, new_dict={})
# print '总字典:%s'% new_dict
# print '空白值的列表:%s'% blank_list1
# print '非空值字段有:%s'% (set(new_dict) - set(blank_list1))
# blank_list = []
# for k, v in res.items():
#     if v.strip() =='':
#         blank_list.append(k)
# print '字段{} 子类尚未填充'.format(blank_list)
if __name__ == '__main__':
    pass
