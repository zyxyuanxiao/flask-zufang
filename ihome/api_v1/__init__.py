# -*- coding:utf-8 -*-
#@Auhor : Agam
#@Time  : 2018-10-08
#@Email : agamgn@163.com

from flask import Blueprint

api=Blueprint("api_v1",__name__)

from . import houses,orders,verify,profile,passport,pay
