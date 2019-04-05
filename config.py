# -*- coding:utf-8 -*-
#@Auhor : Agam
#@Time  : 2018-10-08
#@Email : agamgn@163.com
import redis


class Config():
    """配置信息"""
    SECRET_KEY="AGDJKSNGJSDG916"


    SQLALCHEMY_DATABASE_URI="mysql+pymysql://root:916149@127.0.0.1:3307/ihome"
    SQLALCHEMY_TRACK_MODIFICATIONS=True


    REDIS_HOST="127.0.0.1"
    REDIS_PORT=6379


    SESSION_TYPE='redis'
    SESSION_REDIS=redis.StrictRedis(REDIS_HOST,REDIS_PORT)
    SESSION_USER_SIGNER=True
    PERMANENT_SESSION_LIFETIME=86400



class DevelopmentConfig(Config):
    """开发模式的配置信息"""
    DEBUG=True


class ProductionConfig(Config):
    """生产环境配置信息"""
    pass


config_map={
    "develop":DevelopmentConfig,
    "product":ProductionConfig
}