# -*- coding:utf-8 -*-
#@Auhor : Agam
#@Time  : 2018-10-08
#@Email : agamgn@163.com
from flask import request, jsonify, current_app, session
import re

from ihome import redis_store, db, const
from ihome.models import User
from ihome.utils.response_code import RET
from sqlalchemy.exc import IntegrityError
from . import api

@api.route("/register",methods=['POST'])
def register():
    """
    注册
    :return:
    """

    req_dict=request.get_json()
    mobile=req_dict.get("mobile")
    password=req_dict.get("password")
    password2=req_dict.get("password2")
    if not all([mobile,password,password2]):
        return jsonify(code=RET.PARAMERR,msg="参数不完整")
    if not re.match(r"1[34578]\d{9}",mobile):
        return jsonify(code=RET.PARAMERR,msg="手机格式错误")

    if password!=password2:
        return jsonify(code=RET.PARAMERR,msg="两次密码不一致")



    try:
        user=User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,msg="数据库异常")

    else:
        if user is not None:
            return jsonify(code=RET.DATAEXIST,msg="手机号已存在")



    user=User(name=mobile,mobile=mobile)
    user.password=password
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(code=RET.DATAEXIST,msg="手机号已存在")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DATAEXIST, msg="查询数据库异常")

    session['name']=mobile
    session['mobile']=mobile
    session['user_id']=user.id

    return jsonify(code=RET.OK,msg="注册成功")



@api.route("/login",methods=["POST"])
def login():
    """
    用户登录
    :return:
    """

    req_dict=request.get_json()
    print(req_dict)
    mobile=req_dict.get("mobile")
    password=req_dict.get("password")

    if not all([mobile,password]):
        return jsonify(code=RET.PARAMERR,msg="参数不完整")


    if not re.match(r"1[34578]\d{9}",mobile):
        return jsonify(code=RET.PARAMERR,msg="手机格式不正确")

    user_ip=request.remote_addr
    try:
        access_nums=redis_store.get("access_num_%s"%user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nums is not None and int(access_nums) >= const.LOGIN_ERROR_MAX_TIMES:
            return jsonify(code=RET.REQERR,msg="错误次数过多，请稍后重试")

    try:
        user=User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,msg="获取用户信息失败")

    if user is None or user.check_password(password):
        try:
            redis_store.incr("access_num_%s"%user_ip)
            redis_store.expire("access_num_%s"%user_ip,const.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)
        return jsonify(code=RET.DATAERR,msg="用户名或密码错误")

    session['name']=user.name
    session['mobile']=user.mobile
    session['user_id']=user.id


    return jsonify(code=RET.OK,msg="登录成功")



@api.route("/check_login",methods=['GET'])
def check_login():
    """
    检查登录状态
    :return:
    """
    name=session.get("name")
    if name is not None:
        return jsonify(code=RET.OK,meg="true",data={"name":name})
    else:
        return jsonify(code=RET.SESSIONERR,meg="false")


@api.route("/logout",methods=['DELETE'])
def logout():
    """
    登出
    :return:
    """
    session.clear()
    return jsonify(code=RET.OK,msg="OK")










