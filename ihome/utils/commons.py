# -*- coding:utf-8 -*-
#@Auhor : Agam
#@Time  : 2018-10-08
#@Email : agamgn@163.com

from werkzeug.routing import BaseConverter
from flask import session, jsonify,g
import functools

from ihome.utils.response_code import RET


class ReConverter(BaseConverter):
    """正则转换"""
    def __init__(self,url_map,regex):
        # 调用父类的初始化方法
        super(ReConverter,self).__init__(url_map)
        # 保存正则表达式
        self.regex=regex


# 登录装饰器

def login_requires(view_func):
    """
    验证登录状态的装饰器
    :param view_func:
    :return:
    """

    @functools.wraps(view_func)
    def wrapper(*args,**kwargs):
        user_id=session.get("user_id")
        if user_id is not None:
            g.user_id=user_id
            return view_func(*args,**kwargs)
        else:
            return jsonify(RET.SESSIONERR,"用户未登陆")

    return wrapper


