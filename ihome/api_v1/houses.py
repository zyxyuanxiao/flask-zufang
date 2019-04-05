# -*- coding:utf-8 -*-
#@Auhor : Agam
#@Time  : 2018-10-08
#@Email : agamgn@163.com
import json
from datetime import datetime

from flask import current_app, jsonify, g, request, session

from ihome import redis_store, const, db
from ihome.models import Area, House, Facility, HouseImage, User, Order
from ihome.utils.commons import login_requires
from ihome.utils.image_storage import storage
from ihome.utils.response_code import RET
from . import api


@api.route("/areas")
def get_area_info():
    """
    获取城区信息
    :return:
    """
    try:
        resp_json=redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            return resp_json,200,{"Content-Type":"application/json"}

    try:
        area_li=Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,msg="数据库异常")

    area_dict_li=[]
    for area in area_li:
        area_dict_li.append(area.to_dict())
    print(area_dict_li)
    resp_dict = dict(code=RET.OK, msg="OK", data=area_dict_li)
    resp_json=json.dumps(resp_dict)


    try:
        redis_store.setx("area_info",const.AREA_INFO_REDIS_CACHE_EXPIRES,resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json,200,{"Content-Type":"application/json"}



@api.route("/house",methods=["POST"])
@login_requires
def save_new_house():
    user_id=g.user_id
    house_data=request.get_json()
    print(house_data)
    title=house_data.get("title")
    price=house_data.get("price")
    area_id=house_data.get('area_id')
    address=house_data.get("address")
    room_count=house_data.get("room_count")
    acreage=house_data.get("acreage")
    unit=house_data.get("unit")
    capacity=house_data.get("capacity")
    beds=house_data.get("beds")
    deposit=house_data.get("deposit")
    min_days=house_data.get("min_days")
    max_days=house_data.get("max_days")

    if not all([title,price,area_id,address,room_count,acreage,
                unit,capacity,beds,deposit,min_days,max_days]):

        return jsonify(code=RET.PARAMERR,msg="参数不完整")

    try:
        price=int(float(price)*100)
        deposit=int(float(deposit)*100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.PARAMERR,msg="参数错误")


    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,msg="数据异常")

    if area is None:
        return jsonify(code=RET.NODATA,msg="城区信息有误")

    house=House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR,msg="保存信息异常")


    facility_ids=house_data.get("facility")
    if facility_ids:
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids))

        except Exception as e:
            current_app.logger.error(e)
            return jsonify(code=RET.DBERR,msg="数据库异常")

        if facilities:
            house.facilities=facilities
            try:
                db.session.add(house)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
            return jsonify(code=RET.DBERR,msg="保存数据失败")
    return jsonify(code=RET.OK,msg="OK",data={"house_id":house.id})



@api.route("/house/image",methods=['POST'])
@login_requires
def save_house_image():
    """
    保存房屋图片
    :return:
    """
    image_file=request.files.get("house_image")
    house_id=request.form.get("house_id")

    if not all([image_file,house_id]):
        return jsonify(code=RET.PARAMERR,msg="参数错误")

    try:
        house=House.query.get(house_id)
    except Exception as e:
        return jsonify(code=RET.DBERR,msg="数据库异常")

    if house is None:
        return jsonify(code=RET.NODATA,msg="房屋不存在")

    image_data=image_file.read()
    try:
        file_name=storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.THIRDERR,msg="保存图片失败")

    house_image=HouseImage(house_id,file_name)
    db.session.add(house_image)

    if not house.index_image_url:
        house.index_image_url=file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR,msg="保存失败")

    image_url=const.QINIU_URL_DOMAIN+file_name
    return jsonify(code=RET.OK,msg="OK",data={"image_url":image_url})



@api.route("/user/houses",methods=['GET'])
@login_requires
def get_user_house():
    """
    获取房东发布的房源信息条目
    :return:
    """
    user_id=g.user_id

    try:
        user=User.query.get(user_id)
        houses=user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,msg="获取数据失败")

    houses_list=[]
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())
    return jsonify(code=RET.OK,msg="OK",data={"houses":houses_list})



@api.route("/houses/index",methods=['GET'])
def get_house_index():
    """
    获取主页幻灯片展示的房屋基本信息
    :return:
    """
    try:
        ret=redis_store.get("home_page_data")
    except Exception as e:
        current_app.logger.error(e)
        ret=None
    if ret:
        current_app.logger.info("hit house info redis")
        return '{0,"ok","%s}'%ret,200,{"Content-Type":"application/json"}
    else:
        try:
            houses=House.query.order_by(House.order_count.desc()).limit(const.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(code=RET.DBERR,msg="查询数据失败")

        if not houses:
            return jsonify(code=RET.NODATA,msg="查询无数据")

        houses_list=[]
        for house in houses:
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        json_houses=json.dumps(houses_list)
        try:
            redis_store.setex("home_page_data",const.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)

        return '{0,"OK",%s}'% json_houses,200,{"Content-Type":"application/json"}



@api.route("/houses/<int:house_id>",methods=['GET'])
def get_house_detail(house_id):
    """
    获取房屋详情
    :param house_id:
    :return:
    """
    user_id=session.get("user_id","-1")
    if not house_id:
        return jsonify(code=RET.PARAMERR,msg="参数错误")

    try:
        ret=redis_store.get("house_info_%s"%house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret=None

    if ret:
        current_app.logger.info("hit house info redis")
        return '{code=0,msg="OK",data={"user_id":%s,"house":%s}}'%(user_id,request),200,{"Content-Type":"application/json"}

    try:
        house=House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,msg="查询数据失败")

    if not house:
        return jsonify(code=RET.NODATA,msg="房屋不存在")

    try:
        house_data=house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DATAERRM,msg="数据出错")

    json_house=json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s"%house_id,const.HOME_DETAIL_REDIS_EXPIRE_SECOND,json_house)
    except Exception as e:
        current_app.logger.error(e)

    resp='{code="200",msg="OK",data={"user_id":%s,"house":%s}}'%(user_id,json_house),200,{"Content-Type":"application/json"}

    return resp


@api.route("/houses")
def get_house_list():
    """
    获取房屋的列表信息
    :return:
    """
    start_date=request.args.get("sd")
    end_date=request.args.get("ed")
    area_id=request.args.get("aid")
    sort_key=request.args.get("sk")
    page=request.args.get("p")

    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.PARAMERR,msg="日期参数错误")

    if area_id:
        try:
            area=Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(code=RET.PARAMERR,msg="区域参数错误")

    try:
        page=int(page)
    except Exception as e:
        current_app.logger.error(e)
        page=1

    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        resp_json=redis_store.hget(redis_key,page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            return resp_json,200,{"Content-Type":"application/json"}

    filter_params=[]
    confilct_orders=None


    try:
        if start_date and end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,msg="数据库异常")


    if conflict_orders:
        conflict_house_ids = [order.house_id for order in conflict_orders]
        if conflict_house_ids:
            filter_params.append(House.id.notin_(conflict_house_ids))
    if area_id:
        filter_params.append(House.area_id==area_id)
    if sort_key=="booking":
        house_query=House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key=='price-inc':
        house_query=House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key=='price-des':
        house_query=House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        house_query=House.query.filter(*filter_params).order_by(House.create_time.desc())
    try:
        page_obj = house_query.paginate(page=page, per_page=const.HOME_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="数据库异常")

    house_li=page_obj.items
    houses=[]
    for house in house_li:
        houses.append(house.to_basic_dict())

    total_page=page_obj.pages

    resp_dict=dict(code=RET.OK,msg="OK",data={"total_page":total_page,"houses":house,"current_page":page})
    resp_json=json.dumps(resp_dict)


    if page<=total_page:
        redis_key="house_%s_%s_%s_%s"%(start_date,end_date,area_id,sort_key)
        try:

            pipeline=redis_store.pipeline()
            pipeline.multi()

            pipeline.hset(redis_key,page,resp_json)
            pipeline.expire(redis_key,const.HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES)

            pipeline.execute()


        except Exception as e:
            current_app.logger.error(e)
    return  resp_json,200,{"Content-Type":"application/json"}





