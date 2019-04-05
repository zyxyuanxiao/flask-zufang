# coding:utf-8

import datetime

from flask import request, g, jsonify, current_app
from ihome import db, redis_store
from ihome.utils.commons import login_requires
from ihome.utils.response_code import RET
from ihome.models import House, Order
from . import api

@api.route("/saveorders", methods=["POST"])
@login_requires
def save_order():
    """保存订单"""
    user_id = g.user_id


    order_data = request.get_json()
    if not order_data:
        return jsonify(code=RET.PARAMERR,msg="参数错误")

    house_id = order_data.get("house_id")
    start_date_str = order_data.get("start_date")
    end_date_str = order_data.get("end_date")


    if not all((house_id, start_date_str, end_date_str)):
        return jsonify(code=RET.PARAMERR, msg="参数错误")


    try:

        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        assert start_date <= end_date

        days = (end_date - start_date).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.PARAMERR, msg="日期格式错误")


    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="获取房屋信息失败")
    if not house:
        return jsonify(code=RET.NODATA, msg="房屋不存在")


    if user_id == house.user_id:
        return jsonify(code=RET.ROLEERR, msg="不能预订自己的房屋")


    try:

        count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date,
                                   Order.end_date >= start_date).count()

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="检查出错，请稍候重试")
    if count > 0:
        return jsonify(code=RET.DATAERR, msg="房屋已被预订")


    amount = days * house.price


    order = Order(
        house_id=house_id,
        user_id=user_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount
    )
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR, msg="保存订单失败")
    return jsonify(code=RET.OK, msg="OK", data={"order_id": order.id})



@api.route("/user/orders", methods=["GET"])
@login_requires
def get_user_orders():
    """查询用户的订单信息"""
    user_id = g.user_id


    role = request.args.get("role", "")


    try:
        if "landlord" == role:

            houses = House.query.filter(House.user_id == user_id).all()
            houses_ids = [house.id for house in houses]

            orders = Order.query.filter(Order.house_id.in_(houses_ids)).order_by(Order.create_time.desc()).all()
        else:

            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="查询订单信息失败")


    orders_dict_list = []
    if orders:
        for order in orders:
            orders_dict_list.append(order.to_dict())

    return jsonify(code=RET.OK, msg="OK", data={"orders": orders_dict_list})


@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_requires
def accept_reject_order(order_id):
    """接单、拒单"""
    user_id = g.user_id

    req_data = request.get_json()
    if not req_data:
        return jsonify(code=RET.PARAMERR, msg="参数错误")


    action = req_data.get("action")
    if action not in ("accept", "reject"):
        return jsonify(code=RET.PARAMERR, msg="参数错误")

    try:

        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="无法获取订单数据")

    if not order or house.user_id != user_id:
        return jsonify(code=RET.REQERR, msg="操作无效")

    if action == "accept":
        order.status = "WAIT_PAYMENT"
    elif action == "reject":
        reason = req_data.get("reason")
        if not reason:
            return jsonify(code=RET.PARAMERR, msg="参数错误")
        order.status = "REJECTED"
        order.comment = reason

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR, msg="操作失败")

    return jsonify(code=RET.OK, msg="OK")


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_requires
def save_order_comment(order_id):
    """保存订单评论信息"""
    user_id = g.user_id
    req_data = request.get_json()
    comment = req_data.get("comment")

    if not comment:
        return jsonify(code=RET.PARAMERR, msg="参数错误")

    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,
                                   Order.status == "WAIT_COMMENT").first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="无法获取订单数据")

    if not order:
        return jsonify(code=RET.REQERR, msg="操作无效")

    try:
        order.status = "COMPLETE"
        order.comment = comment
        house.order_count += 1
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR, msg="操作失败")

    try:
        redis_store.delete("house_info_%s" % order.house.id)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(code=RET.OK, msg="OK")
