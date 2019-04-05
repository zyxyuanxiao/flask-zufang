# -*- coding:utf-8 -*-
#@Auhor : Agam
#@Time  : 2018-10-08
#@Email : agamgn@163.com


from flask import Blueprint, current_app, make_response
from flask_wtf import csrf



html=Blueprint("web",__name__)


@html.route("/<re(r'.*'):html_fie_name>")
def get_html(html_fie_name):
    """提供html文件"""

    if not html_fie_name:
        html_fie_name="index.html"
    if html_fie_name !='favicon.ico':


        html_fie_name="html/"+html_fie_name


    csrf_token=csrf.generate_csrf()

    resp=make_response(current_app.send_static_file(html_fie_name))


    resp.set_cookie("csrf_token",csrf_token)

    return resp