# -*- coding:utf-8 -*-
#@Auhor : Agam
#@Time  : 2018-10-08
#@Email : agamgn@163.com
from flask import g, request, jsonify, current_app, session

from ihome import db, const
from ihome.models import User
from ihome.utils.commons import login_requires
from ihome.utils.image_storage import storage
from ihome.utils.response_code import RET
from . import api




@api.route("/users/avatar",methods=['POST'])
@login_requires
def set_user_avatar():
    """
    设置用户头像
    :return:
    """
    user_id=g.user_id

    image_file=request.files.get("avatar")

    if image_file is None:
        return jsonify(code=RET.PARAMERR,msg="未上传图片")

    image_data=image_file.read()


    try:
        file_name=storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.THIRDERR,msg="上传图片失败")

    try:
        User.query.filter_by(id=user_id).update({"avatar_url":file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(RET.DBERR,"保存图片信息失败")

    avatar_url=const.QINIU_URL_DOMAIN+file_name
    return jsonify(code=RET.OK,msg="保存成功",data={"avatar_url":avatar_url})


@api.route("/users/name",methods=['PUT'])
@login_requires
def chage_user_name():
    """
    修改用户名
    :return:
    """

    user_id=g.user_id

    req_data=request.get_json()
    if not req_data:
        return jsonify(code=RET.PARAMERR,msg="参数不完整")

    name=req_data.get("name")
    if not name:
        return jsonify(code=RET.PARAMERR,msg="名字不能为空")

    try:
        User.query.filter_by(id=user_id).update({"name":name})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR,msg="设置用户错误")

    session['name']=name
    return jsonify(code=RET.OK,msg="OK",data={"name":name})


@api.route("/user",methods=['GET'])
def get_user_profile():
    """
    获取个人信息
    :return:
    """
    user_id=g.user_id
    try:
        user=User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,msg="获取用户信息失败")

    if user is None:
        return jsonify(code=RET.NODATA,msg="无效操作")

    return jsonify(code=RET.OK,msg="OK",data=user.to_dict())


@api.route("/user/auth",methods=["GET"])
@login_requires
def get_user_auth():
    """
    获取用户实名认证信息
    :return:
    """
    user_id=g.uesr_id
    try:
        user=User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,msg="获取用户实名信息失败")
    if user is None:
        return jsonify(code=RET.NODATA,msg="无效操作")
    return jsonify(code=RET.OK,msg="OK",data=user.auth_to_dict())


@api.route("/users/auth",methods=['POST'])
@login_requires
def set_user_auth():
    """
    保存实名认证信息
    :return:
    """
    user_id=g.user_id
    req_data=request.get_json()
    if not req_data:
        return jsonify(code=RET.PARAMERR,msg="参数错误")

    real_name=req_data.get("real_name")
    id_card=req_data.get("id_card")

    if not all([real_name,id_card]):
        return jsonify(code=RET.PARAMERR,msg="参数错误")

    try:
        User.query.filter_by( id= user_id, real_name = None, id_card = None).update(
            {"real_name":real_name,"id_card":id_card}
        )
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR,msg="保存用户信息失败")
    return jsonify(code=RET.OK,msg="OK")