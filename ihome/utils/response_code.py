# coding:utf-8

class RET:
    OK                  = "200"
    DBERR               = "401"
    NODATA              = "402"
    DATAEXIST           = "403"
    DATAERR             = "404"
    SESSIONERR          = "411"
    LOGINERR            = "412"
    PARAMERR            = "413"
    USERERR             = "414"
    ROLEERR             = "415"
    PWDERR              = "416"
    REQERR              = "421"
    IPERR               = "422"
    THIRDERR            = "431"
    IOERR               = "432"
    SERVERERR           = "450"
    UNKOWNERR           = "451"

error_map = {
    RET.OK                    : u"成功",
    RET.DBERR                 : u"数据库查询错误",
    RET.NODATA                : u"无数据",
    RET.DATAEXIST             : u"数据已存在",
    RET.DATAERR               : u"数据错误",
    RET.SESSIONERR            : u"用户未登录",
    RET.LOGINERR              : u"用户登录失败",
    RET.PARAMERR              : u"参数错误",
    RET.USERERR               : u"用户不存在或未激活",
    RET.ROLEERR               : u"用户身份错误",
    RET.PWDERR                : u"密码错误",
    RET.REQERR                : u"非法请求或请求次数受限",
    RET.IPERR                 : u"IP受限",
    RET.THIRDERR              : u"第三方系统错误",
    RET.IOERR                 : u"文件读写错误",
    RET.SERVERERR             : u"内部错误",
    RET.UNKOWNERR             : u"未知错误",
}
