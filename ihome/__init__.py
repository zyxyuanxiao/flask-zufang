# -*- coding:utf-8 -*-
#@Auhor : Agam
#@Time  : 2018-10-08
#@Email : agamgn@163.com


from logging.handlers import RotatingFileHandler
from flask import Flask
from config import config_map
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import CSRFProtect
from ihome.utils.commons import ReConverter

import redis
import logging

# 数据库
db=SQLAlchemy()

#创建redis链接对象
redis_store=None



logging.basicConfig(level=logging.DEBUG)
file_log_handler=RotatingFileHandler("logs/log",maxBytes=1024*1024*100,backupCount=10)
formatter=logging.Formatter("%(levelname)s %(filename)s:%(lineno)d %(message)s")
file_log_handler.setFormatter(formatter)
logging.getLogger().addFilter(file_log_handler)


def create_app(config_name):
    """
    创建flask应用对象
    :param config_name:
    :return:
    """
    app = Flask(__name__)
    config_class=config_map.get(config_name)
    app.config.from_object(config_class)

    db.init_app(app)

    global redis_store
    redis_store = redis.StrictRedis(config_class.REDIS_HOST, config_class.REDIS_PORT)
    Session(app)
    app.url_map.converters['re']=ReConverter


    # 注册蓝图
    from .api_v1 import api
    app.register_blueprint(api,url_prefix='/api/v1.0')

    from ihome import web
    app.register_blueprint(web.html)

    return app
