# -*- coding:utf-8 -*-
#@Auhor : Agam
#@Time  : 2018-10-08
#@Email : agamgn@163.com
from ihome import const
from ihome.utils.response_code import RET
from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store
from flask import current_app, jsonify, make_response


@api.route("/image_code/<image_code_id>")
def get_image_code(image_code_id):
    """
    获取图片验证码
    :param image_code_id:
    :return:
    """
    name,text,image_data=captcha.generate_captcha()
    try:
        redis_store.setex("image_code_%s" % image_code_id, const.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error("code error")
        return jsonify(code=RET.DBERR,msg="保存图片验证码失败")

    resp=make_response(image_data)
    resp.headers['Content-Type']="image/jpg"

    return resp

